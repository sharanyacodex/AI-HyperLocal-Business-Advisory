import os
import math
import httpx
from dotenv import load_dotenv

load_dotenv()

GEOAPIFY_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")


# ============================================================
# BUSINESS TYPE → GEOAPIFY CATEGORIES
# ============================================================

BUSINESS_CATEGORIES = {

    "dairy": [
        "commercial.food_and_drink.cheese_and_dairy",
        "commercial.food_and_drink"
    ],

    "dairy shop": [
        "commercial.food_and_drink.cheese_and_dairy",
        "commercial.food_and_drink"
    ],

    "milk shop": [
        "commercial.food_and_drink.cheese_and_dairy",
        "commercial.food_and_drink"
    ],

    "grocery": [
        "commercial.supermarket",
        "commercial.convenience"
    ],

    "grocery shop": [
        "commercial.supermarket",
        "commercial.convenience"
    ],

    "supermarket": [
        "commercial.supermarket"
    ],

    "bakery": [
        "commercial.food_and_drink"
    ],

    "meat": [
        "commercial.food_and_drink"
    ],

    "meat shop": [
        "commercial.food_and_drink"
    ],

    "butcher": [
        "commercial.food_and_drink"
    ],

    "fish": [
        "commercial.food_and_drink"
    ],

    "fish shop": [
        "commercial.food_and_drink"
    ],

    "restaurant": [
        "catering.restaurant"
    ],

    "cafe": [
        "catering.cafe"
    ],

    "coffee shop": [
        "catering.cafe"
    ],

    "fast food": [
        "catering.fast_food"
    ],

    "pharmacy": [
        "healthcare.pharmacy"
    ],

    "medical shop": [
        "healthcare.pharmacy"
    ],

    "medicine shop": [
        "healthcare.pharmacy"
    ],

    "clothing": [
        "commercial.clothing"
    ],

    "clothing shop": [
        "commercial.clothing"
    ],

    "clothes": [
        "commercial.clothing"
    ],

    "mobile shop": [
        "commercial.elektronics"
    ],

    "electronics": [
        "commercial.elektronics"
    ],

    "electronics shop": [
        "commercial.elektronics"
    ],

    "hardware": [
        "commercial.houseware_and_hardware"
    ],

    "hardware shop": [
        "commercial.houseware_and_hardware"
    ],

    "furniture": [
        "commercial.furniture_and_interior"
    ],

    "furniture shop": [
        "commercial.furniture_and_interior"
    ],

    "book shop": [
        "commercial.books"
    ],

    "bookstore": [
        "commercial.books"
    ],

    "stationery": [
        "commercial.stationery"
    ],

    "stationery shop": [
        "commercial.stationery"
    ],

    "salon": [
        "service.beauty"
    ],

    "beauty salon": [
        "service.beauty"
    ],

    "barber": [
        "service.beauty"
    ],

    "laundry": [
        "service.laundry"
    ],

    "tailor": [
        "service.tailor"
    ],

    "pet shop": [
        "commercial.pet"
    ],

    "florist": [
        "commercial.florist"
    ],

    "flower shop": [
        "commercial.florist"
    ],
}


# ============================================================
# KEYWORDS FOR BROAD FALLBACK SEARCH
# ============================================================

BUSINESS_KEYWORDS = {

    "dairy": [
        "dairy",
        "milk",
        "milk products",
        "dairy products",
        "amul",
        "mother dairy",
        "milk booth",
        "milk center",
        "milk centre",
        "dairy farm",
        "dairy shop"
    ],

    "dairy shop": [
        "dairy",
        "milk",
        "dairy products",
        "milk shop",
        "milk booth",
        "milk center",
        "milk centre",
        "dairy shop"
    ],

    "milk shop": [
        "milk",
        "dairy",
        "milk shop",
        "milk booth",
        "milk center",
        "milk centre",
        "dairy products"
    ],

    "grocery": [
        "grocery",
        "supermarket",
        "mart",
        "store",
        "bazaar",
        "market"
    ],

    "grocery shop": [
        "grocery",
        "supermarket",
        "mart",
        "store"
    ],

    "supermarket": [
        "supermarket",
        "mart",
        "hypermarket"
    ],

    "bakery": [
        "bakery",
        "bakers",
        "cake",
        "bread"
    ],

    "meat": [
        "meat",
        "butcher",
        "chicken",
        "mutton"
    ],

    "meat shop": [
        "meat",
        "butcher",
        "chicken",
        "mutton"
    ],

    "butcher": [
        "butcher",
        "meat",
        "chicken",
        "mutton"
    ],

    "fish": [
        "fish",
        "fisheries"
    ],

    "fish shop": [
        "fish",
        "fisheries"
    ],

    "restaurant": [
        "restaurant",
        "food",
        "hotel"
    ],

    "cafe": [
        "cafe",
        "coffee"
    ],

    "coffee shop": [
        "coffee",
        "cafe"
    ],

    "fast food": [
        "fast food",
        "restaurant",
        "burger",
        "pizza"
    ],

    "pharmacy": [
        "pharmacy",
        "medical",
        "medicine",
        "drug"
    ],

    "medical shop": [
        "medical",
        "pharmacy",
        "medicine"
    ],

    "medicine shop": [
        "medicine",
        "pharmacy",
        "medical"
    ],

    "clothing": [
        "clothing",
        "fashion",
        "garments",
        "apparel"
    ],

    "clothing shop": [
        "clothing",
        "fashion",
        "garments",
        "apparel"
    ],

    "clothes": [
        "clothing",
        "fashion",
        "garments",
        "apparel"
    ],

    "mobile shop": [
        "mobile",
        "cell phone",
        "smartphone"
    ],

    "electronics": [
        "electronics",
        "electronic"
    ],

    "electronics shop": [
        "electronics",
        "electronic"
    ],

    "hardware": [
        "hardware",
        "tools",
        "building materials"
    ],

    "hardware shop": [
        "hardware",
        "tools",
        "building materials"
    ],

    "furniture": [
        "furniture",
        "interior"
    ],

    "furniture shop": [
        "furniture",
        "interior"
    ],

    "book shop": [
        "book",
        "books",
        "bookstore"
    ],

    "bookstore": [
        "book",
        "books",
        "bookstore"
    ],

    "stationery": [
        "stationery",
        "stationary",
        "school supplies"
    ],

    "stationery shop": [
        "stationery",
        "stationary",
        "school supplies"
    ],

    "salon": [
        "salon",
        "beauty",
        "hair"
    ],

    "beauty salon": [
        "salon",
        "beauty"
    ],

    "barber": [
        "barber",
        "salon",
        "hair"
    ],

    "laundry": [
        "laundry",
        "dry cleaning"
    ],

    "tailor": [
        "tailor",
        "tailoring"
    ],

    "pet shop": [
        "pet",
        "animal",
        "pet shop"
    ],

    "florist": [
        "florist",
        "flower",
        "flowers"
    ],

    "flower shop": [
        "florist",
        "flower",
        "flowers"
    ],
}


# ============================================================
# NORMALIZE BUSINESS TYPE
# ============================================================

def normalize_business_type(business_type: str) -> str:

    if not business_type:
        return ""

    return " ".join(
        business_type.lower().strip().split()
    )


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:

    earth_radius_km = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    dlat = lat2_rad - lat1_rad
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius_km * c


# ============================================================
# GEOAPIFY REQUEST
# ============================================================

async def search_geoapify(
    latitude: float,
    longitude: float,
    category: str,
    radius: int
):

    if not GEOAPIFY_API_KEY:
        return None

    params = {
        "apiKey": GEOAPIFY_API_KEY,
        "categories": category,
        "filter": f"circle:{longitude},{latitude},{radius}",
        "bias": f"proximity:{longitude},{latitude}",
        "limit": 100,
        "lang": "en",
    }

    try:

        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:

            response = await client.get(
                GEOAPIFY_URL,
                params=params
            )

            response.raise_for_status()

            return response.json()

    except httpx.TimeoutException:

        print(
            f"Geoapify timeout: {category}"
        )

        return None

    except httpx.HTTPStatusError as e:

        print(
            f"Geoapify HTTP error "
            f"{e.response.status_code}: {category}"
        )

        return None

    except Exception as e:

        print(
            f"Geoapify error: {e}"
        )

        return None


# ============================================================
# CHECK WHETHER BUSINESS MATCHES REQUESTED TYPE
# ============================================================

def is_relevant_business(
    properties: dict,
    business: str
) -> bool:

    # --------------------------------------------------------
    # For broad categories, don't filter unnecessarily
    # --------------------------------------------------------

    if business not in (
        "dairy",
        "dairy shop",
        "milk shop"
    ):
        return True

    keywords = BUSINESS_KEYWORDS.get(
        business,
        []
    )

    # --------------------------------------------------------
    # Collect searchable text
    # --------------------------------------------------------

    name = str(
        properties.get("name", "")
    ).lower()

    address = str(
        properties.get("formatted", "")
    ).lower()

    category_data = properties.get(
        "categories",
        []
    )

    if isinstance(category_data, list):

        category_text = " ".join(
            str(x).lower()
            for x in category_data
        )

    else:

        category_text = str(
            category_data
        ).lower()

    commercial_type = str(
        properties.get(
            "commercial",
            {}
        )
    ).lower()

    searchable_text = " ".join([
        name,
        address,
        category_text,
        commercial_type
    ])

    # --------------------------------------------------------
    # Dairy keyword matching
    # --------------------------------------------------------

    for keyword in keywords:

        if keyword.lower() in searchable_text:
            return True

    return False


# ============================================================
# PROCESS GEOAPIFY FEATURES
# ============================================================

def process_features(
    features,
    latitude,
    longitude,
    radius,
    business,
    competitors,
    seen
):

    for feature in features:

        properties = feature.get(
            "properties",
            {}
        )

        geometry = feature.get(
            "geometry",
            {}
        )

        coordinates = geometry.get(
            "coordinates",
            []
        )

        if (
            not isinstance(coordinates, list)
            or len(coordinates) < 2
        ):
            continue

        try:

            shop_longitude = float(
                coordinates[0]
            )

            shop_latitude = float(
                coordinates[1]
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        # ----------------------------------------------------
        # DISTANCE
        # ----------------------------------------------------

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            shop_latitude,
            shop_longitude
        )

        if distance_km > radius / 1000:
            continue

        # ----------------------------------------------------
        # RELEVANCE FILTER
        # ----------------------------------------------------

        if not is_relevant_business(
            properties,
            business
        ):
            continue

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = (
            properties.get("name")
            or properties.get("address_line1")
            or "Unnamed business"
        )

        # ----------------------------------------------------
        # PLACE ID
        # ----------------------------------------------------

        place_id = properties.get(
            "place_id"
        )

        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------

        if place_id:

            key = str(place_id)

        else:

            key = (
                str(name).lower().strip(),
                round(shop_latitude, 5),
                round(shop_longitude, 5)
            )

        if key in seen:
            continue

        seen.add(key)

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        category_data = properties.get(
            "categories",
            []
        )

        if isinstance(category_data, list):

            category_name = (
                category_data[0]
                if category_data
                else business
            )

        else:

            category_name = str(
                category_data
            )

        # ----------------------------------------------------
        # ADDRESS
        # ----------------------------------------------------

        address = properties.get(
            "formatted",
            ""
        )

        # ----------------------------------------------------
        # ADD COMPETITOR
        # ----------------------------------------------------

        competitors.append({

            "name": name,

            "latitude": shop_latitude,

            "longitude": shop_longitude,

            "category": category_name,

            "address": address,

            "distance_m": round(
                distance_km * 1000,
                2
            ),

            "place_id": place_id,

        })


# ============================================================
# FIND NEARBY COMPETITORS
# ============================================================

async def find_nearby_competitors(
    latitude: float,
    longitude: float,
    business_type: str,
    radius: int = 10000,
):

    # --------------------------------------------------------
    # CHECK API KEY
    # --------------------------------------------------------

    if not GEOAPIFY_API_KEY:

        return {
            "success": False,
            "message": "GEOAPIFY_API_KEY is missing.",
            "competitor_count": 0,
            "competitors": [],
            "source": "Geoapify Places API",
            "competition_level": 0,
        }

    # --------------------------------------------------------
    # VALIDATE COORDINATES
    # --------------------------------------------------------

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except (
        TypeError,
        ValueError
    ):

        return {
            "success": False,
            "message": "Invalid latitude or longitude.",
            "competitor_count": 0,
            "competitors": [],
            "source": "Geoapify Places API",
            "competition_level": 0,
        }

    # --------------------------------------------------------
    # RADIUS
    # --------------------------------------------------------

    try:

        radius = int(radius)

    except (
        TypeError,
        ValueError
    ):

        radius = 10000

    radius = min(
        max(radius, 100),
        10000
    )

    # --------------------------------------------------------
    # NORMALIZE BUSINESS
    # --------------------------------------------------------

    business = normalize_business_type(
        business_type
    )

    # --------------------------------------------------------
    # GET CATEGORIES
    # --------------------------------------------------------

    categories = BUSINESS_CATEGORIES.get(
        business
    )

    if not categories:

        return {
            "success": False,
            "message": (
                f"Unsupported business type: "
                f"{business_type}"
            ),
            "competitor_count": 0,
            "competitors": [],
            "source": "Geoapify Places API",
            "competition_level": 0,
        }

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    competitors = []
    seen = set()

    for category in categories:

        data = await search_geoapify(
            latitude=latitude,
            longitude=longitude,
            category=category,
            radius=radius
        )

        if not data:
            continue

        features = data.get(
            "features",
            []
        )

        print(
            f"Geoapify category "
            f"{category}: "
            f"{len(features)} results"
        )

        process_features(
            features=features,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            business=business,
            competitors=competitors,
            seen=seen
        )

    # --------------------------------------------------------
    # SORT BY DISTANCE
    # --------------------------------------------------------

    competitors.sort(
        key=lambda item: item.get(
            "distance_m",
            999999
        )
    )

    # --------------------------------------------------------
    # COUNT
    # --------------------------------------------------------

    competitor_count = len(
        competitors
    )

    # --------------------------------------------------------
    # COMPETITION LEVEL
    # --------------------------------------------------------

    if competitor_count == 0:

        competition_level = 0

    elif competitor_count <= 5:

        competition_level = 25

    elif competitor_count <= 10:

        competition_level = 50

    elif competitor_count <= 20:

        competition_level = 75

    else:

        competition_level = 100

    # --------------------------------------------------------
    # DATA AVAILABILITY
    # --------------------------------------------------------

    if competitor_count == 0:

        data_availability = "LIMITED"

    else:

        data_availability = "AVAILABLE"

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "success": True,

        "business_type": business_type,

        "search_radius_km": radius / 1000,

        "competitor_count": competitor_count,

        "competitors": competitors,

        "source": "Geoapify Places API",

        "competition_level": competition_level,

        "competitor_data_availability": data_availability,

    }


# ============================================================
# PINCODE → LOCATION → COMPETITORS
# ============================================================

async def find_nearby_competitors_by_pincode(
    pincode: str,
    business_type: str,
    radius_km: float = 10
):

    # --------------------------------------------------------
    # GET LOCATION FROM PINCODE
    # --------------------------------------------------------

    from app.services.location_service import resolve_pincode

    location = await resolve_pincode(
        pincode
    )

    # --------------------------------------------------------
    # LOCATION ERROR
    # --------------------------------------------------------

    if not location.get("success"):

        return {

            "success": False,

            "message": location.get(
                "message",
                "Could not resolve PIN code."
            ),

            "competitor_count": 0,

            "competitors": [],

            "source": "Geoapify Places API",

            "competition_level": 0,

        }

    # --------------------------------------------------------
    # GET COORDINATES
    # --------------------------------------------------------

    latitude = location.get(
        "latitude"
    )

    longitude = location.get(
        "longitude"
    )

    if (
        latitude is None
        or longitude is None
    ):

        return {

            "success": False,

            "message": (
                "Coordinates were not found "
                "for this PIN code."
            ),

            "competitor_count": 0,

            "competitors": [],

            "source": "Geoapify Places API",

            "competition_level": 0,

        }

    # --------------------------------------------------------
    # RADIUS
    # --------------------------------------------------------

    try:

        radius_km = float(
            radius_km
        )

    except (
        TypeError,
        ValueError
    ):

        radius_km = 10

    radius_km = min(
        max(radius_km, 0.1),
        10
    )

    radius_m = int(
        radius_km * 1000
    )

    # --------------------------------------------------------
    # FIND COMPETITORS
    # --------------------------------------------------------

    result = await find_nearby_competitors(

        latitude=latitude,

        longitude=longitude,

        business_type=business_type,

        radius=radius_m

    )

    # --------------------------------------------------------
    # ADD LOCATION INFORMATION
    # --------------------------------------------------------

    result["pincode"] = str(
        pincode
    )

    result["location_name"] = location.get(
        "location_name"
    )

    result["district"] = location.get(
        "district"
    )

    result["state"] = location.get(
        "state"
    )

    result["country"] = location.get(
        "country"
    )

    result["latitude"] = latitude

    result["longitude"] = longitude

    return result