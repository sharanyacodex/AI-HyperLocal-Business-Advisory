import httpx


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


# ============================================================
# WEATHER CODE DESCRIPTION
# ============================================================

def get_weather_description(weather_code: int) -> str:

    weather_codes = {
        0: "Clear",
        1: "Mostly Clear",
        2: "Partly Cloudy",
        3: "Cloudy",

        45: "Foggy",
        48: "Foggy",

        51: "Light Drizzle",
        53: "Drizzle",
        55: "Heavy Drizzle",

        56: "Light Freezing Drizzle",
        57: "Heavy Freezing Drizzle",

        61: "Light Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",

        66: "Light Freezing Rain",
        67: "Heavy Freezing Rain",

        71: "Light Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",

        77: "Snow",

        80: "Light Rain Showers",
        81: "Rain Showers",
        82: "Heavy Rain Showers",

        85: "Light Snow Showers",
        86: "Heavy Snow Showers",

        95: "Thunderstorm",
        96: "Thunderstorm with Hail",
        99: "Severe Thunderstorm with Hail",
    }

    return weather_codes.get(
        weather_code,
        "Unknown Weather"
    )


# ============================================================
# WEATHER RISK SCORE
# ============================================================

def calculate_weather_risk(
    temperature_c: float,
    wind_speed_kmh: float,
    precipitation_mm: float,
    weather_code: int,
    apparent_temperature_c: float | None = None,
) -> int:

    # --------------------------------------------------------
    # START WITH MAXIMUM SAFETY
    # --------------------------------------------------------

    score = 100

    # Use apparent temperature if available because it can
    # represent heat/cold stress better than air temperature.
    effective_temperature = (
        apparent_temperature_c
        if apparent_temperature_c is not None
        else temperature_c
    )

    # ========================================================
    # 1. TEMPERATURE RISK
    # ========================================================

    # Comfortable / normal range
    if 10 <= effective_temperature <= 30:
        score -= 0

    # Mild heat
    elif 30 < effective_temperature <= 34:
        score -= 4

    # Moderate heat
    elif 34 < effective_temperature <= 37:
        score -= 8

    # High heat
    elif 37 < effective_temperature <= 40:
        score -= 15

    # Very high heat
    elif 40 < effective_temperature <= 45:
        score -= 25

    # Extreme heat
    elif effective_temperature > 45:
        score -= 35

    # Cold conditions
    elif 5 <= effective_temperature < 10:
        score -= 4

    elif 0 <= effective_temperature < 5:
        score -= 10

    elif -5 <= effective_temperature < 0:
        score -= 18

    else:
        # Below -5°C
        score -= 30

    # ========================================================
    # 2. WIND RISK
    # ========================================================

    if wind_speed_kmh < 20:
        score -= 0

    elif wind_speed_kmh < 30:
        score -= 3

    elif wind_speed_kmh < 40:
        score -= 8

    elif wind_speed_kmh < 50:
        score -= 15

    elif wind_speed_kmh < 60:
        score -= 22

    else:
        # 60+ km/h
        score -= 30

    # ========================================================
    # 3. PRECIPITATION RISK
    # ========================================================

    if precipitation_mm <= 0:
        score -= 0

    elif precipitation_mm < 2:
        score -= 2

    elif precipitation_mm < 5:
        score -= 4

    elif precipitation_mm < 10:
        score -= 8

    elif precipitation_mm < 20:
        score -= 15

    elif precipitation_mm < 40:
        score -= 22

    else:
        # Heavy rainfall
        score -= 30

    # ========================================================
    # 4. WEATHER CONDITION RISK
    # ========================================================

    # --------------------------------------------------------
    # CLEAR / CLOUDY
    # --------------------------------------------------------

    if weather_code in [0, 1, 2, 3]:
        # Normal weather conditions.
        score -= 0

    # --------------------------------------------------------
    # FOG
    # --------------------------------------------------------

    elif weather_code in [45, 48]:
        score -= 7

    # --------------------------------------------------------
    # DRIZZLE
    # --------------------------------------------------------

    elif weather_code in [51, 53, 55]:
        score -= 5

    # --------------------------------------------------------
    # FREEZING DRIZZLE
    # --------------------------------------------------------

    elif weather_code in [56, 57]:
        score -= 10

    # --------------------------------------------------------
    # RAIN
    # --------------------------------------------------------

    elif weather_code == 61:
        score -= 5

    elif weather_code == 63:
        score -= 10

    elif weather_code == 65:
        score -= 18

    # --------------------------------------------------------
    # FREEZING RAIN
    # --------------------------------------------------------

    elif weather_code in [66, 67]:
        score -= 18

    # --------------------------------------------------------
    # SNOW
    # --------------------------------------------------------

    elif weather_code == 71:
        score -= 8

    elif weather_code == 73:
        score -= 14

    elif weather_code == 75:
        score -= 22

    elif weather_code == 77:
        score -= 12

    # --------------------------------------------------------
    # RAIN SHOWERS
    # --------------------------------------------------------

    elif weather_code == 80:
        score -= 6

    elif weather_code == 81:
        score -= 12

    elif weather_code == 82:
        score -= 22

    # --------------------------------------------------------
    # SNOW SHOWERS
    # --------------------------------------------------------

    elif weather_code == 85:
        score -= 12

    elif weather_code == 86:
        score -= 22

    # --------------------------------------------------------
    # THUNDERSTORM
    # --------------------------------------------------------

    elif weather_code == 95:
        score -= 25

    elif weather_code == 96:
        score -= 30

    elif weather_code == 99:
        score -= 35

    # ========================================================
    # 5. FINAL LIMIT
    # ========================================================

    score = max(
        0,
        min(score, 100)
    )

    return int(round(score))


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(
    risk_safety: int
) -> str:

    if risk_safety >= 85:
        return "LOW RISK"

    elif risk_safety >= 65:
        return "MODERATE RISK"

    elif risk_safety >= 40:
        return "HIGH RISK"

    else:
        return "VERY HIGH RISK"


# ============================================================
# RISK MESSAGE
# ============================================================

def get_risk_message(
    risk_safety: int
) -> str:

    if risk_safety >= 85:

        return (
            "Weather conditions are generally favorable "
            "for normal business operations."
        )

    elif risk_safety >= 65:

        return (
            "Weather conditions are mostly manageable, "
            "but some precautions may be required."
        )

    elif risk_safety >= 40:

        return (
            "Weather conditions may affect business "
            "operations. Additional precautions are recommended."
        )

    else:

        return (
            "Severe weather conditions may significantly "
            "affect business operations. Extra precautions are advised."
        )


# ============================================================
# OPEN-METEO REQUEST
# ============================================================

async def get_current_weather(
    latitude: float,
    longitude: float,
):

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "wind_speed_10m,"
            "precipitation,"
            "weather_code"
        ),

        "timezone": "auto",

    }

    try:

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            response = await client.get(
                OPEN_METEO_URL,
                params=params
            )

            response.raise_for_status()

            data = response.json()

            current = data.get(
                "current",
                {}
            )

            temperature = float(
                current.get(
                    "temperature_2m",
                    0
                )
            )

            apparent_temperature = float(
                current.get(
                    "apparent_temperature",
                    temperature
                )
            )

            humidity = float(
                current.get(
                    "relative_humidity_2m",
                    0
                )
            )

            wind_speed = float(
                current.get(
                    "wind_speed_10m",
                    0
                )
            )

            precipitation = float(
                current.get(
                    "precipitation",
                    0
                )
            )

            weather_code = int(
                current.get(
                    "weather_code",
                    0
                )
            )

            return {

                "success": True,

                "temperature_c": temperature,

                "apparent_temperature_c":
                    apparent_temperature,

                "humidity_percent":
                    humidity,

                "wind_speed_kmh":
                    wind_speed,

                "precipitation_mm":
                    precipitation,

                "weather_code":
                    weather_code,

                "weather_description":
                    get_weather_description(
                        weather_code
                    ),

            }

    except httpx.TimeoutException:

        print(
            "Open-Meteo request timed out."
        )

        return {

            "success": False,

            "message":
                "Weather service timed out."

        }

    except httpx.HTTPStatusError as e:

        print(
            "Open-Meteo HTTP error:",
            e.response.status_code
        )

        return {

            "success": False,

            "message":
                "Weather service returned an error."

        }

    except Exception as e:

        print(
            "Open-Meteo error:",
            e
        )

        return {

            "success": False,

            "message":
                "Could not retrieve weather data."

        }


# ============================================================
# MAIN RISK / SAFETY FUNCTION
# ============================================================

async def calculate_risk_safety(
    latitude: float,
    longitude: float,
):

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

            "message":
                "Invalid latitude or longitude.",

            "risk_safety": None,

            "risk_level": None,

            "risk_message": None,

            "risk_data_source":
                "Open-Meteo",

            "current_weather": None,

        }

    # --------------------------------------------------------
    # VALIDATE COORDINATE RANGE
    # --------------------------------------------------------

    if not -90 <= latitude <= 90:

        return {

            "success": False,

            "message":
                "Latitude must be between -90 and 90.",

            "risk_safety": None,

            "risk_level": None,

            "risk_message": None,

            "risk_data_source":
                "Open-Meteo",

            "current_weather": None,

        }

    if not -180 <= longitude <= 180:

        return {

            "success": False,

            "message":
                "Longitude must be between -180 and 180.",

            "risk_safety": None,

            "risk_level": None,

            "risk_message": None,

            "risk_data_source":
                "Open-Meteo",

            "current_weather": None,

        }

    # --------------------------------------------------------
    # GET WEATHER
    # --------------------------------------------------------

    weather = await get_current_weather(
        latitude,
        longitude
    )

    if not weather.get("success"):

        return {

            "success": False,

            "message": weather.get(
                "message",
                "Could not retrieve weather."
            ),

            "risk_safety": None,

            "risk_level": None,

            "risk_message": None,

            "risk_data_source":
                "Open-Meteo",

            "current_weather": None,

        }

    # --------------------------------------------------------
    # CALCULATE RISK SCORE
    # --------------------------------------------------------

    risk_safety = calculate_weather_risk(

        temperature_c=
            weather["temperature_c"],

        wind_speed_kmh=
            weather["wind_speed_kmh"],

        precipitation_mm=
            weather["precipitation_mm"],

        weather_code=
            weather["weather_code"],

        apparent_temperature_c=
            weather.get(
                "apparent_temperature_c"
            ),

    )

    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    risk_level = get_risk_level(
        risk_safety
    )

    # --------------------------------------------------------
    # RISK MESSAGE
    # --------------------------------------------------------

    risk_message = get_risk_message(
        risk_safety
    )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "success": True,

        "risk_safety": risk_safety,

        "risk_level": risk_level,

        "risk_message": risk_message,

        "risk_data_source":
            "Open-Meteo",

        "current_weather": {

            "temperature_c":
                weather["temperature_c"],

            "apparent_temperature_c":
                weather.get(
                    "apparent_temperature_c"
                ),

            "humidity_percent":
                weather.get(
                    "humidity_percent"
                ),

            "wind_speed_kmh":
                weather["wind_speed_kmh"],

            "precipitation_mm":
                weather["precipitation_mm"],

            "weather_code":
                weather["weather_code"],

            "weather_description":
                weather["weather_description"],

        },

    }