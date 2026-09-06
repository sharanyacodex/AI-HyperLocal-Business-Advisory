import httpx
import asyncio
import json
import math


# ============================================================
# APIs
# ============================================================

WORLDPOP_URL = "https://api.worldpop.org/v1/services/stats"

WORLD_BANK_URL = (
    "https://api.worldbank.org/v2/country/IND/indicator/NY.GDP.PCAP.PP.CD"
)

# OpenStreetMap / Overpass
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


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

        async with httpx.AsyncClient(
            timeout=30.0
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

            api_data = data.get("data", {})

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
        # Approximate area
        # ----------------------------------------------------

        area_km2 = 16.0

        density = population / area_km2

        # ----------------------------------------------------
        # Dashboard score: 0–100
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
    Get India's GDP per-capita PPP.

    IMPORTANT:
    This is only used as a national economic baseline.
    It is NOT local PIN-code income.
    """

    try:

        params = {
            "format": "json",
            "per_page": 10,
        }

        async with httpx.AsyncClient(
            timeout=20.0
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

        for record in records:

            value = record.get("value")

            year = record.get("date")

            if value is not None:

                return float(value), year

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

    This is used only as a LOCAL ECONOMIC ACTIVITY PROXY.
    It is not actual household income.
    """

    try:

        latitude = float(latitude)
        longitude = float(longitude)

        # ----------------------------------------------------
        # Search approximately 5 km around location
        # ----------------------------------------------------

        radius = 5000

        query = f"""
        [out:json][timeout:20];

        (
          node["shop"](around:{radius},{latitude},{longitude});
          way["shop"](around:{radius},{latitude},{longitude});

          node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
          way["amenity"="restaurant"](around:{radius},{latitude},{longitude});

          node["amenity"="cafe"](around:{radius},{latitude},{longitude});
          way["amenity"="cafe"](around:{radius},{latitude},{longitude});

          node["amenity"="bank"](around:{radius},{latitude},{longitude});
          way["amenity"="bank"](around:{radius},{latitude},{longitude});
        );

        out center;
        """

        async with httpx.AsyncClient(
            timeout=30.0
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

        if not isinstance(elements, list):

            elements = []

        return len(elements)

    except httpx.TimeoutException:

        return None

    except Exception as e:

        print(
            "Local business activity error:",
            e
        )

        return None


# ============================================================
# PURCHASING POWER
# ============================================================

async def get_purchasing_power(
    latitude: float,
    longitude: float,
):
    """
    Estimate a location-sensitive purchasing-power score.

    World Bank provides India's national GDP-per-capita PPP.
    Since it does not provide PIN-level purchasing power,
    nearby economic activity from OpenStreetMap is used
    as a local proxy.

    IMPORTANT:
    This is a proxy score, NOT exact household income.
    """

    try:

        latitude = float(latitude)
        longitude = float(longitude)

        # ----------------------------------------------------
        # Get national baseline and local activity together
        # ----------------------------------------------------

        india_task = get_india_gdp_ppp()

        local_activity_task = (
            get_local_business_activity(
                latitude,
                longitude,
            )
        )

        india_result, local_business_count = (
            await asyncio.gather(
                india_task,
                local_activity_task,
            )
        )

        india_gdp_ppp, india_year = india_result

        # ----------------------------------------------------
        # Base score
        #
        # This maps India's GDP PPP baseline into
        # a reasonable 0–100 dashboard score.
        #
        # It is deliberately capped.
        # ----------------------------------------------------

        if india_gdp_ppp is None:

            base_score = 50

        else:

            # Reference range for normalization.
            # This is a proxy normalization, not income data.
            base_score = (
                india_gdp_ppp / 30000
            ) * 100

            base_score = max(
                20,
                min(base_score, 80)
            )

        # ----------------------------------------------------
        # LOCAL ECONOMIC ACTIVITY ADJUSTMENT
        #
        # More nearby businesses/services can indicate
        # stronger commercial activity.
        #
        # This does NOT mean businesses = income.
        # It is only a local proxy.
        # ----------------------------------------------------

        if local_business_count is None:

            local_adjustment = 0

        else:

            if local_business_count <= 20:
                local_adjustment = -15

            elif local_business_count <= 50:
                local_adjustment = -5

            elif local_business_count <= 100:
                local_adjustment = 5

            elif local_business_count <= 200:
                local_adjustment = 10

            else:
                local_adjustment = 15

        purchasing_power = (
            base_score +
            local_adjustment
        )

        # ----------------------------------------------------
        # Keep score between 0 and 100
        # ----------------------------------------------------

        purchasing_power = max(
            0,
            min(
                purchasing_power,
                100
            )
        )

        purchasing_power = round(
            purchasing_power,
            2
        )

        # ----------------------------------------------------
        # Dashboard label
        # ----------------------------------------------------

        if purchasing_power >= 70:

            level = "HIGH"

        elif purchasing_power >= 40:

            level = "MODERATE"

        else:

            level = "LOW"

        # ----------------------------------------------------
        # Return
        # ----------------------------------------------------

        return {

            "success": True,

            "purchasing_power":
                purchasing_power,

            "purchasing_power_unit":
                "score / 100",

            "purchasing_power_level":
                level,

            "purchasing_power_proxy":
                True,

            "purchasing_power_data_source":
                "World Bank + OpenStreetMap local economic activity",

            "purchasing_power_year":
                india_year,

            "local_business_activity":
                local_business_count,

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

    population_task = get_population_density(
        latitude,
        longitude,
    )

    purchasing_task = get_purchasing_power(
        latitude,
        longitude,
    )

    population_result, purchasing_result = (
        await asyncio.gather(
            population_task,
            purchasing_task,
        )
    )

    return {

        "population":
            population_result,

        "purchasing_power":
            purchasing_result,

    }