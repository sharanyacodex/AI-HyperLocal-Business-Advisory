from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import httpx
import math

# ============================================================
# YOUR EXISTING SERVICES
# ============================================================

from app.services.demographics_service import get_demographic_analysis
from app.services.location_insights_service import get_location_insights
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
# API URLS
# ============================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

POSTAL_PINCODE_URL = (
    "https://api.postalpincode.in/pincode"
)

OVERPASS_URL = (
    "https://overpass-api.de/api/interpreter"
)

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


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
# PINCODE SERVICE
# ============================================================

@app.get("/pincode")
async def get_pincode_location(
    pincode: str = Query(
        ...,
        min_length=6,
        max_length=6,
    )
):

    # --------------------------------------------------------
    # Validate PIN
    # --------------------------------------------------------

    pincode = pincode.strip()

    if not pincode.isdigit() or len(pincode) != 6:

        return {
            "success": False,
            "message": "Please enter a valid 6-digit PIN code.",
        }

    # --------------------------------------------------------
    # STEP 1:
    # Get Indian postal information
    # --------------------------------------------------------

    try:

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=3.0,
                read=6.0,
                write=6.0,
                pool=3.0,
            )
        ) as client:

            response = await client.get(
                f"{POSTAL_PINCODE_URL}/{pincode}"
            )

            response.raise_for_status()

            data = response.json()

        print("POSTAL PIN RESPONSE:", data)

    except httpx.TimeoutException:

        return {
            "success": False,
            "message": "Pincode service timed out. Please try again.",
        }

    except Exception as e:

        print(
            "POSTAL PIN ERROR:",
            e,
        )

        return {
            "success": False,
            "message": "Could not retrieve pincode information.",
        }

    # --------------------------------------------------------
    # STEP 2:
    # Validate postal response
    # --------------------------------------------------------

    if not data:

        return {
            "success": False,
            "message": "PIN code not found.",
        }

    postal_result = data[0]

    if postal_result.get("Status") != "Success":

        return {
            "success": False,
            "message": postal_result.get(
                "Message",
                "PIN code not found.",
            ),
        }

    post_offices = postal_result.get(
        "PostOffice",
        [],
    )

    if not post_offices:

        return {
            "success": False,
            "message": "No location found for this PIN code.",
        }

    # --------------------------------------------------------
    # STEP 3:
    # Extract first postal office
    # --------------------------------------------------------

    office = post_offices[0]

    location_name = (
        office.get("Name")
        or office.get("Block")
        or office.get("Division")
        or ""
    )

    district = (
        office.get("District")
        or ""
    )

    state = (
        office.get("State")
        or ""
    )

    country = (
        office.get("Country")
        or "India"
    )

    # --------------------------------------------------------
    # STEP 4:
    # Get coordinates
    #
    # Postal PIN API does not normally provide coordinates.
    # Therefore we use Nominatim only for geocoding here.
    # --------------------------------------------------------

    latitude = None
    longitude = None
    display_name = ""

    search_queries = []

    # Most specific search first
    if location_name and district and state:

        search_queries.append(
            f"{location_name}, {district}, {state}, India"
        )

    # Fallback
    if district and state:

        search_queries.append(
            f"{district}, {state}, India"
        )

    # Another fallback
    if state:

        search_queries.append(
            f"{state}, India"
        )

    headers = {
        "User-Agent": (
            "AI-Rural-Business-Advisory/1.0 "
            "(local-business-analysis)"
        ),
        "Accept-Language": "en",
    }

    for search_query in search_queries:

        try:

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=2.0,
                    read=4.0,
                    write=4.0,
                    pool=2.0,
                )
            ) as client:

                geo_response = await client.get(
                    NOMINATIM_URL,
                    params={
                        "q": search_query,
                        "format": "json",
                        "limit": 1,
                        "countrycodes": "in",
                    },
                    headers=headers,
                )

                geo_response.raise_for_status()

                geo_data = geo_response.json()

            print(
                "GEOCODING RESPONSE:",
                search_query,
                geo_data,
            )

            if geo_data:

                try:

                    latitude = float(
                        geo_data[0]["lat"]
                    )

                    longitude = float(
                        geo_data[0]["lon"]
                    )

                    display_name = (
                        geo_data[0].get(
                            "display_name",
                            "",
                        )
                    )

                    break

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ):

                    continue

        except Exception as e:

            print(
                "GEOCODING WARNING:",
                e,
            )

            continue

    # --------------------------------------------------------
    # STEP 5:
    # If coordinates could not be found
    # --------------------------------------------------------

    if latitude is None or longitude is None:

        return {
            "success": False,
            "message": (
                "PIN code was found, but coordinates "
                "could not be determined. Please try again."
            ),
            "pincode": pincode,
            "location_name": location_name,
            "district": district,
            "state": state,
            "country": country,
        }

    # --------------------------------------------------------
    # STEP 6:
    # Return complete location data
    # --------------------------------------------------------

    return {

        "success": True,

        "pincode": pincode,

        "location_name": location_name,

        "district": district,

        "state": state,

        "country": country,

        "latitude": latitude,

        "longitude": longitude,

        "display_name": (
            display_name
            or ", ".join(
                part
                for part in [
                    location_name,
                    district,
                    state,
                    country,
                ]
                if part
            )
        ),

        "data_source": (
            "India Postal PIN Code API + "
            "OpenStreetMap / Nominatim"
        ),
    }


# ============================================================
# COMPETITOR SEARCH
# ============================================================

async def get_competitors(
    latitude: float,
    longitude: float,
    business_type: str,
    radius_m: int = 10000,
):

    # --------------------------------------------------------
    # Clean business type
    # --------------------------------------------------------

    business = business_type.strip().lower()

    # --------------------------------------------------------
    # Decide OSM search tags
    # --------------------------------------------------------

    search_terms = []

    if any(
        word in business
        for word in [
            "cafe",
            "coffee",
            "restaurant",
            "food",
            "hotel",
            "bakery",
            "sweet",
        ]
    ):

        search_terms = [
            '["amenity"="restaurant"]',
            '["amenity"="cafe"]',
            '["shop"="bakery"]',
            '["shop"="confectionery"]',
        ]

    elif any(
        word in business
        for word in [
            "dairy",
            "milk",
        ]
    ):

        search_terms = [
            '["shop"="dairy"]',
            '["shop"="convenience"]',
        ]

    elif any(
        word in business
        for word in [
            "grocery",
            "supermarket",
            "general store",
            "kirana",
        ]
    ):

        search_terms = [
            '["shop"="supermarket"]',
            '["shop"="convenience"]',
            '["shop"="grocery"]',
        ]

    elif any(
        word in business
        for word in [
            "salon",
            "beauty",
            "parlour",
            "barber",
        ]
    ):

        search_terms = [
            '["shop"="hairdresser"]',
            '["shop"="beauty"]',
        ]

    elif any(
        word in business
        for word in [
            "pharmacy",
            "medical",
        ]
    ):

        search_terms = [
            '["amenity"="pharmacy"]',
        ]

    else:

        search_terms = [
            '["shop"]',
            '["amenity"]',
        ]

    # --------------------------------------------------------
    # Build Overpass query
    # --------------------------------------------------------

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
    [out:json][timeout:40];

    (
        {"".join(query_parts)}
    );

    out center;
    """

    try:

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,
                read=45.0,
                write=45.0,
                pool=5.0,
            )
        ) as client:

            response = await client.post(
                OVERPASS_URL,
                data=query,
            )

            response.raise_for_status()

            data = response.json()

        elements = data.get(
            "elements",
            [],
        )

        competitors = []

        for element in elements:

            tags = element.get(
                "tags",
                {},
            )

            # ------------------------------------------------
            # Coordinates
            # ------------------------------------------------

            if element.get("type") == "node":

                lat = element.get("lat")
                lon = element.get("lon")

            else:

                center = element.get(
                    "center",
                    {},
                )

                lat = center.get("lat")
                lon = center.get("lon")

            if lat is None or lon is None:
                continue

            # ------------------------------------------------
            # Name
            # ------------------------------------------------

            name = (
                tags.get("name")
                or tags.get("brand")
                or "Nearby Business"
            )

            # ------------------------------------------------
            # Category
            # ------------------------------------------------

            category = (
                tags.get("shop")
                or tags.get("amenity")
                or tags.get("office")
                or "business"
            )

            # ------------------------------------------------
            # Address
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Distance
            # ------------------------------------------------

            distance_m = calculate_distance(
                latitude,
                longitude,
                float(lat),
                float(lon),
            )

            # ------------------------------------------------
            # Only keep within radius
            # ------------------------------------------------

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
                        2,
                    ),

                    "place_id": str(
                        element.get(
                            "id",
                            "",
                        )
                    ),
                }
            )

        # ----------------------------------------------------
        # Remove duplicate businesses
        # ----------------------------------------------------

        unique = {}

        for competitor in competitors:

            key = (
                competitor["name"],
                round(
                    competitor["latitude"],
                    5,
                ),
                round(
                    competitor["longitude"],
                    5,
                ),
            )

            unique[key] = competitor

        competitors = list(
            unique.values()
        )

        # ----------------------------------------------------
        # Sort by distance
        # ----------------------------------------------------

        competitors.sort(
            key=lambda x: x["distance_m"]
        )

        return {

            "success": True,

            "competitors": competitors,

            "competitor_count": len(
                competitors
            ),

            "competitor_data_availability":
                "AVAILABLE"
                if competitors
                else "LIMITED",

            "competitor_radius_km":
                radius_m / 1000,

            "competitor_data_source":
                "OpenStreetMap / Overpass",
        }

    except httpx.TimeoutException:

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
            e,
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
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2,
):

    earth_radius = 6371000

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = (
        2
        * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )
    )

    return earth_radius * c


# ============================================================
# WEATHER
# ============================================================

async def get_weather(
    latitude: float,
    longitude: float,
):

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "wind_speed_10m,"
            "precipitation,"
            "weather_code"
        ),

    }

    try:

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=3.0,
                read=8.0,
                write=8.0,
                pool=3.0,
            )
        ) as client:

            response = await client.get(
                OPEN_METEO_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        current = data.get(
            "current",
            {},
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
                current.get(
                    "weather_code"
                ),

            "data_source":
                "Open-Meteo",

        }

    except Exception as e:

        print(
            "WEATHER ERROR:",
            e,
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

    # --------------------------------------------------------
    # Base demand
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Population effect
    # --------------------------------------------------------

    base_demand += (
        population_density * 0.15
    )

    # --------------------------------------------------------
    # Competition effect
    # --------------------------------------------------------

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
                100,
            ),
        ),
        2,
    )


# ============================================================
# OPPORTUNITY
# ============================================================

def calculate_opportunity(
    market_demand: float,
    competitor_count: int,
):

    score = market_demand

    if competitor_count <= 5:

        score += 15

    elif competitor_count <= 10:

        score += 5

    elif competitor_count <= 20:

        score -= 5

    else:

        score -= 15

    return round(
        max(
            0,
            min(
                score,
                100,
            ),
        ),
        2,
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
                100,
            ),
        ),
        2,
    )


# ============================================================
# RISK / SAFETY
# ============================================================

def calculate_risk_safety(
    weather: dict,
):

    # Start with safe baseline

    score = 80

    if not weather.get(
        "success"
    ):

        return score

    wind = weather.get(
        "wind_speed_kmh"
    )

    precipitation = weather.get(
        "precipitation_mm"
    )

    # --------------------------------------------------------
    # Wind
    # --------------------------------------------------------

    if wind is not None:

        if wind >= 60:

            score -= 30

        elif wind >= 40:

            score -= 20

        elif wind >= 25:

            score -= 10

    # --------------------------------------------------------
    # Precipitation
    # --------------------------------------------------------

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
                100,
            ),
        ),
        2,
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
        ValueError,
    ):

        return 50

    # --------------------------------------------------------
    # Convert actual people/km² into 0-100 score
    # --------------------------------------------------------

    if density < 500:

        return 25

    elif density < 1000:

        return 40

    elif density < 1500:

        return 55

    elif density < 3000:

        return 75

    else:

        return 90


# ============================================================
# NORMALIZE PURCHASING POWER
# ============================================================

def get_purchasing_power_score(
    location_data,
    demographic_data,
):

    # --------------------------------------------------------
    # First use location insight proxy
    # --------------------------------------------------------

    proxy = location_data.get(
        "purchasing_power_proxy"
    )

    if proxy is not None:

        try:

            return float(proxy)

        except (
            TypeError,
            ValueError,
        ):

            pass

    # --------------------------------------------------------
    # Fallback to demographic service
    # --------------------------------------------------------

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
        ValueError,
    ):

        return 50

    # --------------------------------------------------------
    # Convert World Bank value to 0-100
    # --------------------------------------------------------

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
# MAIN MODULE 1 ANALYSIS
# ============================================================

@app.get("/module1/analyze")
async def analyze_business(

    latitude: float,

    longitude: float,

    business_type: str,

):

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    business_type = business_type.strip()

    if not business_type:

        return {

            "success": False,

            "message":
                "Business type is required.",
        }

    # --------------------------------------------------------
    # STEP 1
    # Location Insights
    # --------------------------------------------------------

    try:

        location_result = (
            await get_location_insights(
                latitude,
                longitude,
            )
        )

    except Exception as e:

        print(
            "LOCATION INSIGHT ERROR:",
            e,
        )

        location_result = {
            "success": False
        }

    # --------------------------------------------------------
    # STEP 2
    # Demographic Analysis
    # --------------------------------------------------------

    try:

        demographic_result = (
            await get_demographic_analysis(
                latitude,
                longitude,
            )
        )

    except Exception as e:

        print(
            "DEMOGRAPHIC ERROR:",
            e,
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
    # STEP 3
    # Competitors
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
        [],
    )

    competitor_count = competitor_result.get(
        "competitor_count",
        len(competitors),
    )

    # --------------------------------------------------------
    # STEP 4
    # Population density
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
    # STEP 5
    # Purchasing power
    # --------------------------------------------------------

    purchasing_power_score = (
        get_purchasing_power_score(
            location_result,
            demographic_result,
        )
    )

    # --------------------------------------------------------
    # STEP 6
    # Market demand
    # --------------------------------------------------------

    market_demand = (
        calculate_market_demand(
            business_type,
            competitor_count,
            population_score,
        )
    )

    # --------------------------------------------------------
    # STEP 7
    # Opportunity
    # --------------------------------------------------------

    opportunity = (
        calculate_opportunity(
            market_demand,
            competitor_count,
        )
    )

    # --------------------------------------------------------
    # STEP 8
    # Profit potential
    # --------------------------------------------------------

    profit_potential = (
        calculate_profit_potential(
            market_demand,
            purchasing_power_score,
        )
    )

    # --------------------------------------------------------
    # STEP 9
    # Competition level
    # --------------------------------------------------------

    competition_level = (
        calculate_competition_level(
            competitor_count
        )
    )

    # --------------------------------------------------------
    # STEP 10
    # Weather
    # --------------------------------------------------------

    weather = await get_weather(
        latitude,
        longitude,
    )

    # --------------------------------------------------------
    # STEP 11
    # Risk / Safety
    # --------------------------------------------------------

    risk_safety = (
        calculate_risk_safety(
            weather
        )
    )

    # --------------------------------------------------------
    # STEP 12
    # FINAL FEASIBILITY
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # STEP 13
    # Return everything to frontend
    # --------------------------------------------------------

    return {

        "success": True,

        "business_type":
            business_type,

        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        "latitude":
            latitude,

        "longitude":
            longitude,

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

        "population_data_source":
            location_result.get(
                "population_data_source",
                "WorldPop",
            ),

        "population_estimate":
            location_result.get(
                "population_estimate"
            ),

        # ----------------------------------------------------
        # Purchasing Power
        # ----------------------------------------------------

        "purchasing_power":
            purchasing_power_score,

        "purchasing_power_proxy":
            location_result.get(
                "purchasing_power_proxy"
            ),

        "purchasing_power_level":
            location_result.get(
                "purchasing_power_level"
            ),

        "purchasing_power_data_source":
            location_result.get(
                "purchasing_power_data_source"
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
                "LIMITED",
            ),

        "competitor_data_source":
            competitor_result.get(
                "competitor_data_source"
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
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():

    return {
        "success": True,
        "status": "healthy",
    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )