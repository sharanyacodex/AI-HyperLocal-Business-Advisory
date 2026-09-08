import httpx
import asyncio
import json


# ============================================================
# APIs
# ============================================================

WORLDPOP_URL = "https://api.worldpop.org/v1/services/stats"

WORLD_BANK_URL = (
    "https://api.worldbank.org/v2/country/IND/indicator/"
    "NY.GDP.PCAP.PP.CD"
)

# Multiple Overpass servers
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


# ============================================================
# COMMON HEADERS
# ============================================================

HEADERS = {
    "User-Agent": (
        "AI-Rural-Business-Advisory/1.0 "
        "(educational-project)"
    ),
    "Accept": "application/json",
}


# ============================================================
# POPULATION DENSITY
# ============================================================

async def get_population_density(
    latitude: float,
    longitude: float,
):
    """
    Estimate population around the selected location.

    WorldPop provides gridded population datasets.
    A small area around the selected coordinates is used.
    """

    try:

        latitude = float(latitude)
        longitude = float(longitude)

        # ----------------------------------------------------
        # Approximately 2 km x 2 km around location
        # ----------------------------------------------------

        lat_delta = 0.018
        lon_delta = 0.018

        min_lat = latitude - lat_delta
        max_lat = latitude + lat_delta

        min_lon = longitude - lon_delta
        max_lon = longitude + lon_delta

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [min_lon, min_lat],
                                [max_lon, min_lat],
                                [max_lon, max_lat],
                                [min_lon, max_lat],
                                [min_lon, min_lat],
                            ]
                        ],
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

        timeout = httpx.Timeout(
            connect=5.0,
            read=30.0,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:

            response = await client.get(
                WORLDPOP_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        # ----------------------------------------------------
        # Extract population
        # ----------------------------------------------------

        population = None

        if isinstance(data, dict):

            api_data = data.get(
                "data",
                {}
            )

            if isinstance(api_data, dict):

                population = api_data.get(
                    "total_population"
                )

        if population is None:

            return {
                "success": False,
                "message": "Population data unavailable.",
            }

        population = float(population)

        # ----------------------------------------------------
        # Area
        # ----------------------------------------------------

        area_km2 = 16.0

        density = population / area_km2

        # ----------------------------------------------------
        # Convert actual density to score
        # ----------------------------------------------------

        if density < 500:

            density_score = 20
            density_level = "LOW"

        elif density < 1500:

            density_score = 40
            density_level = "MODERATE"

        elif density < 3000:

            density_score = 70
            density_level = "HIGH"

        else:

            density_score = 90
            density_level = "VERY HIGH"

        return {

            "success": True,

            "population_estimate":
                round(population, 0),

            "population_density":
                round(density, 2),

            "population_density_actual":
                round(density, 2),

            "population_density_unit":
                "people/km²",

            "population_density_score":
                density_score,

            "population_density_level":
                density_level,

            "population_data_source":
                "WorldPop",

        }

    except httpx.TimeoutException:

        return {

            "success": False,

            "message":
                "Population service timed out.",

        }

    except Exception as e:

        print(
            "Population API error:",
            e
        )

        return {

            "success": False,

            "message":
                "Could not retrieve population data.",

        }


# ============================================================
# WORLD BANK BASELINE
# ============================================================

async def get_india_gdp_ppp():

    """
    Get India's GDP-per-capita PPP.

    This is used only as a national economic baseline.
    It is NOT local PIN-code income.
    """

    try:

        params = {
            "format": "json",
            "per_page": 20,
        }

        timeout = httpx.Timeout(
            connect=5.0,
            read=20.0,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:

            response = await client.get(
                WORLD_BANK_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        if (
            not isinstance(data, list)
            or len(data) < 2
        ):

            return None, None

        records = data[1]

        if not isinstance(records, list):

            return None, None

        # ----------------------------------------------------
        # Find latest available value
        # ----------------------------------------------------

        for record in records:

            if not isinstance(record, dict):
                continue

            value = record.get("value")
            year = record.get("date")

            if value is not None:

                try:

                    return (
                        float(value),
                        year
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

        return None, None

    except Exception as e:

        print(
            "World Bank API error:",
            e
        )

        return None, None


# ============================================================
# LOCAL BUSINESS ACTIVITY
# ============================================================

async def get_local_business_activity(
    latitude: float,
    longitude: float,
):
    """
    Estimate local economic activity using nearby
    OpenStreetMap businesses/amenities.

    This is a LOCAL ECONOMIC ACTIVITY PROXY.
    It is not actual household income.
    """

    try:

        latitude = float(latitude)
        longitude = float(longitude)

        radius = 5000

        query = f"""
        [out:json][timeout:30];

        (
            node["shop"](around:{radius},{latitude},{longitude});
            way["shop"](around:{radius},{latitude},{longitude});
            relation["shop"](around:{radius},{latitude},{longitude});

            node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
            way["amenity"="restaurant"](around:{radius},{latitude},{longitude});
            relation["amenity"="restaurant"](around:{radius},{latitude},{longitude});

            node["amenity"="cafe"](around:{radius},{latitude},{longitude});
            way["amenity"="cafe"](around:{radius},{latitude},{longitude});
            relation["amenity"="cafe"](around:{radius},{latitude},{longitude});

            node["amenity"="bank"](around:{radius},{latitude},{longitude});
            way["amenity"="bank"](around:{radius},{latitude},{longitude});
            relation["amenity"="bank"](around:{radius},{latitude},{longitude});
        );

        out center;
        """

        timeout = httpx.Timeout(
            connect=8.0,
            read=35.0,
            write=15.0,
            pool=8.0,
        )

        # ----------------------------------------------------
        # Try multiple Overpass servers
        # ----------------------------------------------------

        for overpass_url in OVERPASS_URLS:

            try:

                print(
                    "Purchasing power - trying Overpass:",
                    overpass_url
                )

                async with httpx.AsyncClient(
                    timeout=timeout,
                    follow_redirects=True,
                    headers=HEADERS,
                ) as client:

                    response = await client.post(
                        overpass_url,
                        data=query,
                        headers={
                            **HEADERS,
                            "Content-Type":
                                "application/x-www-form-urlencoded",
                        },
                    )

                    response.raise_for_status()

                    data = response.json()

                elements = data.get(
                    "elements",
                    []
                )

                if not isinstance(elements, list):

                    elements = []

                # ------------------------------------------------
                # Remove duplicate OSM objects
                # ------------------------------------------------

                unique_ids = set()

                for element in elements:

                    element_id = (
                        element.get("type"),
                        element.get("id")
                    )

                    unique_ids.add(element_id)

                count = len(unique_ids)

                print(
                    "Local economic activity:",
                    count
                )

                return count

            except Exception as e:

                print(
                    "Overpass failed:",
                    overpass_url,
                    str(e)
                )

                continue

        return None

    except Exception as e:

        print(
            "Local business activity error:",
            e
        )

        return None


# ============================================================
# PURCHASING POWER SCORE
# ============================================================

def calculate_purchasing_power_score(
    india_gdp_ppp,
    local_business_count,
):
    """
    Calculate a location-sensitive purchasing-power proxy.

    IMPORTANT:
    This is NOT actual household income.

    World Bank:
        National PPP baseline.

    OpenStreetMap:
        Local economic activity proxy.
    """

    # --------------------------------------------------------
    # BASE SCORE
    # --------------------------------------------------------

    if india_gdp_ppp is None:

        base_score = 50.0

    else:

        try:

            india_gdp_ppp = float(
                india_gdp_ppp
            )

            # Normalize national PPP baseline.
            #
            # 30,000 PPP = 100 reference score.
            #

            base_score = (
                india_gdp_ppp / 30000.0
            ) * 100.0

            base_score = max(
                20.0,
                min(
                    base_score,
                    80.0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            base_score = 50.0

    # --------------------------------------------------------
    # LOCAL ACTIVITY ADJUSTMENT
    # --------------------------------------------------------

    if local_business_count is None:

        local_adjustment = 0.0

    else:

        count = int(
            local_business_count
        )

        if count <= 10:

            local_adjustment = -5.0

        elif count <= 30:

            local_adjustment = 0.0

        elif count <= 60:

            local_adjustment = 5.0

        elif count <= 100:

            local_adjustment = 10.0

        elif count <= 200:

            local_adjustment = 15.0

        else:

            local_adjustment = 20.0

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    score = (
        base_score
        +
        local_adjustment
    )

    score = max(
        0.0,
        min(
            score,
            100.0
        )
    )

    return round(
        score,
        2
    )


# ============================================================
# PURCHASING POWER LEVEL
# ============================================================

def get_purchasing_power_level(
    score: float,
):

    if score >= 70:

        return "HIGH"

    elif score >= 40:

        return "MODERATE"

    else:

        return "LOW"


# ============================================================
# PURCHASING POWER
# ============================================================

async def get_purchasing_power(
    latitude: float,
    longitude: float,
):
    """
    Estimate location-sensitive purchasing power.

    World Bank:
        National PPP baseline.

    OpenStreetMap:
        Local economic activity proxy.

    This is a proxy score and not actual household income.
    """

    try:

        latitude = float(latitude)
        longitude = float(longitude)

        # ----------------------------------------------------
        # Run both APIs simultaneously
        # ----------------------------------------------------

        india_task = get_india_gdp_ppp()

        local_activity_task = (
            get_local_business_activity(
                latitude,
                longitude,
            )
        )

        (
            india_result,
            local_business_count,
        ) = await asyncio.gather(
            india_task,
            local_activity_task,
        )

        india_gdp_ppp, india_year = (
            india_result
        )

        # ----------------------------------------------------
        # Calculate score
        # ----------------------------------------------------

        purchasing_power = (
            calculate_purchasing_power_score(
                india_gdp_ppp,
                local_business_count,
            )
        )

        level = (
            get_purchasing_power_level(
                purchasing_power
            )
        )

        print(
            "----------------------------------------"
        )

        print(
            "PURCHASING POWER"
        )

        print(
            "India GDP PPP:",
            india_gdp_ppp
        )

        print(
            "World Bank year:",
            india_year
        )

        print(
            "Local businesses:",
            local_business_count
        )

        print(
            "Purchasing power score:",
            purchasing_power
        )

        print(
            "Purchasing power level:",
            level
        )

        print(
            "----------------------------------------"
        )

        return {

            "success": True,

            "purchasing_power":
                purchasing_power,

            "purchasing_power_unit":
                "score / 100",

            "purchasing_power_level":
                level,

            # Keep this TRUE because the value
            # is a proxy rather than actual income.

            "purchasing_power_proxy":
                True,

            "purchasing_power_data_source":
                (
                    "World Bank + "
                    "OpenStreetMap local economic activity"
                ),

            "purchasing_power_year":
                india_year,

            "local_business_activity":
                local_business_count,

            "india_gdp_ppp":
                india_gdp_ppp,

        }

    except httpx.TimeoutException:

        return {

            "success": False,

            "message":
                "Purchasing power service timed out.",

        }

    except Exception as e:

        print(
            "Purchasing power service error:",
            e
        )

        return {

            "success": False,

            "message":
                "Could not retrieve purchasing power data.",

        }


# ============================================================
# COMPLETE DEMOGRAPHIC ANALYSIS
# ============================================================

async def get_demographic_analysis(
    latitude: float,
    longitude: float,
):

    # --------------------------------------------------------
    # Run population and purchasing power together
    # --------------------------------------------------------

    population_task = (
        get_population_density(
            latitude,
            longitude,
        )
    )

    purchasing_task = (
        get_purchasing_power(
            latitude,
            longitude,
        )
    )

    (
        population_result,
        purchasing_result,
    ) = await asyncio.gather(
        population_task,
        purchasing_task,
    )

    return {

        "population":
            population_result,

        "purchasing_power":
            purchasing_result,

    }