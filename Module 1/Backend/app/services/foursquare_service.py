import os
import math
import httpx
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# FOURSQUARE PLACES API
# ==========================================================

FOURSQUARE_URL = (
    "https://places-api.foursquare.com/places/search"
)

FOURSQUARE_API_KEY = os.getenv(
    "FOURSQUARE_API_KEY"
)


# ==========================================================
# BUSINESS SEARCH TERMS
# ==========================================================

BUSINESS_SEARCH_TERMS = {
    "dairy": "dairy milk shop",
    "dairy shop": "dairy milk shop",
    "milk shop": "milk dairy",

    "grocery": "grocery general store",
    "grocery shop": "grocery general store",
    "supermarket": "supermarket grocery",

    "bakery": "bakery",
    "restaurant": "restaurant",
    "cafe": "cafe coffee",
    "coffee shop": "coffee shop",
    "fast food": "fast food",

    "pharmacy": "pharmacy medical shop",
    "medical shop": "medical shop pharmacy",
    "medicine shop": "medicine shop pharmacy",

    "clothing": "clothing garments",
    "clothing shop": "clothing garments",

    "mobile shop": "mobile phone shop",
    "electronics": "electronics shop",
    "electronics shop": "electronics shop",

    "hardware": "hardware shop tools",
    "hardware shop": "hardware shop tools",

    "furniture": "furniture shop",

    "book shop": "book shop bookstore",
    "bookstore": "bookstore",

    "stationery": "stationery shop",

    "salon": "salon beauty",
    "beauty salon": "beauty salon",
    "barber": "barber shop",

    "laundry": "laundry dry cleaning",
    "tailor": "tailor tailoring",

    "pet shop": "pet shop",
    "florist": "florist flower shop",
    "flower shop": "flower shop florist",

    "meat": "meat shop butcher",
    "meat shop": "meat shop butcher",
    "butcher": "butcher meat shop",

    "fish": "fish shop",
    "fish shop": "fish shop",
}


# ==========================================================
# NORMALIZE BUSINESS TYPE
# ==========================================================

def normalize_business_type(
    business_type: str
) -> str:

    if not business_type:
        return ""

    return " ".join(
        business_type.lower()
        .strip()
        .split()
    )


# ==========================================================
# DISTANCE CALCULATION
# ==========================================================

def calculate_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:

    earth_radius = 6371.0

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

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ==========================================================
# SEARCH FOURSQUARE
# ==========================================================

async def search_foursquare(
    latitude: float,
    longitude: float,
    business_type: str,
    radius: int = 10000,
):

    if not FOURSQUARE_API_KEY:
        raise RuntimeError(
            "FOURSQUARE_API_KEY is missing."
        )

    business = normalize_business_type(
        business_type
    )

    query = BUSINESS_SEARCH_TERMS.get(
        business,
        business
    )

    params = {
        "query": query,

        "ll": (
            f"{latitude},{longitude}"
        ),

        "radius": radius,

        "limit": 50,

        "sort": "DISTANCE",

        "fields": (
            "fsq_id,"
            "name,"
            "geocodes,"
            "location,"
            "categories,"
            "distance,"
            "website,"
            "tel"
        ),
    }

    headers = {
        "Accept": "application/json",

        "Authorization":
            f"Bearer {FOURSQUARE_API_KEY}",

        "X-Places-Api-Version":
            "2025-06-17",
    }

    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.get(
            FOURSQUARE_URL,
            params=params,
            headers=headers,
        )

        if response.status_code != 200:

            try:
                details = response.json()

            except Exception:
                details = response.text

            raise RuntimeError(
                f"Foursquare API error "
                f"{response.status_code}: "
                f"{details}"
            )

        return response.json()


# ==========================================================
# PROCESS FOURSQUARE RESULTS
# ==========================================================

def process_foursquare_results(
    data: dict,
    latitude: float,
    longitude: float,
    radius: int,
    business_type: str,
):

    results = data.get(
        "results",
        []
    )

    competitors = []

    seen = set()

    for place in results:

        if not isinstance(
            place,
            dict
        ):
            continue

        # --------------------------------------------------
        # Get coordinates
        # --------------------------------------------------

        geocodes = place.get(
            "geocodes",
            {}
        )

        main_coordinates = geocodes.get(
            "main",
            {}
        )

        try:

            shop_latitude = float(
                main_coordinates.get(
                    "latitude"
                )
            )

            shop_longitude = float(
                main_coordinates.get(
                    "longitude"
                )
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        # --------------------------------------------------
        # Distance safety check
        # --------------------------------------------------

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            shop_latitude,
            shop_longitude,
        )

        if distance_km * 1000 > radius:
            continue

        # --------------------------------------------------
        # Name
        # --------------------------------------------------

        name = place.get(
            "name"
        ) or "Unnamed business"

        # --------------------------------------------------
        # Categories
        # --------------------------------------------------

        categories = place.get(
            "categories",
            []
        )

        category_names = []

        if isinstance(
            categories,
            list
        ):

            for category in categories:

                if isinstance(
                    category,
                    dict
                ):

                    category_name = category.get(
                        "name"
                    )

                    if category_name:
                        category_names.append(
                            str(category_name)
                        )

        category = (
            ", ".join(category_names)
            if category_names
            else business_type
        )

        # --------------------------------------------------
        # Address
        # --------------------------------------------------

        location = place.get(
            "location",
            {}
        )

        if isinstance(
            location,
            dict
        ):

            address = location.get(
                "formatted_address"
            )

            if not address:

                address_parts = []

                for key in [
                    "address",
                    "locality",
                    "region",
                    "postcode",
                    "country"
                ]:

                    value = location.get(
                        key
                    )

                    if value:
                        address_parts.append(
                            str(value)
                        )

                address = ", ".join(
                    address_parts
                )

        else:

            address = ""

        # --------------------------------------------------
        # Distance
        # --------------------------------------------------

        api_distance = place.get(
            "distance"
        )

        if isinstance(
            api_distance,
            (int, float)
        ):

            distance_m = api_distance

        else:

            distance_m = round(
                distance_km * 1000,
                2
            )

        # --------------------------------------------------
        # Duplicate protection
        # --------------------------------------------------

        key = (
            str(name).lower().strip(),
            round(
                shop_latitude,
                5
            ),
            round(
                shop_longitude,
                5
            ),
        )

        if key in seen:
            continue

        seen.add(key)

        # --------------------------------------------------
        # Add competitor
        # --------------------------------------------------

        competitors.append({

            "name":
                str(name),

            "latitude":
                shop_latitude,

            "longitude":
                shop_longitude,

            "category":
                category,

            "address":
                address or "",

            "distance_m":
                distance_m,

            "place_id":
                place.get(
                    "fsq_id"
                ),

            "phone":
                place.get(
                    "tel"
                ),

            "website":
                place.get(
                    "website"
                ),

            "source":
                "Foursquare Places API",
        })

    # Sort by distance

    competitors.sort(
        key=lambda shop:
            shop.get(
                "distance_m",
                float("inf")
            )
    )

    return competitors


# ==========================================================
# MAIN FOURSQUARE FUNCTION
# ==========================================================

async def find_foursquare_competitors(
    latitude: float,
    longitude: float,
    business_type: str,
    radius: int = 10000,
):

    try:

        latitude = float(
            latitude
        )

        longitude = float(
            longitude
        )

    except (
        TypeError,
        ValueError
    ):

        return {
            "success": False,
            "message":
                "Invalid coordinates.",
            "competitor_count": 0,
            "competitors": [],
            "source":
                "Foursquare Places API",
        }

    radius = min(
        max(
            int(radius),
            100
        ),
        10000
    )

    try:

        data = await search_foursquare(
            latitude=latitude,
            longitude=longitude,
            business_type=business_type,
            radius=radius,
        )

        competitors = process_foursquare_results(
            data=data,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            business_type=business_type,
        )

        return {

            "success":
                True,

            "business_type":
                business_type,

            "search_radius_km":
                radius / 1000,

            "competitor_count":
                len(competitors),

            "competitors":
                competitors,

            "source":
                "Foursquare Places API",
        }

    except httpx.TimeoutException:

        return {

            "success":
                False,

            "message":
                "Foursquare request timed out.",

            "competitor_count":
                0,

            "competitors":
                [],

            "source":
                "Foursquare Places API",
        }

    except Exception as e:

        return {

            "success":
                False,

            "message":
                "Could not retrieve Foursquare competitor data.",

            "error":
                str(e),

            "competitor_count":
                0,

            "competitors":
                [],

            "source":
                "Foursquare Places API",
        }