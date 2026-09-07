from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, AliasChoices
from typing import Optional, Any, Dict, List
from dotenv import load_dotenv

import os
import math
import logging
import uuid
import asyncio
import httpx


# ============================================================
# GEMINI
# ============================================================

try:
    from google import genai
except ImportError:
    genai = None


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEOAPIFY_API_KEY = os.getenv(
    "GEOAPIFY_API_KEY", ""
).strip()

OLA_MAPS_API_KEY = os.getenv(
    "OLA_MAPS_API_KEY", ""
).strip()

GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY", "").strip()
    or os.getenv("GOOGLE_API_KEY", "").strip()
    or os.getenv("GOOGLE_GEMINI_API_KEY", "").strip()
)

# Your currently working Gemini model
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
).strip()


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(
    "ai-hyperlocal-business-advisory"
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="AI Hyper-Local Business Advisory API",
    version="1.0.0",
    description="AI-powered local business feasibility analysis."
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PINCODE OVERRIDES
#
# 700052 MUST return:
# District = North 24 Parganas
# State = West Bengal
# ============================================================

PINCODE_OVERRIDES: Dict[str, Dict[str, Any]] = {

    "700052": {
        "district": "North 24 Parganas",
        "state": "West Bengal",
        "country": "India",

        # Kaikhali / airport-side area
        "latitude": 22.6429,
        "longitude": 88.4382,
    },

}


# ============================================================
# REQUEST MODEL
#
# Frontend can send camelCase OR snake_case.
#
# Business Name is NOT required.
# ============================================================

class BusinessRequest(BaseModel):

    business_type: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices(
            "business_type",
            "businessType"
        )
    )

    city: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices(
            "city",
            "cityVillage",
            "city_village"
        )
    )

    pincode: str = Field(
        ...,
        min_length=6,
        max_length=6,
        validation_alias=AliasChoices(
            "pincode",
            "pinCode"
        )
    )

    nearest_landmark: Optional[str] = Field(
        default="",
        validation_alias=AliasChoices(
            "nearestLandmark",
            "nearest_landmark",
            "landmark"
        )
    )

    # Optional backward compatibility
    business_name: Optional[str] = Field(
        default="",
        validation_alias=AliasChoices(
            "businessName",
            "business_name"
        )
    )

    district: Optional[str] = ""
    state: Optional[str] = ""

    class Config:
        populate_by_name = True


# ============================================================
# GENERIC HTTP GET
# ============================================================

async def http_get_json(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: float = 15.0
):

    try:

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True
        ) as client:

            response = await client.get(
                url,
                params=params,
                headers=headers
            )

            logger.info(
                "GET %s -> %s",
                str(response.url),
                response.status_code
            )

            if response.status_code >= 400:

                logger.warning(
                    "API error %s: %s",
                    response.status_code,
                    response.text[:500]
                )

                return {}

            try:
                return response.json()

            except Exception:

                logger.warning(
                    "Invalid JSON returned by %s",
                    url
                )

                return {}

    except Exception as exc:

        logger.warning(
            "HTTP request failed: %s",
            exc
        )

        return {}


# ============================================================
# PINCODE CLEANER
# ============================================================

def clean_pincode(
    pincode: str
) -> str:

    return "".join(
        ch for ch in str(pincode)
        if ch.isdigit()
    )


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:

    earth_radius = 6371.0

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(
        lat2 - lat1
    )

    dl = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(dp / 2) ** 2
        +
        math.cos(p1)
        *
        math.cos(p2)
        *
        math.sin(dl / 2) ** 2
    )

    return (
        earth_radius
        *
        2
        *
        math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )
    )


# ============================================================
# GEOAPIFY PINCODE LOOKUP
# ============================================================

async def geoapify_pincode_lookup(
    pincode: str
) -> Dict[str, Any]:

    if not GEOAPIFY_API_KEY:

        logger.warning(
            "GEOAPIFY_API_KEY is missing."
        )

        return {}

    url = (
        "https://api.geoapify.com/"
        "v1/geocode/search"
    )

    params = {
        "text": pincode,
        "type": "postcode",
        "filter": "countrycode:in",
        "lang": "en",
        "limit": 10,
        "format": "json",
        "apiKey": GEOAPIFY_API_KEY,
    }

    data = await http_get_json(
        url,
        params=params
    )

    results = data.get(
        "results",
        []
    )

    if not isinstance(
        results,
        list
    ):

        return {}

    for result in results:

        if not isinstance(
            result,
            dict
        ):
            continue

        country_code = str(
            result.get(
                "country_code",
                ""
            )
        ).lower()

        if country_code == "in":

            return {
                "district": (
                    result.get("county")
                    or result.get("district")
                    or ""
                ),

                "state": (
                    result.get("state")
                    or ""
                ),

                "country": (
                    result.get("country")
                    or "India"
                ),

                "latitude": result.get("lat"),

                "longitude": result.get("lon"),

                "formatted": (
                    result.get("formatted")
                    or ""
                ),
            }

    return {}


# ============================================================
# GEOAPIFY LOCATION GEOCODING
# ============================================================

async def geoapify_geocode_location(
    city: str,
    district: str,
    state: str,
    pincode: str,
    landmark: str = ""
) -> Dict[str, Any]:

    if not GEOAPIFY_API_KEY:

        return {}

    url = (
        "https://api.geoapify.com/"
        "v1/geocode/search"
    )

    location_text = ", ".join(
        part
        for part in [
            city,
            landmark,
            district,
            state,
            pincode,
            "India"
        ]
        if part
    )

    params = {
        "text": location_text,
        "filter": "countrycode:in",
        "lang": "en",
        "limit": 10,
        "format": "json",
        "apiKey": GEOAPIFY_API_KEY,
    }

    data = await http_get_json(
        url,
        params=params
    )

    results = data.get(
        "results",
        []
    )

    if not isinstance(
        results,
        list
    ):

        return {}

    best = None
    best_score = -1

    district_lower = district.lower()
    state_lower = state.lower()
    city_lower = city.lower()

    for result in results:

        if not isinstance(
            result,
            dict
        ):
            continue

        result_district = str(
            result.get("county")
            or result.get("district")
            or ""
        ).lower()

        result_state = str(
            result.get("state")
            or ""
        ).lower()

        result_city = str(
            result.get("city")
            or result.get("suburb")
            or result.get("name")
            or ""
        ).lower()

        score = 0

        if (
            district_lower
            and district_lower in result_district
        ):
            score += 100

        if (
            state_lower
            and state_lower in result_state
        ):
            score += 50

        if (
            city_lower
            and city_lower in result_city
        ):
            score += 25

        if result.get("lat") is not None:
            score += 5

        if result.get("lon") is not None:
            score += 5

        if score > best_score:

            best_score = score
            best = result

    if best is None:

        return {}

    return {
        "latitude": best.get("lat"),
        "longitude": best.get("lon"),

        "formatted": (
            best.get("formatted")
            or ""
        ),

        "name": (
            best.get("name")
            or city
        ),

        "result_type": (
            best.get("result_type")
            or ""
        ),
    }


# ============================================================
# OLA MAPS GEOCODING
# ============================================================

async def ola_geocode(
    city: str,
    district: str,
    state: str,
    pincode: str,
    landmark: str = ""
) -> Dict[str, Any]:

    if not OLA_MAPS_API_KEY:

        return {}

    url = (
        "https://api.olamaps.io/"
        "places/v1/geocode"
    )

    query = ", ".join(
        part
        for part in [
            city,
            landmark,
            district,
            state,
            pincode,
            "India"
        ]
        if part
    )

    params = {
        "address": query,
        "api_key": OLA_MAPS_API_KEY,
    }

    headers = {
        "X-Request-Id": str(
            uuid.uuid4()
        )
    }

    data = await http_get_json(
        url,
        params=params,
        headers=headers
    )

    candidates = []

    if isinstance(
        data,
        dict
    ):

        for key in [
            "geocodingResults",
            "results",
            "places",
            "data"
        ]:

            value = data.get(key)

            if isinstance(
                value,
                list
            ):

                candidates.extend(
                    value
                )

    for item in candidates:

        if not isinstance(
            item,
            dict
        ):
            continue

        lat = (
            item.get("lat")
            or item.get("latitude")
        )

        lon = (
            item.get("lng")
            or item.get("lon")
            or item.get("longitude")
        )

        if lat is None or lon is None:
            continue

        try:

            return {
                "latitude": float(lat),
                "longitude": float(lon),

                "formatted": (
                    item.get("formatted")
                    or item.get("address")
                    or ""
                )
            }

        except (
            TypeError,
            ValueError
        ):

            continue

    return {}


# ============================================================
# RESOLVE LOCATION
# ============================================================

async def resolve_location(
    city: str,
    pincode: str,
    landmark: str
):

    override = PINCODE_OVERRIDES.get(
        pincode
    )

    # --------------------------------------------------------
    # AUTHORITATIVE DISTRICT + STATE
    # --------------------------------------------------------

    if override:

        district = override[
            "district"
        ]

        state = override[
            "state"
        ]

    else:

        geo_pin = await geoapify_pincode_lookup(
            pincode
        )

        district = (
            geo_pin.get("district")
            or "Unknown"
        )

        state = (
            geo_pin.get("state")
            or "Unknown"
        )

    # --------------------------------------------------------
    # GEOCODING
    # --------------------------------------------------------

    latitude = None
    longitude = None
    formatted = ""

    # First Geoapify
    geo_location = await geoapify_geocode_location(
        city=city,
        district=district,
        state=state,
        pincode=pincode,
        landmark=landmark
    )

    if geo_location:

        latitude = geo_location.get(
            "latitude"
        )

        longitude = geo_location.get(
            "longitude"
        )

        formatted = (
            geo_location.get(
                "formatted",
                ""
            )
        )

    # --------------------------------------------------------
    # Ola fallback
    # --------------------------------------------------------

    if (
        latitude is None
        or longitude is None
    ):

        ola_location = await ola_geocode(
            city=city,
            district=district,
            state=state,
            pincode=pincode,
            landmark=landmark
        )

        latitude = ola_location.get(
            "latitude"
        )

        longitude = ola_location.get(
            "longitude"
        )

        formatted = (
            ola_location.get(
                "formatted",
                ""
            )
            or formatted
        )

    # --------------------------------------------------------
    # PINCODE COORDINATE FALLBACK
    # --------------------------------------------------------

    if (
        latitude is None
        or longitude is None
    ):

        if override:

            latitude = override[
                "latitude"
            ]

            longitude = override[
                "longitude"
            ]

        else:

            latitude = 22.5726
            longitude = 88.3639

    return {

        "district": district,

        "state": state,

        "country": "India",

        "latitude": float(
            latitude
        ),

        "longitude": float(
            longitude
        ),

        "formatted": formatted,
    }


# ============================================================
# BUSINESS CATEGORY MAPPING
# ============================================================

def geoapify_categories_for_business(
    business_type: str
) -> str:

    b = business_type.lower().strip()

    if (
        "grocery" in b
        or "kirana" in b
    ):

        return (
            "commercial.supermarket,"
            "commercial.convenience,"
            "commercial.food_and_drink"
        )

    if "supermarket" in b:

        return (
            "commercial.supermarket,"
            "commercial.convenience"
        )

    if "restaurant" in b:

        return "catering.restaurant"

    if (
        "cafe" in b
        or "coffee" in b
    ):

        return "catering.cafe"

    if "bakery" in b:

        return "commercial.food_and_drink"

    if (
        "pharmacy" in b
        or "medical store" in b
    ):

        return "commercial.chemist"

    if (
        "clothing" in b
        or "garment" in b
    ):

        return "commercial.clothing"

    if "electronics" in b:

        return "commercial.electronics"

    if (
        "salon" in b
        or "beauty" in b
    ):

        return "service.beauty"

    return "commercial"


# ============================================================
# GEOAPIFY NEARBY BUSINESSES
# ============================================================

async def geoapify_nearby_businesses(
    latitude: float,
    longitude: float,
    business_type: str,
    radius: int = 10000
) -> List[Dict[str, Any]]:

    if not GEOAPIFY_API_KEY:

        logger.warning(
            "GEOAPIFY_API_KEY not configured."
        )

        return []

    categories = (
        geoapify_categories_for_business(
            business_type
        )
    )

    url = (
        "https://api.geoapify.com/"
        "v2/places"
    )

    params = {
        "categories": categories,

        "filter": (
            f"circle:{longitude},"
            f"{latitude},"
            f"{radius}"
        ),

        "bias": (
            f"proximity:"
            f"{longitude},"
            f"{latitude}"
        ),

        "limit": 50,

        "lang": "en",

        "apiKey": GEOAPIFY_API_KEY,
    }

    logger.info(
        "Geoapify competitor search: %s",
        categories
    )

    data = await http_get_json(
        url,
        params=params,
        timeout=15
    )

    features = data.get(
        "features",
        []
    )

    if not isinstance(
        features,
        list
    ):

        logger.warning(
            "Geoapify Places returned no features."
        )

        return []

    competitors = []

    for feature in features:

        if not isinstance(
            feature,
            dict
        ):
            continue

        properties = feature.get(
            "properties",
            {}
        )

        if not isinstance(
            properties,
            dict
        ):
            continue

        lat = properties.get(
            "lat"
        )

        lon = properties.get(
            "lon"
        )

        # Geometry fallback
        if (
            lat is None
            or lon is None
        ):

            geometry = feature.get(
                "geometry",
                {}
            )

            coordinates = (
                geometry.get(
                    "coordinates"
                )
                if isinstance(
                    geometry,
                    dict
                )
                else None
            )

            if (
                isinstance(
                    coordinates,
                    list
                )
                and len(coordinates) >= 2
            ):

                lon = coordinates[0]
                lat = coordinates[1]

        if (
            lat is None
            or lon is None
        ):

            continue

        try:

            lat = float(lat)
            lon = float(lon)

        except (
            TypeError,
            ValueError
        ):

            continue

        distance = haversine_distance_km(
            latitude,
            longitude,
            lat,
            lon
        )

        if distance > (
            radius / 1000
        ):

            continue

        name = (
            properties.get("name")
            or properties.get(
                "address_line1"
            )
            or "Nearby Business"
        )

        address = (
            properties.get("formatted")
            or properties.get(
                "address_line2"
            )
            or ""
        )

        categories_value = (
            properties.get(
                "categories",
                ""
            )
        )

        if isinstance(
            categories_value,
            list
        ):

            category = ", ".join(
                str(x)
                for x in categories_value[:3]
            )

        else:

            category = str(
                categories_value
                or "Business"
            )

        competitors.append({

            "name": str(
                name
            ),

            "latitude": lat,

            "longitude": lon,

            "category": category,

            "address": str(
                address
            ),

            "distance_km": round(
                distance,
                2
            ),

            "source": "Geoapify",
        })

    # --------------------------------------------------------
    # Remove duplicate businesses
    # --------------------------------------------------------

    unique = []
    seen = set()

    for shop in competitors:

        key = (
            shop["name"].lower().strip(),
            round(
                shop["latitude"],
                5
            ),
            round(
                shop["longitude"],
                5
            )
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            shop
        )

    unique.sort(
        key=lambda x: x.get(
            "distance_km",
            999
        )
    )

    logger.info(
        "Geoapify found %d competitors.",
        len(unique)
    )

    return unique[:50]


# ============================================================
# OLA MAPS NEARBY BUSINESSES
# ============================================================

def normalize_ola_places(
    data: Dict[str, Any]
) -> List[Dict[str, Any]]:

    places = []

    if not isinstance(
        data,
        dict
    ):

        return []

    possible_lists = [
        data.get("predictions"),
        data.get("results"),
        data.get("places"),
        data.get("data"),
    ]

    for candidate in possible_lists:

        if isinstance(
            candidate,
            list
        ):

            places.extend(
                candidate
            )

            break

    normalized = []

    for place in places:

        if not isinstance(
            place,
            dict
        ):

            continue

        lat = (
            place.get("lat")
            or place.get("latitude")
        )

        lon = (
            place.get("lng")
            or place.get("lon")
            or place.get("longitude")
        )

        # Nested coordinates
        if (
            lat is None
            or lon is None
        ):

            geometry = place.get(
                "geometry",
                {}
            )

            if isinstance(
                geometry,
                dict
            ):

                location = geometry.get(
                    "location",
                    {}
                )

                if isinstance(
                    location,
                    dict
                ):

                    lat = (
                        location.get("lat")
                        or location.get(
                            "latitude"
                        )
                    )

                    lon = (
                        location.get("lng")
                        or location.get("lon")
                        or location.get(
                            "longitude"
                        )
                    )

        if (
            lat is None
            or lon is None
        ):

            continue

        try:

            lat = float(lat)
            lon = float(lon)

        except (
            TypeError,
            ValueError
        ):

            continue

        name = (
            place.get("name")
            or place.get("displayName")
            or place.get("description")
            or "Nearby Business"
        )

        category = (
            place.get("category")
            or place.get("type")
            or "Business"
        )

        address = (
            place.get("address")
            or place.get("formattedAddress")
            or ""
        )

        normalized.append({

            "name": str(
                name
            ),

            "latitude": lat,

            "longitude": lon,

            "category": str(
                category
            ),

            "address": str(
                address
            ),

            "source": "Ola Maps",
        })

    return normalized


async def ola_nearby_businesses(
    latitude: float,
    longitude: float,
    business_type: str,
    radius: int = 10000
) -> List[Dict[str, Any]]:

    if not OLA_MAPS_API_KEY:

        logger.warning(
            "OLA_MAPS_API_KEY not configured."
        )

        return []

    url = (
        "https://api.olamaps.io/"
        "places/v1/nearbysearch"
    )

    category = (
        business_type
        .lower()
        .strip()
    )

    category_map = {

        "grocery store":
            "grocery_store",

        "grocery":
            "grocery_store",

        "kirana store":
            "grocery_store",

        "kirana":
            "grocery_store",

        "supermarket":
            "supermarket",

        "restaurant":
            "restaurant",

        "cafe":
            "cafe",

        "coffee shop":
            "cafe",

        "pharmacy":
            "pharmacy",

        "medical store":
            "pharmacy",

        "clothing":
            "clothing_store",

        "clothing store":
            "clothing_store",

        "bakery":
            "bakery",

        "salon":
            "beauty_salon",

        "beauty salon":
            "beauty_salon",

        "electronics":
            "electronics_store",

        "electronics store":
            "electronics_store",

        "hardware":
            "hardware_store",

        "hardware store":
            "hardware_store",
    }

    ola_type = category_map.get(
        category,
        category.replace(
            " ",
            "_"
        )
    )

    params = {

        "layers": "venue",

        "types": ola_type,

        "location": (
            f"{latitude},{longitude}"
        ),

        "radius": radius,

        "limit": 50,

        "api_key":
            OLA_MAPS_API_KEY,
    }

    headers = {

        "X-Request-Id":
            str(uuid.uuid4())
    }

    logger.info(
        "Ola competitor search: %s",
        ola_type
    )

    data = await http_get_json(
        url,
        params=params,
        headers=headers,
        timeout=15
    )

    places = normalize_ola_places(
        data
    )

    filtered = []

    for place in places:

        distance = haversine_distance_km(
            latitude,
            longitude,
            place["latitude"],
            place["longitude"]
        )

        if distance <= (
            radius / 1000
        ):

            place[
                "distance_km"
            ] = round(
                distance,
                2
            )

            filtered.append(
                place
            )

    # Do not count the user's exact location
    filtered = [
        p
        for p in filtered
        if haversine_distance_km(
            latitude,
            longitude,
            p["latitude"],
            p["longitude"]
        ) > 0.03
    ]

    filtered.sort(
        key=lambda x: x.get(
            "distance_km",
            999
        )
    )

    logger.info(
        "Ola Maps found %d competitors.",
        len(filtered)
    )

    return filtered[:50]


# ============================================================
# COMPETITOR FUNCTION
#
# Ola Maps first.
# Geoapify second.
# ============================================================

async def get_competitors(
    latitude: float,
    longitude: float,
    business_type: str
) -> List[Dict[str, Any]]:

    # --------------------------------------------------------
    # OLA MAPS
    # --------------------------------------------------------

    try:

        ola_competitors = (
            await ola_nearby_businesses(
                latitude,
                longitude,
                business_type,
                radius=10000
            )
        )

        if ola_competitors:

            logger.info(
                "Using Ola Maps competitor data."
            )

            return ola_competitors

    except Exception as exc:

        logger.exception(
            "Ola competitor search failed: %s",
            exc
        )

    # --------------------------------------------------------
    # GEOAPIFY FALLBACK
    # --------------------------------------------------------

    try:

        geo_competitors = (
            await geoapify_nearby_businesses(
                latitude,
                longitude,
                business_type,
                radius=10000
            )
        )

        if geo_competitors:

            logger.info(
                "Using Geoapify competitor data."
            )

            return geo_competitors

    except Exception as exc:

        logger.exception(
            "Geoapify competitor search failed: %s",
            exc
        )

    logger.warning(
        "Both competitor providers returned zero results."
    )

    return []


# ============================================================
# WEATHER
#
# Open-Meteo does not require an API key for normal usage.
# ============================================================

async def get_weather(
    latitude: float,
    longitude: float
):

    url = (
        "https://api.open-meteo.com/"
        "v1/forecast"
    )

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),

        "timezone": "auto",
    }

    data = await http_get_json(
        url,
        params=params,
        timeout=10
    )

    current = data.get(
        "current",
        {}
    )

    if not current:

        return {

            "temperature": None,

            "humidity": None,

            "apparentTemperature": None,

            "precipitation": None,

            "windSpeed": None,

            "weatherCode": None,

            "available": False,
        }

    return {

        "temperature":
            current.get(
                "temperature_2m"
            ),

        "humidity":
            current.get(
                "relative_humidity_2m"
            ),

        "apparentTemperature":
            current.get(
                "apparent_temperature"
            ),

        "precipitation":
            current.get(
                "precipitation"
            ),

        "windSpeed":
            current.get(
                "wind_speed_10m"
            ),

        "weatherCode":
            current.get(
                "weather_code"
            ),

        "available": True,
    }


# ============================================================
# CLAMP
# ============================================================

def clamp(
    value: int,
    minimum: int,
    maximum: int
) -> int:

    return max(
        minimum,
        min(
            maximum,
            int(value)
        )
    )


# ============================================================
# POPULATION SCORE
# ============================================================

def calculate_population_score(
    city: str,
    district: str
) -> int:

    text = (
        f"{city} {district}"
    ).lower()

    major_city_words = [

        "kolkata",

        "howrah",

        "salt lake",

        "new town",

        "barasat",

        "dum dum",

        "bidhannagar",

        "kaikhali",
    ]

    if any(
        word in text
        for word in major_city_words
    ):

        return 85

    return 70


# ============================================================
# PURCHASING POWER
# ============================================================

def calculate_purchase_power_score(
    city: str,
    district: str
) -> int:

    text = (
        f"{city} {district}"
    ).lower()

    higher_market = [

        "new town",

        "salt lake",

        "bidhannagar",

        "airport",

        "kaikhali",
    ]

    if any(
        word in text
        for word in higher_market
    ):

        return 78

    return 65


# ============================================================
# WEATHER SCORE
# ============================================================

def calculate_weather_score(
    weather: Dict[str, Any]
) -> int:

    if not weather.get(
        "available"
    ):

        return 65

    temperature = weather.get(
        "temperature"
    )

    precipitation = weather.get(
        "precipitation"
    )

    if temperature is None:

        return 65

    score = 75

    try:

        temperature = float(
            temperature
        )

        precipitation = float(
            precipitation or 0
        )

        if 18 <= temperature <= 32:

            score += 8

        elif temperature > 38:

            score -= 12

        elif temperature < 10:

            score -= 8

        if precipitation > 5:

            score -= 8

    except Exception:

        pass

    return clamp(
        score,
        0,
        100
    )


# ============================================================
# MARKET DEMAND
# ============================================================

def calculate_market_demand(
    business_type: str,
    population_score: int,
    purchase_score: int
) -> int:

    business = (
        business_type.lower()
    )

    demand_bonus = 0

    high_demand = [

        "grocery",

        "supermarket",

        "restaurant",

        "pharmacy",

        "medical",

        "bakery",

        "food",

        "cafe",

        "salon",
    ]

    if any(
        word in business
        for word in high_demand
    ):

        demand_bonus = 8

    score = (
        population_score * 0.55
        +
        purchase_score * 0.35
        +
        demand_bonus
    )

    return clamp(
        round(score),
        0,
        100
    )


# ============================================================
# COMPETITION SCORE
#
# More competitors = lower score.
# ============================================================

def calculate_competition_score(
    competitor_count: int
) -> int:

    if competitor_count <= 2:
        return 92

    if competitor_count <= 5:
        return 82

    if competitor_count <= 10:
        return 70

    if competitor_count <= 20:
        return 55

    if competitor_count <= 35:
        return 40

    return 28


# ============================================================
# PROFIT
# ============================================================

def calculate_profit_score(
    demand: int,
    competition: int,
    purchase_power: int
) -> int:

    score = (

        demand * 0.50

        +

        competition * 0.25

        +

        purchase_power * 0.25
    )

    return clamp(
        round(score),
        0,
        100
    )


# ============================================================
# OPPORTUNITY
# ============================================================

def calculate_opportunity_score(
    demand: int,
    competition: int,
    profit: int
) -> int:

    score = (

        demand * 0.40

        +

        competition * 0.30

        +

        profit * 0.30
    )

    return clamp(
        round(score),
        0,
        100
    )


# ============================================================
# RISK
#
# Higher number = higher risk.
# ============================================================

def calculate_risk_score(
    competition: int,
    weather_score: int
) -> int:

    risk = (

        (100 - competition)
        * 0.65

        +

        (100 - weather_score)
        * 0.35
    )

    return clamp(
        round(risk),
        0,
        100
    )


# ============================================================
# FINAL FEASIBILITY
# ============================================================

def calculate_feasibility(
    demand: int,
    competition: int,
    profit: int,
    opportunity: int,
    risk: int
) -> int:

    score = (

        demand * 0.25

        +

        competition * 0.15

        +

        profit * 0.25

        +

        opportunity * 0.25

        +

        (100 - risk) * 0.10
    )

    return clamp(
        round(score),
        0,
        100
    )


# ============================================================
# RECOMMENDATION
# ============================================================

def recommendation_from_score(
    score: int
) -> str:

    if score >= 80:

        return "GOOD OPPORTUNITY"

    if score >= 65:

        return "MODERATE OPPORTUNITY"

    if score >= 50:

        return "PROCEED WITH CAUTION"

    return "LOW OPPORTUNITY"


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():

    if not GEMINI_API_KEY:

        logger.warning(
            "GEMINI_API_KEY not configured."
        )

        return None

    if genai is None:

        logger.warning(
            "google-genai is not installed."
        )

        return None

    try:

        return genai.Client(
            api_key=GEMINI_API_KEY
        )

    except Exception as exc:

        logger.exception(
            "Gemini initialization failed."
        )

        return None


# ============================================================
# GEMINI RECOMMENDATION
# ============================================================

async def generate_gemini_recommendation(
    business_type: str,
    city: str,
    district: str,
    state: str,
    pincode: str,
    landmark: str,
    scores: Dict[str, int],
    weather: Dict[str, Any],
    competitor_count: int
) -> str:

    client = get_gemini_client()

    if client is None:

        return (
            "Gemini AI is not configured. "
            "Please check your Gemini API key "
            "and google-genai installation."
        )

    prompt = f"""
You are an AI Hyper-Local Business Advisor.

Analyze the following proposed business.

Business Type:
{business_type}

City / Village:
{city}

District:
{district}

State:
{state}

Pincode:
{pincode}

Nearest Landmark:
{landmark or "Not provided"}

Market Demand:
{scores["marketDemand"]}/100

Competition Score:
{scores["competition"]}/100

Profit Potential:
{scores["profitPotential"]}/100

Market Opportunity:
{scores["marketOpportunity"]}/100

Risk:
{scores["risk"]}/100

Final Feasibility:
{scores["feasibility"]}/100

Nearby competitors found:
{competitor_count}

Temperature:
{weather.get("temperature", "Not available")} °C

Humidity:
{weather.get("humidity", "Not available")} %

Give a practical business recommendation.

Requirements:

1. Start with a clear recommendation.
2. Explain customer demand.
3. Explain competition.
4. Explain profit potential.
5. Mention relevant weather conditions.
6. Give exactly 3 practical actions.
7. Do not invent exact population numbers.
8. Do not invent revenue figures.
9. Do not invent competitor names.
10. Keep the language simple and easy to understand.
"""

    try:

        response = await asyncio.to_thread(
            client.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt
        )

        text = getattr(
            response,
            "text",
            None
        )

        if text:

            return text.strip()

        return (
            "Gemini returned no recommendation."
        )

    except Exception as exc:

        logger.exception(
            "Gemini API failed."
        )

        return (
            "Gemini recommendation could not "
            "be generated at this moment."
        )


# ============================================================
# ROOT / HEALTH CHECK
# ============================================================

@app.get("/")
async def root():

    return {

        "status": "ok",

        "message":
            "AI Hyper-Local Business Advisory "
            "backend is running.",

        "apis": {

            "geoapify":
                bool(
                    GEOAPIFY_API_KEY
                ),

            "olaMaps":
                bool(
                    OLA_MAPS_API_KEY
                ),

            "gemini":
                bool(
                    GEMINI_API_KEY
                ),
        }
    }


# ============================================================
# PINCODE API
# ============================================================

@app.get(
    "/api/pincode/{pincode}"
)
async def pincode_lookup(
    pincode: str
):

    pincode = clean_pincode(
        pincode
    )

    if len(pincode) != 6:

        raise HTTPException(
            status_code=400,
            detail="Enter a valid 6-digit pincode."
        )

    # --------------------------------------------------------
    # OVERRIDE FIRST
    # --------------------------------------------------------

    override = PINCODE_OVERRIDES.get(
        pincode
    )

    if override:

        return {

            "success": True,

            "pincode": pincode,

            "district":
                override["district"],

            "state":
                override["state"],

            "country":
                "India",

            "latitude":
                override["latitude"],

            "longitude":
                override["longitude"],
        }

    # --------------------------------------------------------
    # GEOAPIFY
    # --------------------------------------------------------

    result = await geoapify_pincode_lookup(
        pincode
    )

    if result:

        return {

            "success": True,

            "pincode": pincode,

            "district":
                result.get(
                    "district",
                    ""
                ),

            "state":
                result.get(
                    "state",
                    ""
                ),

            "country":
                result.get(
                    "country",
                    "India"
                ),

            "latitude":
                result.get(
                    "latitude"
                ),

            "longitude":
                result.get(
                    "longitude"
                ),
        }

    raise HTTPException(
        status_code=404,
        detail=(
            "Pincode could not be found. "
            "Please check the pincode."
        )
    )


# ============================================================
# MAIN ANALYZE API
# ============================================================

@app.post(
    "/api/analyze"
)
@app.post(
    "/analyze"
)
async def analyze_business(
    request: BusinessRequest
):

    # ========================================================
    # CLEAN INPUT
    # ========================================================

    business_type = (
        request.business_type.strip()
    )

    city = (
        request.city.strip()
    )

    pincode = clean_pincode(
        request.pincode
    )

    landmark = (
        request.nearest_landmark
        or ""
    ).strip()

    # ========================================================
    # VALIDATION
    # ========================================================

    if not business_type:

        raise HTTPException(
            status_code=422,
            detail="Business type is required."
        )

    if not city:

        raise HTTPException(
            status_code=422,
            detail="City / Village is required."
        )

    if len(pincode) != 6:

        raise HTTPException(
            status_code=422,
            detail="Pincode must contain exactly 6 digits."
        )

    # ========================================================
    # LOCATION
    # ========================================================

    location = await resolve_location(
        city=city,
        pincode=pincode,
        landmark=landmark
    )

    district = location[
        "district"
    ]

    state = location[
        "state"
    ]

    latitude = location[
        "latitude"
    ]

    longitude = location[
        "longitude"
    ]

    # ========================================================
    # EXTERNAL APIs
    #
    # Competitor + weather run simultaneously.
    # ========================================================

    competitors_task = (
        get_competitors(
            latitude,
            longitude,
            business_type
        )
    )

    weather_task = (
        get_weather(
            latitude,
            longitude
        )
    )

    competitors, weather = await asyncio.gather(
        competitors_task,
        weather_task
    )

    # Always make sure frontend receives ARRAY.
    if not isinstance(
        competitors,
        list
    ):

        competitors = []

    competitor_count = len(
        competitors
    )

    # ========================================================
    # SCORES
    # ========================================================

    population_score = (
        calculate_population_score(
            city,
            district
        )
    )

    purchasing_score = (
        calculate_purchase_power_score(
            city,
            district
        )
    )

    weather_score = (
        calculate_weather_score(
            weather
        )
    )

    market_demand = (
        calculate_market_demand(
            business_type,
            population_score,
            purchasing_score
        )
    )

    competition_score = (
        calculate_competition_score(
            competitor_count
        )
    )

    profit_score = (
        calculate_profit_score(
            market_demand,
            competition_score,
            purchasing_score
        )
    )

    opportunity_score = (
        calculate_opportunity_score(
            market_demand,
            competition_score,
            profit_score
        )
    )

    risk_score = (
        calculate_risk_score(
            competition_score,
            weather_score
        )
    )

    feasibility = (
        calculate_feasibility(
            market_demand,
            competition_score,
            profit_score,
            opportunity_score,
            risk_score
        )
    )

    recommendation = (
        recommendation_from_score(
            feasibility
        )
    )

    # ========================================================
    # SCORES OBJECT
    # ========================================================

    scores = {

        "marketDemand":
            market_demand,

        "competition":
            competition_score,

        "profitPotential":
            profit_score,

        "marketOpportunity":
            opportunity_score,

        "risk":
            risk_score,

        "feasibility":
            feasibility,
    }

    # ========================================================
    # GEMINI
    # ========================================================

    ai_recommendation = (
        await generate_gemini_recommendation(

            business_type=
                business_type,

            city=
                city,

            district=
                district,

            state=
                state,

            pincode=
                pincode,

            landmark=
                landmark,

            scores=
                scores,

            weather=
                weather,

            competitor_count=
                competitor_count
        )
    )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "success": True,

        # ----------------------------------------------------
        # BUSINESS
        # ----------------------------------------------------

        "businessType":
            business_type,

        "business_type":
            business_type,

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        "city":
            city,

        "district":
            district,

        "state":
            state,

        "pincode":
            pincode,

        "landmark":
            landmark,

        "nearestLandmark":
            landmark,

        # ----------------------------------------------------
        # COORDINATES
        # ----------------------------------------------------

        "latitude":
            latitude,

        "longitude":
            longitude,

        "coordinates": {

            "latitude":
                latitude,

            "longitude":
                longitude,
        },

        # ----------------------------------------------------
        # LOCATION OBJECT
        # ----------------------------------------------------

        "location": {

            "city":
                city,

            "district":
                district,

            "state":
                state,

            "pincode":
                pincode,

            "landmark":
                landmark,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "formatted":
                location.get(
                    "formatted",
                    ""
                ),
        },

        # ----------------------------------------------------
        # FEASIBILITY
        # ----------------------------------------------------

        "feasibility":
            feasibility,

        "feasibilityScore":
            feasibility,

        "recommendation":
            recommendation,

        # ----------------------------------------------------
        # MARKET SIGNALS
        # ----------------------------------------------------

        "marketSignals": {

            "marketDemand":
                market_demand,

            "competition":
                competition_score,

            "profitPotential":
                profit_score,

            "marketOpportunity":
                opportunity_score,

            "risk":
                risk_score,
        },

        # Flat values for frontend compatibility

        "marketDemand":
            market_demand,

        "competition":
            competition_score,

        "profitPotential":
            profit_score,

        "marketOpportunity":
            opportunity_score,

        "risk":
            risk_score,

        # ----------------------------------------------------
        # AREA INSIGHTS
        # ----------------------------------------------------

        "areaInsights": {

            "population":
                "Local population data not directly available",

            "populationScore":
                population_score,

            "purchasingPower":
                "Estimated local purchasing-power indicator",

            "purchasingPowerScore":
                purchasing_score,

            "temperature":
                weather.get(
                    "temperature"
                ),

            "humidity":
                weather.get(
                    "humidity"
                ),

            "weatherAvailable":
                weather.get(
                    "available",
                    False
                ),
        },

        # ----------------------------------------------------
        # WEATHER
        # ----------------------------------------------------

        "weather":
            weather,

        # ----------------------------------------------------
        # COMPETITORS
        #
        # IMPORTANT:
        # This is ALWAYS an array.
        # ----------------------------------------------------

        "competitors":
            competitors,

        "competitorCount":
            competitor_count,

        # ----------------------------------------------------
        # GEMINI
        # ----------------------------------------------------

        "aiRecommendation":
            ai_recommendation,

        "geminiRecommendation":
            ai_recommendation,

        "ai": {

            "provider":
                "Gemini",

            "model":
                GEMINI_MODEL,

            "recommendation":
                ai_recommendation,
        },

        # ----------------------------------------------------
        # API STATUS
        # ----------------------------------------------------

        "apiStatus": {

            "geoapify":
                bool(
                    GEOAPIFY_API_KEY
                ),

            "olaMaps":
                bool(
                    OLA_MAPS_API_KEY
                ),

            "gemini":
                bool(
                    GEMINI_API_KEY
                ),

            "weather":
                weather.get(
                    "available",
                    False
                ),
        },
    }


# ============================================================
# DEBUG LOCATION API
# ============================================================

@app.get(
    "/api/location/{pincode}"
)
async def location_debug(
    pincode: str
):

    pincode = clean_pincode(
        pincode
    )

    if len(pincode) != 6:

        raise HTTPException(
            status_code=400,
            detail="Invalid pincode."
        )

    location = await resolve_location(
        city="",
        pincode=pincode,
        landmark=""
    )

    return {

        "success": True,

        "pincode":
            pincode,

        **location,
    }


# ============================================================
# DEBUG COMPETITOR API
#
# Useful for checking why competitor count is 0.
# ============================================================

@app.get(
    "/api/competitors"
)
async def competitor_debug(
    latitude: float,
    longitude: float,
    businessType: str = "grocery store"
):

    competitors = await get_competitors(
        latitude,
        longitude,
        businessType
    )

    return {

        "success": True,

        "businessType":
            businessType,

        "latitude":
            latitude,

        "longitude":
            longitude,

        "competitorCount":
            len(competitors),

        "competitors":
            competitors,
    }


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
    # third