import asyncio
import math
import json
import httpx


# ============================================================
# API URLS
# ============================================================

# Correct WorldPop API
WORLDPOP_URL = "https://api.worldpop.org/v1/services/stats"

# OpenStreetMap Overpass API
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate distance between two coordinates
    using the Haversine formula.

    Returns distance in meters.
    """

    earth_radius = 6371000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    a = max(0.0, min(1.0, a))

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return earth_radius * c


# ============================================================
# POPULATION DENSITY
# WORLDPOP
# ============================================================

async def get_population_density(
    latitude: float,
    longitude: float,
):
    """
    Estimate population around the selected location
    using WorldPop.

    Approximately 1 km x 1 km area is analysed.
    """

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    try:
        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError):

        return {
            "success": False,
            "message": "Invalid coordinates.",
            "population_density": None,
        }

    # --------------------------------------------------------
    # Validate coordinate range
    # --------------------------------------------------------

    if not (-90 <= latitude <= 90):
        return {
            "success": False,
            "message": "Invalid latitude.",
            "population_density": None,
        }

    if not (-180 <= longitude <= 180):
        return {
            "success": False,
            "message": "Invalid longitude.",
            "population_density": None,
        }

    # --------------------------------------------------------
    # Approximately 1 km x 1 km square
    # --------------------------------------------------------

    lat_offset = 0.0045

    cos_lat = max(
        abs(math.cos(math.radians(latitude))),
        0.1,
    )

    lon_offset = 0.0045 / cos_lat

    south = latitude - lat_offset
    north = latitude + lat_offset
    west = longitude - lon_offset
    east = longitude + lon_offset

    # --------------------------------------------------------
    # GeoJSON FeatureCollection
    # WorldPop stats API expects GeoJSON
    # --------------------------------------------------------

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [west, south],
                        [east, south],
                        [east, north],
                        [west, north],
                        [west, south],
                    ]],
                },
            }
        ],
    }

    params = {
        "dataset": "wpgppop",
        "year": 2020,
        "geojson": json.dumps(geojson),
        "runasync": "false",
    }

    # --------------------------------------------------------
    # Call WorldPop
    # --------------------------------------------------------

    try:

        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:

            response = await client.get(
                WORLDPOP_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        # ----------------------------------------------------
        # WorldPop response format:
        #
        # {
        #   "status": "finished",
        #   "data": {
        #       "total_population": ...
        #   }
        # }
        # ----------------------------------------------------

        if not isinstance(data, dict):

            return {
                "success": False,
                "message": "Invalid WorldPop response.",
                "population_density": None,
            }

        if data.get("error") is True:

            return {
                "success": False,
                "message": data.get(
                    "error_message",
                    "WorldPop returned an error.",
                ),
                "population_density": None,
            }

        api_data = data.get(
            "data",
            {},
        )

        if not isinstance(api_data, dict):

            return {
                "success": False,
                "message": "Population data unavailable.",
                "population_density": None,
            }

        total_population = api_data.get(
            "total_population"
        )

        if total_population is None:

            return {
                "success": False,
                "message": "Population data unavailable.",
                "population_density": None,
            }

        total_population = float(
            total_population
        )

        # ----------------------------------------------------
        # Calculate actual area
        # ----------------------------------------------------

        lat_distance = calculate_distance(
            south,
            longitude,
            north,
            longitude,
        )

        lon_distance = calculate_distance(
            latitude,
            west,
            latitude,
            east,
        )

        area_km2 = (
            (lat_distance / 1000)
            * (lon_distance / 1000)
        )

        if area_km2 <= 0:
            area_km2 = 1.0

        # ----------------------------------------------------
        # Population density
        # ----------------------------------------------------

        population_density = (
            total_population / area_km2
        )

        population_density = round(
            population_density,
            2,
        )

        total_population = round(
            total_population,
            0,
        )

        area_km2 = round(
            area_km2,
            2,
        )

        # ----------------------------------------------------
        # Density score
        # ----------------------------------------------------

        if population_density < 500:

            density_score = 20
            density_level = "LOW"

        elif population_density < 1500:

            density_score = 40
            density_level = "MODERATE"

        elif population_density < 3000:

            density_score = 70
            density_level = "HIGH"

        else:

            density_score = 90
            density_level = "VERY HIGH"

        # ----------------------------------------------------
        # Return
        # ----------------------------------------------------

        return {

            "success": True,

            "population_estimate":
                total_population,

            "population_density":
                population_density,

            "population_density_actual":
                population_density,

            "population_density_unit":
                "people/km²",

            "population_density_score":
                density_score,

            "population_density_level":
                density_level,

            "population_area_km2":
                area_km2,

            "population_data_year":
                2020,

            "population_data_source":
                "WorldPop",

        }

    except httpx.TimeoutException:

        print(
            "WorldPop timeout"
        )

        return {

            "success": False,

            "message":
                "Population service timed out.",

            "population_density":
                None,

        }

    except httpx.HTTPStatusError as e:

        print(
            "WorldPop HTTP error:",
            e.response.status_code,
        )

        return {

            "success": False,

            "message":
                "Population service returned an HTTP error.",

            "population_density":
                None,

        }

    except Exception as e:

        print(
            "WorldPop error:",
            repr(e),
        )

        return {

            "success": False,

            "message":
                "Could not retrieve population data.",

            "population_density":
                None,

        }


# ============================================================
# PURCHASING POWER / LOCAL ECONOMIC ACTIVITY
# OPENSTREETMAP / OVERPASS
# ============================================================

async def get_purchasing_power_proxy(
    latitude: float,
    longitude: float,
    radius_m: int = 10000,
):
    """
    Estimate local purchasing-power proxy from
    mapped economic activity.

    IMPORTANT:
    This is NOT actual household income.

    It is a location-based proxy using:
    - Banks
    - ATMs
    - Supermarkets
    - Marketplaces
    - Department stores
    """

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError):

        return {

            "success": False,

            "purchasing_power":
                None,

            "purchasing_power_proxy":
                None,

            "message":
                "Invalid coordinates.",

        }

    # --------------------------------------------------------
    # Validate radius
    # --------------------------------------------------------

    try:

        radius_m = int(radius_m)

    except (TypeError, ValueError):

        radius_m = 10000

    radius_m = max(
        1000,
        min(radius_m, 10000),
    )

    # --------------------------------------------------------
    # Overpass query
    # --------------------------------------------------------

    query = f"""
    [out:json][timeout:30];

    (
        nwr["amenity"="bank"]
            (around:{radius_m},{latitude},{longitude});

        nwr["amenity"="atm"]
            (around:{radius_m},{latitude},{longitude});

        nwr["shop"="supermarket"]
            (around:{radius_m},{latitude},{longitude});

        nwr["amenity"="marketplace"]
            (around:{radius_m},{latitude},{longitude});

        nwr["shop"="department_store"]
            (around:{radius_m},{latitude},{longitude});
    );

    out center;
    """

    # --------------------------------------------------------
    # Call Overpass
    # --------------------------------------------------------

    try:

        async with httpx.AsyncClient(
            timeout=45.0
        ) as client:

            response = await client.post(
                OVERPASS_URL,
                data=query,
            )

            response.raise_for_status()

            data = response.json()

        if not isinstance(data, dict):

            return {

                "success": False,

                "purchasing_power":
                    None,

                "purchasing_power_proxy":
                    None,

                "message":
                    "Invalid OpenStreetMap response.",

            }

        elements = data.get(
            "elements",
            [],
        )

        if not isinstance(elements, list):

            elements = []

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        banks = 0
        atms = 0
        supermarkets = 0
        marketplaces = 0
        department_stores = 0

        # ----------------------------------------------------
        # Weighted activity score
        # ----------------------------------------------------

        weighted_score = 0.0

        # ----------------------------------------------------
        # Prevent duplicate OSM objects
        # ----------------------------------------------------

        seen = set()

        for element in elements:

            element_id = (
                element.get("type"),
                element.get("id"),
            )

            if element_id in seen:
                continue

            seen.add(
                element_id
            )

            tags = element.get(
                "tags",
                {},
            )

            if not isinstance(tags, dict):
                tags = {}

            # ------------------------------------------------
            # Coordinates
            # ------------------------------------------------

            if element.get("type") == "node":

                place_lat = element.get(
                    "lat"
                )

                place_lon = element.get(
                    "lon"
                )

            else:

                center = element.get(
                    "center",
                    {},
                )

                place_lat = center.get(
                    "lat"
                )

                place_lon = center.get(
                    "lon"
                )

            if (
                place_lat is None
                or place_lon is None
            ):
                continue

            try:

                place_lat = float(
                    place_lat
                )

                place_lon = float(
                    place_lon
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            # ------------------------------------------------
            # Actual distance
            # ------------------------------------------------

            distance_m = calculate_distance(
                latitude,
                longitude,
                place_lat,
                place_lon,
            )

            if distance_m > radius_m:
                continue

            # ------------------------------------------------
            # Distance weight
            # ------------------------------------------------

            if distance_m <= 1000:

                distance_weight = 1.00

            elif distance_m <= 3000:

                distance_weight = 0.70

            elif distance_m <= 7000:

                distance_weight = 0.45

            else:

                distance_weight = 0.25

            # ------------------------------------------------
            # Category weight
            # ------------------------------------------------

            amenity = tags.get(
                "amenity"
            )

            shop = tags.get(
                "shop"
            )

            if amenity == "bank":

                banks += 1
                category_weight = 8

            elif amenity == "atm":

                atms += 1
                category_weight = 2

            elif shop == "supermarket":

                supermarkets += 1
                category_weight = 8

            elif amenity == "marketplace":

                marketplaces += 1
                category_weight = 5

            elif shop == "department_store":

                department_stores += 1
                category_weight = 10

            else:

                continue

            weighted_score += (
                category_weight
                * distance_weight
            )

        # ----------------------------------------------------
        # Total mapped economic locations
        # ----------------------------------------------------

        total_activity = (
            banks
            + atms
            + supermarkets
            + marketplaces
            + department_stores
        )

        # ----------------------------------------------------
        # Convert activity into 0-100 score
        #
        # This prevents the score from being fixed.
        # The score changes according to the actual
        # OSM activity around the selected location.
        # ----------------------------------------------------

        if weighted_score <= 0:

            proxy_score = 0.0

        else:

            # Smooth saturation:
            # more activity increases score,
            # but score cannot exceed 100.
            proxy_score = (
                100
                * (
                    1
                    - math.exp(
                        -weighted_score / 55
                    )
                )
            )

        proxy_score = max(
            0.0,
            min(
                proxy_score,
                100.0,
            ),
        )

        proxy_score = round(
            proxy_score,
            2,
        )

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        if proxy_score >= 70:

            level = "HIGH"

        elif proxy_score >= 40:

            level = "MODERATE"

        elif proxy_score >= 20:

            level = "LOW"

        else:

            level = "VERY LOW"

        # ----------------------------------------------------
        # Return
        # ----------------------------------------------------

        return {

            "success": True,

            # Main field
            "purchasing_power":
                proxy_score,

            # Backward-compatible field
            "purchasing_power_proxy":
                proxy_score,

            "purchasing_power_unit":
                "score / 100",

            "purchasing_power_level":
                level,

            "purchasing_power_proxy_based":
                True,

            "purchasing_power_data_source":
                "OpenStreetMap / Overpass",

            "purchasing_power_radius_km":
                round(
                    radius_m / 1000,
                    2,
                ),

            # ------------------------------------------------
            # Economic activity
            # ------------------------------------------------

            "economic_activity": {

                "banks":
                    banks,

                "atms":
                    atms,

                "supermarkets":
                    supermarkets,

                "marketplaces":
                    marketplaces,

                "department_stores":
                    department_stores,

                "total_activity":
                    total_activity,

                "weighted_activity":
                    round(
                        weighted_score,
                        2,
                    ),

            },

            # ------------------------------------------------
            # Useful aliases for frontend
            # ------------------------------------------------

            "local_business_count":
                total_activity,

            "purchasing_power_note":
                (
                    "This is a location-based proxy "
                    "using mapped economic and "
                    "commercial activity within "
                    "the selected radius. It is "
                    "not direct household income."
                ),

        }

    except httpx.TimeoutException:

        print(
            "Economic activity timeout"
        )

        return {

            "success": False,

            "purchasing_power":
                None,

            "purchasing_power_proxy":
                None,

            "message":
                "Economic activity service timed out.",

        }

    except httpx.HTTPStatusError as e:

        print(
            "Overpass HTTP error:",
            e.response.status_code,
        )

        return {

            "success": False,

            "purchasing_power":
                None,

            "purchasing_power_proxy":
                None,

            "message":
                "Economic activity service returned an error.",

        }

    except Exception as e:

        print(
            "Overpass error:",
            repr(e),
        )

        return {

            "success": False,

            "purchasing_power":
                None,

            "purchasing_power_proxy":
                None,

            "message":
                "Could not retrieve economic activity data.",

        }


# ============================================================
# COMPLETE LOCATION INSIGHTS
# ============================================================

async def get_location_insights(
    latitude: float,
    longitude: float,
):
    """
    Get population density and purchasing-power
    proxy for the selected location.
    """

    # --------------------------------------------------------
    # Run both APIs at the same time
    # --------------------------------------------------------

    population_task = (
        get_population_density(
            latitude,
            longitude,
        )
    )

    purchasing_task = (
        get_purchasing_power_proxy(
            latitude,
            longitude,
            radius_m=10000,
        )
    )

    population_result, purchasing_result = (
        await asyncio.gather(
            population_task,
            purchasing_task,
        )
    )

    # --------------------------------------------------------
    # Return combined result
    # --------------------------------------------------------

    return {

        "success":
            population_result.get(
                "success",
                False,
            )
            or purchasing_result.get(
                "success",
                False,
            ),

        # ====================================================
        # POPULATION
        # ====================================================

        "population_density":
            population_result.get(
                "population_density"
            ),

        "population_density_actual":
            population_result.get(
                "population_density_actual"
            ),

        "population_density_unit":
            population_result.get(
                "population_density_unit",
                "people/km²",
            ),

        "population_density_score":
            population_result.get(
                "population_density_score"
            ),

        "population_density_level":
            population_result.get(
                "population_density_level"
            ),

        "population_estimate":
            population_result.get(
                "population_estimate"
            ),

        "population_area_km2":
            population_result.get(
                "population_area_km2"
            ),

        "population_data_year":
            population_result.get(
                "population_data_year"
            ),

        "population_data_source":
            population_result.get(
                "population_data_source",
                "WorldPop",
            ),

        # ====================================================
        # PURCHASING POWER
        # ====================================================

        # Main frontend field
        "purchasing_power":
            purchasing_result.get(
                "purchasing_power"
            ),

        # Old field retained for compatibility
        "purchasing_power_proxy":
            purchasing_result.get(
                "purchasing_power_proxy"
            ),

        "purchasing_power_level":
            purchasing_result.get(
                "purchasing_power_level"
            ),

        "purchasing_power_unit":
            purchasing_result.get(
                "purchasing_power_unit",
                "score / 100",
            ),

        "purchasing_power_data_source":
            purchasing_result.get(
                "purchasing_power_data_source"
            ),

        "purchasing_power_radius_km":
            purchasing_result.get(
                "purchasing_power_radius_km"
            ),

        "purchasing_power_note":
            purchasing_result.get(
                "purchasing_power_note"
            ),

        # ====================================================
        # ECONOMIC ACTIVITY
        # ====================================================

        "economic_activity":
            purchasing_result.get(
                "economic_activity",
                {},
            ),

        "local_business_count":
            purchasing_result.get(
                "local_business_count",
                0,
            ),

    }