import asyncio
import math
import httpx


# ============================================================
# FREE DATA SOURCES
# ============================================================

WORLDPOP_API_URL = "https://api.worldpop.org/v2"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2,
):
    """
    Calculate distance between two coordinates
    using the Haversine formula.

    Returns distance in meters.
    """

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

    # Protect against tiny floating-point errors.
    a = min(
        1.0,
        max(
            0.0,
            a
        )
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
# POPULATION DENSITY
# WORLDPOP
# ============================================================

async def get_population_density(
    latitude: float,
    longitude: float,
):
    """
    Estimate population density around the selected location.

    WorldPop provides population data globally.

    We use approximately a 1 km x 1 km area around
    the selected point.
    """

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
    # Create approximately 1 km x 1 km square
    # --------------------------------------------------------

    lat_offset = 0.0045

    lon_offset = (
        0.0045 /
        max(
            math.cos(
                math.radians(latitude)
            ),
            0.1
        )
    )

    south = latitude - lat_offset
    north = latitude + lat_offset
    west = longitude - lon_offset
    east = longitude + lon_offset

    polygon = {
        "type": "Polygon",
        "coordinates": [[

            [west, south],
            [east, south],
            [east, north],
            [west, north],
            [west, south],

        ]]
    }

    payload = {

        "geojson": polygon,

        # WorldPop data available through 2020
        "year": 2020,

        # 1 km resolution
        "resolution": "1km",

    }

    try:

        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:

            # ------------------------------------------------
            # Submit WorldPop task
            # ------------------------------------------------

            response = await client.post(
                f"{WORLDPOP_API_URL}/population",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            task_id = data.get(
                "task_id"
            )

            if not task_id:

                return {
                    "success": False,
                    "message":
                        "WorldPop did not return a task ID.",
                    "population_density": None,
                }

            # ------------------------------------------------
            # Poll task
            # ------------------------------------------------

            for _ in range(30):

                await asyncio.sleep(1)

                result_response = await client.get(
                    f"{WORLDPOP_API_URL}/tasks/{task_id}"
                )

                result_response.raise_for_status()

                result_data = (
                    result_response.json()
                )

                status = result_data.get(
                    "status"
                )

                if status == "success":

                    result = (
                        result_data.get(
                            "result",
                            {}
                        )
                    )

                    density = result.get(
                        "population_density"
                    )

                    total_population = result.get(
                        "total_population"
                    )

                    area_km2 = result.get(
                        "area_km2"
                    )

                    if density is None:

                        return {
                            "success": False,
                            "message":
                                "Population density unavailable.",
                            "population_density":
                                None,
                        }

                    return {

                        "success": True,

                        "population_density":
                            round(
                                float(density),
                                2
                            ),

                        "population_estimate":
                            round(
                                float(
                                    total_population
                                ),
                                0
                            )
                            if total_population is not None
                            else None,

                        "area_km2":
                            round(
                                float(area_km2),
                                2
                            )
                            if area_km2 is not None
                            else 1.0,

                        "population_data_year":
                            2020,

                        "population_data_source":
                            "WorldPop",

                    }

                if status == "failure":

                    return {
                        "success": False,
                        "message":
                            result_data.get(
                                "error",
                                "WorldPop task failed."
                            ),
                        "population_density":
                            None,
                    }

            return {
                "success": False,
                "message":
                    "WorldPop request timed out.",
                "population_density":
                    None,
            }

    except httpx.TimeoutException:

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
            e.response.status_code
        )

        return {
            "success": False,
            "message":
                "Population service returned an error.",
            "population_density":
                None,
        }

    except Exception as e:

        print(
            "WorldPop error:",
            e
        )

        return {
            "success": False,
            "message":
                "Could not retrieve population data.",
            "population_density":
                None,
        }


# ============================================================
# PURCHASING POWER PROXY
# OPENSTREETMAP / OVERPASS
# ============================================================

async def get_purchasing_power_proxy(
    latitude: float,
    longitude: float,
    radius_m: int = 10000,
):
    """
    Estimate local purchasing-power proxy from
    nearby economic/commercial activity.

    IMPORTANT:
    This is NOT actual household income.

    The search radius is up to 10 km.

    Businesses closer to the selected location
    have greater influence on the score.
    """

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError):

        return {
            "success": False,
            "purchasing_power_proxy":
                None,
            "message":
                "Invalid coordinates.",
        }

    # --------------------------------------------------------
    # Protect the function from invalid radius values
    # --------------------------------------------------------

    try:

        radius_m = int(radius_m)

    except (TypeError, ValueError):

        radius_m = 10000

    radius_m = max(
        1000,
        min(
            radius_m,
            10000
        )
    )

    # --------------------------------------------------------
    # OpenStreetMap / Overpass query
    # --------------------------------------------------------

    query = f"""
    [out:json][timeout:30];

    (
      node["amenity"="bank"]
        (around:{radius_m},{latitude},{longitude});

      way["amenity"="bank"]
        (around:{radius_m},{latitude},{longitude});

      node["amenity"="atm"]
        (around:{radius_m},{latitude},{longitude});

      way["amenity"="atm"]
        (around:{radius_m},{latitude},{longitude});

      node["shop"="supermarket"]
        (around:{radius_m},{latitude},{longitude});

      way["shop"="supermarket"]
        (around:{radius_m},{latitude},{longitude});

      node["amenity"="marketplace"]
        (around:{radius_m},{latitude},{longitude});

      way["amenity"="marketplace"]
        (around:{radius_m},{latitude},{longitude});

      node["shop"="department_store"]
        (around:{radius_m},{latitude},{longitude});

      way["shop"="department_store"]
        (around:{radius_m},{latitude},{longitude});
    );

    out center;
    """

    try:

        async with httpx.AsyncClient(
            timeout=40.0
        ) as client:

            response = await client.post(
                OVERPASS_URL,
                data=query,
            )

            response.raise_for_status()

            data = response.json()

        elements = data.get(
            "elements",
            []
        )

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        banks = 0
        atms = 0
        supermarkets = 0
        marketplaces = 0
        department_stores = 0

        # ----------------------------------------------------
        # Weighted economic activity
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
                {}
            )

            # ------------------------------------------------
            # Get coordinates
            # ------------------------------------------------

            if element.get("type") == "node":

                lat = element.get(
                    "lat"
                )

                lon = element.get(
                    "lon"
                )

            else:

                center = element.get(
                    "center",
                    {}
                )

                lat = center.get(
                    "lat"
                )

                lon = center.get(
                    "lon"
                )

            if lat is None or lon is None:

                continue

            try:

                lat = float(lat)
                lon = float(lon)

            except (
                TypeError,
                ValueError
            ):

                continue

            # ------------------------------------------------
            # Calculate actual distance
            # ------------------------------------------------

            distance_m = calculate_distance(
                latitude,
                longitude,
                lat,
                lon,
            )

            # ------------------------------------------------
            # Safety check
            # ------------------------------------------------

            if distance_m > radius_m:

                continue

            # ------------------------------------------------
            # Distance weighting
            #
            # 0 - 1 km   = 100%
            # 1 - 3 km   = 70%
            # 3 - 7 km   = 45%
            # 7 - 10 km  = 25%
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
            # Economic category weight
            # ------------------------------------------------

            if tags.get(
                "amenity"
            ) == "bank":

                banks += 1

                category_weight = 8

            elif tags.get(
                "amenity"
            ) == "atm":

                atms += 1

                category_weight = 2

            elif tags.get(
                "shop"
            ) == "supermarket":

                supermarkets += 1

                category_weight = 8

            elif tags.get(
                "amenity"
            ) == "marketplace":

                marketplaces += 1

                category_weight = 5

            elif tags.get(
                "shop"
            ) == "department_store":

                department_stores += 1

                category_weight = 10

            else:

                continue

            # ------------------------------------------------
            # Add distance-adjusted contribution
            # ------------------------------------------------

            weighted_score += (
                category_weight
                * distance_weight
            )

        # ----------------------------------------------------
        # Convert score to 0-100
        # ----------------------------------------------------

        proxy_score = min(
            100,
            max(
                0,
                weighted_score
            )
        )

        proxy_score = round(
            proxy_score,
            2
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
        # Return result
        # ----------------------------------------------------

        return {

            "success": True,

            "purchasing_power_proxy":
                proxy_score,

            "purchasing_power_level":
                level,

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

            },

            "purchasing_power_data_source":
                "OpenStreetMap / Overpass",

            "purchasing_power_radius_km":
                radius_m / 1000,

            "purchasing_power_note":
                "Proxy based on mapped local "
                "economic and commercial activity "
                "within up to 10 km. Businesses "
                "closer to the selected location "
                "receive greater weight. This is "
                "not a direct household income estimate.",

        }

    except httpx.TimeoutException:

        print(
            "Economic activity timeout"
        )

        return {

            "success": False,

            "purchasing_power_proxy":
                None,

            "message":
                "Economic activity service timed out.",

        }

    except httpx.HTTPStatusError as e:

        print(
            "Overpass HTTP error:",
            e.response.status_code
        )

        return {

            "success": False,

            "purchasing_power_proxy":
                None,

            "message":
                "Economic activity service returned an error.",

        }

    except Exception as e:

        print(
            "Overpass error:",
            e
        )

        return {

            "success": False,

            "purchasing_power_proxy":
                None,

            "message":
                "Could not retrieve economic activity data.",

        }


# ============================================================
# COMBINED LOCATION INSIGHTS
# ============================================================

async def get_location_insights(
    latitude: float,
    longitude: float,
):
    """
    Get population density and purchasing-power proxy
    for the selected location.

    Purchasing-power analysis considers economic
    activity up to 10 km away.
    """

    # --------------------------------------------------------
    # Run both services concurrently
    # --------------------------------------------------------

    population_task = (
        get_population_density(
            latitude,
            longitude
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
                "success"
            )
            or purchasing_result.get(
                "success"
            ),

        # ====================================================
        # POPULATION
        # ====================================================

        "population_density":
            population_result.get(
                "population_density"
            ),

        "population_estimate":
            population_result.get(
                "population_estimate"
            ),

        "population_area_km2":
            population_result.get(
                "area_km2"
            ),

        "population_data_year":
            population_result.get(
                "population_data_year"
            ),

        "population_data_source":
            population_result.get(
                "population_data_source",
                "WorldPop"
            ),

        # ====================================================
        # PURCHASING POWER
        # ====================================================

        "purchasing_power_proxy":
            purchasing_result.get(
                "purchasing_power_proxy"
            ),

        "purchasing_power_level":
            purchasing_result.get(
                "purchasing_power_level"
            ),

        "economic_activity":
            purchasing_result.get(
                "economic_activity",
                {}
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

    }