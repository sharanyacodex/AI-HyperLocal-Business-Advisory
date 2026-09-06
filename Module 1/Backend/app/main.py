import re
import time
import asyncio

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import httpx
import math
import uvicorn


# ============================================================
# YOUR EXISTING SERVICES
# ============================================================

from app.services.demographics_service import (
    get_demographic_analysis
)

from app.services.location_insights_service import (
    get_location_insights
)

from app.services.feasibility_service import (
    calculate_feasibility_score,
    calculate_competition_level,
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Rural Business Advisory API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# EXTERNAL SERVICES
# ============================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

OVERPASS_URL = (
    "https://overpass-api.de/api/interpreter"
)

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

POSTAL_API_URL = (
    "https://api.postalpincode.in/pincode"
)


# ============================================================
# PINCODE: IN-MEMORY TTL CACHE
# ============================================================
#
# Pincode -> district/state/lat/lon is essentially static data.
# There is no reason to hit the live postal API / Nominatim
# again for a pincode we already resolved recently. This also
# means transient slowness in the upstream API only costs the
# user once per pincode, not on every request.
# ============================================================

_PINCODE_CACHE = {}
_PINCODE_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours


def _get_cached_pincode(pincode: str):

    entry = _PINCODE_CACHE.get(pincode)

    if not entry:
        return None

    cached_at, data = entry

    if time.monotonic() - cached_at > _PINCODE_CACHE_TTL_SECONDS:
        _PINCODE_CACHE.pop(pincode, None)
        return None

    return data


def _set_cached_pincode(pincode: str, data: dict):

    _PINCODE_CACHE[pincode] = (
        time.monotonic(),
        data,
    )


# ============================================================
# PINCODE: POSTAL API FETCH WITH RETRY
# ============================================================
#
# api.postalpincode.in is a free, unauthenticated, no-SLA API
# and is known to be intermittently slow. A single transient
# slow response should not be a hard failure for the user, so
# we retry once with a short backoff before giving up. If both
# attempts time out, we re-raise so the endpoint's existing
# httpx.TimeoutException handler still returns the correct
# user-facing message.
# ============================================================

async def fetch_postal_data(
    client,
    postal_url: str,
    headers: dict,
    attempts: int = 2,
):

    last_error = None

    for attempt in range(1, attempts + 1):

        try:

            response = await client.get(
                postal_url,
                headers=headers,
            )

            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:

            last_error = e

            print(
                f"POSTAL API TIMEOUT (attempt {attempt}/{attempts}):",
                postal_url,
            )

            if attempt < attempts:

                await asyncio.sleep(1.5)
                continue

    raise last_error


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "success": True,
        "message": "AI Rural Business Advisory API is running.",
        "endpoints": [
            "/",
            "/health",
            "/pincode",
            "/module1/analyze",
        ],
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():

    return {
        "success": True,
        "status": "healthy",
    }


# ============================================================
# PINCODE: POST OFFICE SELECTION (GENERALIZED)
# ============================================================
#
# A single pincode can map to many post offices (Head Post
# Office, Sub Post Offices, Branch Offices / villages). We want
# the one that best represents the "main" locality for that
# pincode, for ANY pincode - not a hardcoded name list.
#
# Preference order:
#   1. Head Post Office  (BranchType == "Head Post Office")
#   2. Sub Post Office    (BranchType == "Sub Post Office")
#   3. First entry as a last resort
# ============================================================

def select_best_post_office(post_offices: list) -> dict:

    if not post_offices:
        return {}

    if len(post_offices) == 1:
        return post_offices[0]

    for office in post_offices:

        branch_type = str(
            office.get("BranchType", "")
        ).strip().lower()

        if branch_type == "head post office":
            return office

    for office in post_offices:

        branch_type = str(
            office.get("BranchType", "")
        ).strip().lower()

        if branch_type == "sub post office":
            return office

    return post_offices[0]


# ============================================================
# PINCODE: GEOCODING (PROGRESSIVE + STATE-VALIDATED)
# ============================================================
#
# Nominatim can return a same-named place in a completely
# different state (e.g. "Bishnupur" exists in West Bengal AND
# Manipur). We now:
#
#   1. Try a series of increasingly broad queries
#      (location -> block -> district -> state).
#   2. For each query's results, only accept a candidate whose
#      returned "state" actually matches the expected state.
#   3. Only fall back to an unvalidated "first result" if no
#      query at any tier produced a validated match.
#
# Any timeout or error on an individual geocode request is
# caught here and simply moves on to the next query tier - it
# does NOT propagate up and does NOT trigger the pincode
# endpoint's "taking too long" message.
# ============================================================

async def geocode_location(
    client,
    headers,
    location_name: str,
    block: str,
    district: str,
    state: str,
):

    query_candidates = [
        f"{location_name}, {district}, {state}, India"
        if location_name else None,

        f"{block}, {district}, {state}, India"
        if block else None,

        f"{district}, {state}, India"
        if district else None,

        f"{state}, India"
        if state else None,
    ]

    query_candidates = [
        q for q in query_candidates if q
    ]

    first_unvalidated = None
    first_unvalidated_query = None

    for query in query_candidates:

        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": 5,
        }

        try:

            response = await client.get(
                NOMINATIM_URL,
                params=params,
                headers=headers,
            )

            response.raise_for_status()

            results = response.json()

        except Exception as e:

            print(
                "GEOCODE QUERY ERROR:",
                query,
                e,
            )

            continue

        if not results:
            continue

        if first_unvalidated is None:
            first_unvalidated = results[0]
            first_unvalidated_query = query

        for geo in results:

            address = geo.get(
                "address",
                {}
            )

            geo_state = str(
                address.get("state", "")
            ).strip().lower()

            geo_district = str(
                address.get(
                    "state_district",
                    address.get("county", "")
                )
            ).strip().lower()

            state_matches = (
                not state
                or state.lower() in geo_state
                or geo_state in state.lower()
            )

            district_matches = (
                not district
                or district.lower() in geo_district
                or district.lower() in query.lower()
            )

            if state_matches and district_matches:
                return geo, query

        for geo in results:

            address = geo.get(
                "address",
                {}
            )

            geo_state = str(
                address.get("state", "")
            ).strip().lower()

            if (
                not state
                or state.lower() in geo_state
                or geo_state in state.lower()
            ):
                return geo, query

    return first_unvalidated, first_unvalidated_query


# ============================================================
# PINCODE SERVICE
# ============================================================

@app.get("/pincode")
async def get_pincode_location(
    pincode: str = Query(
        ...,
        min_length=6,
        max_length=6
    )
):

    pincode = pincode.strip()

    if not pincode.isdigit() or len(pincode) != 6:
        return {
            "success": False,
            "message": "Please enter a valid 6-digit PIN code.",
        }

    # --------------------------------------------------------
    # CACHE CHECK - skip the network entirely if we've already
    # resolved this pincode recently.
    # --------------------------------------------------------

    cached_result = _get_cached_pincode(pincode)

    if cached_result is not None:
        return cached_result

    headers = {
        "User-Agent": (
            "AI-Rural-Business-Advisory/1.0 "
            "(educational-project)"
        ),
        "Accept": "application/json",
    }

    timeout = httpx.Timeout(
        connect=5.0,
        read=15.0,
        write=5.0,
        pool=5.0,
    )

    try:

        # ------------------------------------------------
        # 1. GET ALL POST OFFICES FOR PIN CODE
        #    (retried once on timeout before failing)
        # ------------------------------------------------

        postal_url = (
            f"https://api.postalpincode.in/pincode/{pincode}"
        )

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        ) as client:

            postal_data = await fetch_postal_data(
                client,
                postal_url,
                headers,
                attempts=2,
            )

        if not postal_data:
            return {
                "success": False,
                "message": "PIN code not found.",
            }

        postal_result = postal_data[0]

        if postal_result.get("Status") != "Success":
            return {
                "success": False,
                "message": "PIN code not found.",
            }

        post_offices = postal_result.get(
            "PostOffice",
            []
        )

        if not post_offices:
            return {
                "success": False,
                "message": "No location found for this PIN code.",
            }

        # ------------------------------------------------
        # 2. PICK THE BEST-REPRESENTATIVE POST OFFICE
        #    (Head PO > Sub PO > first entry), for ANY
        #    pincode - not hardcoded to a specific name.
        # ------------------------------------------------

        selected = select_best_post_office(post_offices)

        # ------------------------------------------------
        # 3. GET DISTRICT / STATE DIRECTLY FROM
        #    INDIA POSTAL PIN API
        # ------------------------------------------------

        district = (
            selected.get("District")
            or ""
        )

        state = (
            selected.get("State")
            or ""
        )

        block = (
            selected.get("Block")
            or ""
        )

        location_name = (
            selected.get("Name")
            or block
            or ""
        )

        # ------------------------------------------------
        # 4. GEOCODE (progressive + state-validated)
        # ------------------------------------------------

        selected_geo = None
        used_query = None

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        ) as client:

            selected_geo, used_query = (
                await geocode_location(
                    client,
                    headers,
                    location_name,
                    block,
                    district,
                    state,
                )
            )

        latitude = None
        longitude = None
        display_name = ""

        if selected_geo:

            try:

                latitude = float(
                    selected_geo.get("lat")
                )

                longitude = float(
                    selected_geo.get("lon")
                )

                display_name = selected_geo.get(
                    "display_name",
                    ""
                )

            except (
                TypeError,
                ValueError
            ):

                latitude = None
                longitude = None

        # ------------------------------------------------
        # 5. FINAL RESPONSE
        # ------------------------------------------------

        result = {

            "success": True,

            "pincode": pincode,

            "location_name": location_name,

            "district": district,

            "state": state,

            "country": (
                selected.get("Country")
                or "India"
            ),

            "block": block,

            "latitude": latitude,

            "longitude": longitude,

            "display_name": display_name,

            "post_office": selected.get(
                "Name",
                ""
            ),

            "geocode_query_used":
                used_query,

            "geocode_matched":
                bool(selected_geo)
                and latitude is not None,

            "data_source":
                "India Postal PIN Code API + "
                "OpenStreetMap / Nominatim",

        }

        # Only cache fully-resolved, successful lookups -
        # don't cache partial failures.
        if result["latitude"] is not None:
            _set_cached_pincode(pincode, result)

        return result

    except httpx.TimeoutException:

        print(
            f"PINCODE TIMEOUT: {pincode}"
        )

        return {

            "success": False,

            "message":
                "Pincode service is taking too long. "
                "Please try again.",
        }

    except httpx.HTTPStatusError as e:

        print(
            "PINCODE HTTP ERROR:",
            e
        )

        return {

            "success": False,

            "message":
                "Pincode service is temporarily unavailable.",
        }

    except Exception as e:

        print(
            "PINCODE ERROR:",
            e
        )

        return {

            "success": False,

            "message":
                "Could not retrieve pincode location.",
        }


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2,
):

    earth_radius = 6371000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = (
        2
        * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )
    )

    return earth_radius * c


# ============================================================
# BUSINESS TYPE -> OSM TAG MAP (GENERALIZED)
# ============================================================
#
# Word-boundary matched (not loose substring matching), so
# "seafood export" no longer matches "food" -> restaurant/cafe,
# and "medical equipment supplier" no longer matches "medical"
# -> pharmacy.
#
# If nothing in the map matches, we try to infer a direct OSM
# shop= tag from the phrase itself (e.g. "toy shop" -> shop=toy)
# instead of dumping every shop/amenity within radius.
# ============================================================

BUSINESS_TAG_MAP = {
    "cafe": ['["amenity"="cafe"]'],
    "coffee shop": ['["amenity"="cafe"]'],
    "restaurant": ['["amenity"="restaurant"]'],
    "dhaba": ['["amenity"="restaurant"]'],
    "hotel": ['["tourism"="hotel"]', '["amenity"="restaurant"]'],
    "bakery": ['["shop"="bakery"]'],
    "sweet shop": ['["shop"="confectionery"]'],
    "sweets": ['["shop"="confectionery"]'],
    "confectionery": ['["shop"="confectionery"]'],

    "dairy": ['["shop"="dairy"]'],
    "milk": ['["shop"="dairy"]'],

    "grocery": ['["shop"="supermarket"]', '["shop"="convenience"]'],
    "kirana": ['["shop"="convenience"]', '["shop"="grocery"]'],
    "general store": ['["shop"="convenience"]', '["shop"="grocery"]'],
    "supermarket": ['["shop"="supermarket"]'],
    "convenience store": ['["shop"="convenience"]'],

    "salon": ['["shop"="hairdresser"]', '["shop"="beauty"]'],
    "beauty parlour": ['["shop"="beauty"]'],
    "beauty parlor": ['["shop"="beauty"]'],
    "barber": ['["shop"="hairdresser"]'],
    "hairdresser": ['["shop"="hairdresser"]'],

    "pharmacy": ['["amenity"="pharmacy"]'],
    "medical store": ['["amenity"="pharmacy"]'],
    "chemist": ['["amenity"="pharmacy"]'],
    "medicine shop": ['["amenity"="pharmacy"]'],

    "stationery": ['["shop"="stationery"]'],
    "hardware": ['["shop"="hardware"]', '["shop"="doityourself"]'],
    "electronics": ['["shop"="electronics"]'],
    "mobile shop": ['["shop"="mobile_phone"]'],
    "mobile store": ['["shop"="mobile_phone"]'],
    "phone shop": ['["shop"="mobile_phone"]'],

    "clothing": ['["shop"="clothes"]'],
    "garment": ['["shop"="clothes"]'],
    "tailor": ['["shop"="tailor"]'],
    "footwear": ['["shop"="shoes"]'],
    "shoe shop": ['["shop"="shoes"]'],

    "gym": ['["leisure"="fitness_centre"]'],
    "fitness": ['["leisure"="fitness_centre"]'],

    "bookstore": ['["shop"="books"]'],
    "book shop": ['["shop"="books"]'],

    "jewellery": ['["shop"="jewelry"]'],
    "jewelry": ['["shop"="jewelry"]'],

    "furniture": ['["shop"="furniture"]'],

    "agri input": ['["shop"="agrarian"]', '["shop"="farm"]'],
    "fertilizer": ['["shop"="agrarian"]'],
    "seed shop": ['["shop"="agrarian"]'],

    "veterinary": ['["amenity"="veterinary"]'],
    "vet clinic": ['["amenity"="veterinary"]'],

    "laundry": ['["shop"="laundry"]'],
    "dry cleaner": ['["shop"="laundry"]'],
}


def resolve_search_terms(business_type: str) -> list:

    business = business_type.strip().lower()

    matched_terms = []

    for keyword, tags in BUSINESS_TAG_MAP.items():

        pattern = r"\b" + re.escape(keyword) + r"\b"

        if re.search(pattern, business):

            for tag in tags:

                if tag not in matched_terms:
                    matched_terms.append(tag)

    if matched_terms:
        return matched_terms

    # --------------------------------------------------------
    # No known keyword matched. Try to infer a direct OSM
    # shop= value from the raw phrase itself, e.g.:
    #   "toy shop"       -> shop=toy
    #   "pet store"      -> shop=pet
    #   "bicycle shop"   -> shop=bicycle
    # --------------------------------------------------------

    slug = re.sub(
        r"\b(shop|store|shops|stores|business)\b",
        "",
        business,
    )

    slug = re.sub(r"[^a-z]+", "_", slug).strip("_")

    if slug:
        return [
            f'["shop"="{slug}"]',
            f'["craft"="{slug}"]',
        ]

    return ['["shop"]', '["amenity"]']


# ============================================================
# COMPETITOR SEARCH
# ============================================================

async def get_competitors(
    latitude: float,
    longitude: float,
    business_type: str,
    radius_m: int = 10000,
):

    search_terms = resolve_search_terms(business_type)

    query_parts = []

    for tag in search_terms:

        query_parts.append(
            f"""
            node{tag}
            (around:{radius_m},{latitude},{longitude});

            way{tag}
            (around:{radius_m},{latitude},{longitude});
            """
        )

    query = f"""
    [out:json][timeout:30];

    (
        {"".join(query_parts)}
    );

    out center;
    """

    async def run_overpass_query(q: str):

        overpass_timeout = httpx.Timeout(
            connect=5.0,
            read=25.0,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(
            timeout=overpass_timeout,
            follow_redirects=True,
        ) as client:

            response = await client.post(
                OVERPASS_URL,
                data=q,
            )

            response.raise_for_status()

            return response.json()

    try:

        data = await run_overpass_query(query)

        elements = data.get(
            "elements",
            []
        )

        fell_back_to_broad = False

        if not elements and search_terms != ['["shop"]', '["amenity"]']:

            broad_query = f"""
            [out:json][timeout:30];

            (
                node["shop"](around:{radius_m},{latitude},{longitude});
                way["shop"](around:{radius_m},{latitude},{longitude});
                node["amenity"](around:{radius_m},{latitude},{longitude});
                way["amenity"](around:{radius_m},{latitude},{longitude});
            );

            out center;
            """

            try:

                data = await run_overpass_query(broad_query)

                elements = data.get(
                    "elements",
                    []
                )

                fell_back_to_broad = True

            except Exception as e:

                print(
                    "COMPETITOR BROAD FALLBACK ERROR:",
                    e
                )

        competitors = []

        for element in elements:

            tags = element.get(
                "tags",
                {}
            )

            if element.get("type") == "node":

                lat = element.get("lat")
                lon = element.get("lon")

            else:

                center = element.get(
                    "center",
                    {}
                )

                lat = center.get("lat")
                lon = center.get("lon")

            if lat is None or lon is None:
                continue

            name = (
                tags.get("name")
                or tags.get("brand")
                or "Nearby Business"
            )

            category = (
                tags.get("shop")
                or tags.get("amenity")
                or tags.get("office")
                or "business"
            )

            address_parts = [

                tags.get("addr:housenumber"),

                tags.get("addr:street"),

                tags.get("addr:suburb"),

                tags.get("addr:city"),

            ]

            address = ", ".join(
                part
                for part in address_parts
                if part
            )

            distance_m = calculate_distance(
                latitude,
                longitude,
                float(lat),
                float(lon),
            )

            if distance_m > radius_m:
                continue

            competitors.append(
                {
                    "name": name,

                    "latitude": float(lat),

                    "longitude": float(lon),

                    "category": category,

                    "address": address,

                    "distance_m": round(
                        distance_m,
                        2
                    ),

                    "place_id": str(
                        element.get(
                            "id",
                            ""
                        )
                    ),
                }
            )

        unique = {}

        for competitor in competitors:

            key = (
                competitor["name"],
                round(
                    competitor["latitude"],
                    5
                ),
                round(
                    competitor["longitude"],
                    5
                ),
            )

            unique[key] = competitor

        competitors = list(
            unique.values()
        )

        competitors.sort(
            key=lambda x: x["distance_m"]
        )

        return {

            "success": True,

            "competitors": competitors,

            "competitor_count":
                len(competitors),

            "competitor_data_availability":
                "AVAILABLE"
                if competitors
                else "LIMITED",

            "competitor_radius_km":
                radius_m / 1000,

            "matched_osm_tags":
                search_terms,

            "used_broad_fallback":
                fell_back_to_broad,

            "competitor_data_source":
                "OpenStreetMap / Overpass",
        }

    except httpx.TimeoutException:

        print("COMPETITOR TIMEOUT")

        return {

            "success": False,

            "competitors": [],

            "competitor_count": 0,

            "competitor_data_availability":
                "LIMITED",

            "message":
                "Competitor service timed out.",
        }

    except Exception as e:

        print(
            "COMPETITOR ERROR:",
            e
        )

        return {

            "success": False,

            "competitors": [],

            "competitor_count": 0,

            "competitor_data_availability":
                "LIMITED",

            "message":
                "Could not retrieve competitor data.",
        }


# ============================================================
# WEATHER
# ============================================================

def weather_description(
    weather_code
):

    if weather_code is None:
        return "Unavailable"

    try:

        code = int(weather_code)

    except (
        TypeError,
        ValueError
    ):
        return "Unavailable"

    if code == 0:
        return "Clear"

    elif code in [1, 2, 3]:
        return "Cloudy"

    elif code in [45, 48]:
        return "Foggy"

    elif code in [51, 53, 55]:
        return "Drizzle"

    elif code in [56, 57]:
        return "Freezing Drizzle"

    elif code in [61, 63, 65]:
        return "Rainy"

    elif code in [66, 67]:
        return "Freezing Rain"

    elif code in [71, 73, 75, 77]:
        return "Snowy"

    elif code in [80, 81, 82]:
        return "Rain Showers"

    elif code in [85, 86]:
        return "Snow Showers"

    elif code in [95, 96, 99]:
        return "Thunderstorm"

    return "Normal"


async def get_weather(
    latitude: float,
    longitude: float,
):

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "current":
            "temperature_2m,"
            "wind_speed_10m,"
            "precipitation,"
            "weather_code",

    }

    try:

        timeout = httpx.Timeout(
            connect=5.0,
            read=10.0,
            write=5.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout
        ) as client:

            response = await client.get(
                OPEN_METEO_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        current = data.get(
            "current",
            {}
        )

        code = current.get(
            "weather_code"
        )

        return {

            "success": True,

            "temperature_c":
                current.get(
                    "temperature_2m"
                ),

            "wind_speed_kmh":
                current.get(
                    "wind_speed_10m"
                ),

            "precipitation_mm":
                current.get(
                    "precipitation"
                ),

            "weather_code":
                code,

            "weather_description":
                weather_description(code),

            "data_source":
                "Open-Meteo",

        }

    except Exception as e:

        print(
            "WEATHER ERROR:",
            e
        )

        return {

            "success": False,

            "message":
                "Weather data unavailable.",
        }


# ============================================================
# MARKET DEMAND
# ============================================================

def calculate_market_demand(
    business_type: str,
    competitor_count: int,
    population_density: float,
):

    business = business_type.lower()

    base_demand = 60

    common_businesses = [
        "dairy",
        "grocery",
        "kirana",
        "bakery",
        "cafe",
        "restaurant",
        "pharmacy",
        "salon",
        "food",
    ]

    if any(
        word in business
        for word in common_businesses
    ):

        base_demand += 10

    base_demand += (
        population_density * 0.15
    )

    if competitor_count <= 3:

        base_demand += 10

    elif competitor_count <= 10:

        base_demand += 5

    elif competitor_count <= 20:

        base_demand -= 5

    else:

        base_demand -= 10

    return round(
        max(
            0,
            min(
                base_demand,
                100
            )
        ),
        2
    )


# ============================================================
# OPPORTUNITY
# ============================================================

def calculate_opportunity(
    market_demand: float,
    competitor_count: int,
):

    if competitor_count <= 0:

        competition_penalty = -5

    elif competitor_count <= 5:

        competition_penalty = 10

    elif competitor_count <= 10:

        competition_penalty = 5

    elif competitor_count <= 20:

        competition_penalty = 0

    elif competitor_count <= 30:

        competition_penalty = -5

    else:

        competition_penalty = max(
            -25,
            -5 - (
                (competitor_count - 30)
                * 0.10
            )
        )

    score = (
        market_demand
        + competition_penalty
    )

    return round(
        max(
            0,
            min(
                score,
                100
            )
        ),
        2
    )


# ============================================================
# PROFIT POTENTIAL
# ============================================================

def calculate_profit_potential(
    market_demand: float,
    purchasing_power: float,
):

    score = (
        market_demand * 0.55
        +
        purchasing_power * 0.45
    )

    return round(
        max(
            0,
            min(
                score,
                100
            )
        ),
        2
    )


# ============================================================
# RISK / SAFETY
# ============================================================

def calculate_risk_safety(
    weather: dict,
):

    score = 80

    if not weather.get("success"):

        return score

    wind = weather.get(
        "wind_speed_kmh"
    )

    precipitation = weather.get(
        "precipitation_mm"
    )

    if wind is not None:

        if wind >= 60:

            score -= 30

        elif wind >= 40:

            score -= 20

        elif wind >= 25:

            score -= 10

    if precipitation is not None:

        if precipitation >= 20:

            score -= 20

        elif precipitation >= 10:

            score -= 10

        elif precipitation >= 5:

            score -= 5

    return round(
        max(
            0,
            min(
                score,
                100
            )
        ),
        2
    )


# ============================================================
# NORMALIZE DEMOGRAPHIC DATA
# ============================================================

def convert_population_density_to_score(
    density
):

    if density is None:
        return 50

    try:

        density = float(density)

    except (
        TypeError,
        ValueError
    ):

        return 50

    if density <= 0:
        return 0

    score = (
        density / 3000
    ) * 100

    return round(
        max(
            0,
            min(
                score,
                100
            )
        ),
        2
    )


# ============================================================
# NORMALIZE PURCHASING POWER
# ============================================================

def get_purchasing_power_score(
    location_data,
    demographic_data,
):

    proxy = location_data.get(
        "purchasing_power_proxy"
    )

    if proxy is not None:

        try:

            proxy = float(proxy)

            return round(
                max(
                    0,
                    min(
                        proxy,
                        100
                    )
                ),
                2
            )

        except (
            TypeError,
            ValueError
        ):

            pass

    demographic_power = (
        demographic_data
        .get(
            "purchasing_power",
            {}
        )
        .get(
            "purchasing_power"
        )
    )

    if demographic_power is None:
        return 50

    try:

        demographic_power = float(
            demographic_power
        )

    except (
        TypeError,
        ValueError
    ):

        return 50

    if demographic_power >= 30000:

        return 90

    elif demographic_power >= 25000:

        return 75

    elif demographic_power >= 20000:

        return 65

    elif demographic_power >= 15000:

        return 50

    else:

        return 35


# ============================================================
# PURCHASING POWER LABEL
# ============================================================

def get_purchasing_power_level(
    score: float
):

    if score >= 70:

        return "Good"

    elif score >= 40:

        return "Moderate"

    else:

        return "Low"


# ============================================================
# MAIN MODULE 1 ANALYSIS
# ============================================================

@app.get("/module1/analyze")
async def analyze_business(

    latitude: float,

    longitude: float,

    business_type: str,

):

    business_type = business_type.strip()

    if not business_type:

        return {

            "success": False,

            "message":
                "Business type is required.",
        }

    # --------------------------------------------------------
    # STEP 1 - Location Insights
    # --------------------------------------------------------

    try:

        location_result = (
            await get_location_insights(
                latitude,
                longitude,
            )
        )

        if not isinstance(
            location_result,
            dict
        ):

            location_result = {
                "success": False
            }

    except Exception as e:

        print(
            "LOCATION INSIGHT ERROR:",
            e
        )

        location_result = {
            "success": False
        }

    # --------------------------------------------------------
    # STEP 2 - Demographic Analysis
    # --------------------------------------------------------

    try:

        demographic_result = (
            await get_demographic_analysis(
                latitude,
                longitude,
            )
        )

        if not isinstance(
            demographic_result,
            dict
        ):

            demographic_result = {}

    except Exception as e:

        print(
            "DEMOGRAPHIC ERROR:",
            e
        )

        demographic_result = {

            "population": {
                "success": False
            },

            "purchasing_power": {
                "success": False
            },

        }

    # --------------------------------------------------------
    # STEP 3 - Competitors
    # --------------------------------------------------------

    competitor_result = (
        await get_competitors(
            latitude,
            longitude,
            business_type,
        )
    )

    competitors = competitor_result.get(
        "competitors",
        []
    )

    competitor_count = competitor_result.get(
        "competitor_count",
        len(competitors)
    )

    try:

        competitor_count = int(
            competitor_count
        )

    except (
        TypeError,
        ValueError
    ):

        competitor_count = len(
            competitors
        )

    # --------------------------------------------------------
    # STEP 4 - Population density
    # --------------------------------------------------------

    actual_density = location_result.get(
        "population_density"
    )

    if actual_density is None:

        actual_density = (
            demographic_result
            .get(
                "population",
                {}
            )
            .get(
                "population_density"
            )
        )

    population_score = (
        convert_population_density_to_score(
            actual_density
        )
    )

    # --------------------------------------------------------
    # STEP 5 - Purchasing power
    # --------------------------------------------------------

    purchasing_power_score = (
        get_purchasing_power_score(
            location_result,
            demographic_result,
        )
    )

    purchasing_power_level = (
        get_purchasing_power_level(
            purchasing_power_score
        )
    )

    # --------------------------------------------------------
    # STEP 6 - Market demand
    # --------------------------------------------------------

    market_demand = (
        calculate_market_demand(
            business_type,
            competitor_count,
            population_score,
        )
    )

    # --------------------------------------------------------
    # STEP 7 - Opportunity
    # --------------------------------------------------------

    opportunity = (
        calculate_opportunity(
            market_demand,
            competitor_count,
        )
    )

    # --------------------------------------------------------
    # STEP 8 - Profit potential
    # --------------------------------------------------------

    profit_potential = (
        calculate_profit_potential(
            market_demand,
            purchasing_power_score,
        )
    )

    # --------------------------------------------------------
    # STEP 9 - Competition level
    # --------------------------------------------------------

    try:

        competition_level = (
            calculate_competition_level(
                competitor_count
            )
        )

    except Exception as e:

        print(
            "COMPETITION SCORE ERROR:",
            e
        )

        competition_level = 50

    # --------------------------------------------------------
    # STEP 10 - Weather
    # --------------------------------------------------------

    weather = await get_weather(
        latitude,
        longitude,
    )

    # --------------------------------------------------------
    # STEP 11 - Risk / Safety
    # --------------------------------------------------------

    risk_safety = (
        calculate_risk_safety(
            weather
        )
    )

    # --------------------------------------------------------
    # STEP 12 - Final feasibility
    # --------------------------------------------------------

    try:

        feasibility = (
            calculate_feasibility_score(

                market_demand=market_demand,

                population_density=population_score,

                purchasing_power=purchasing_power_score,

                opportunity=opportunity,

                profit_potential=profit_potential,

                risk_safety=risk_safety,

                competition_level=competition_level,

            )
        )

    except Exception as e:

        print(
            "FEASIBILITY ERROR:",
            e
        )

        feasibility = {
            "feasibility_score": 0,
            "recommendation": "LOW OPPORTUNITY"
        }

    # --------------------------------------------------------
    # STEP 13 - Return everything
    # --------------------------------------------------------

    return {

        "success": True,

        "business_type": business_type,

        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        "latitude": latitude,

        "longitude": longitude,

        # ----------------------------------------------------
        # Market
        # ----------------------------------------------------

        "market_demand":
            market_demand,

        "market_data_source":
            "Local business and location analysis",

        # ----------------------------------------------------
        # Population
        # ----------------------------------------------------

        "population_density":
            population_score,

        "population_density_actual":
            actual_density,

        "population_density_unit":
            "people/km²",

        "population_data_source":
            location_result.get(
                "population_data_source",
                demographic_result
                .get("population", {})
                .get(
                    "population_data_source",
                    "WorldPop"
                )
            ),

        "population_estimate":
            location_result.get(
                "population_estimate"
            )
            or
            demographic_result
            .get(
                "population",
                {}
            )
            .get(
                "population_estimate"
            ),

        # ----------------------------------------------------
        # Purchasing Power
        # ----------------------------------------------------

        "purchasing_power":
            purchasing_power_score,

        "purchasing_power_level":
            purchasing_power_level,

        "purchasing_power_proxy":
            location_result.get(
                "purchasing_power_proxy"
            ),

        "purchasing_power_data_source":
            location_result.get(
                "purchasing_power_data_source"
            )
            or
            demographic_result
            .get(
                "purchasing_power",
                {}
            )
            .get(
                "purchasing_power_data_source"
            ),

        "purchasing_power_year":
            demographic_result
            .get(
                "purchasing_power",
                {}
            )
            .get(
                "purchasing_power_year"
            ),

        # ----------------------------------------------------
        # Competition
        # ----------------------------------------------------

        "competitor_count":
            competitor_count,

        "competition_level":
            competition_level,

        "competitor_data_availability":
            competitor_result.get(
                "competitor_data_availability",
                "LIMITED"
            ),

        "competitor_data_source":
            competitor_result.get(
                "competitor_data_source"
            ),

        "matched_osm_tags":
            competitor_result.get(
                "matched_osm_tags"
            ),

        "competitors":
            competitors,

        # ----------------------------------------------------
        # Opportunity
        # ----------------------------------------------------

        "opportunity":
            opportunity,

        # ----------------------------------------------------
        # Profit
        # ----------------------------------------------------

        "profit_potential":
            profit_potential,

        # ----------------------------------------------------
        # Risk
        # ----------------------------------------------------

        "risk_safety":
            risk_safety,

        "risk_data_source":
            "Open-Meteo weather analysis",

        "current_weather":
            weather,

        # ----------------------------------------------------
        # Final feasibility
        # ----------------------------------------------------

        "feasibility":
            feasibility,

    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
