import httpx


async def calculate_risk_safety(
    latitude: float,
    longitude: float
):
    """
    Calculate a location safety score using
    real weather data.

    Score:
    100 = safer current conditions
    0   = very risky current conditions
    """

    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            "&current=temperature_2m,wind_speed_10m,"
            "precipitation,rain,weather_code"
        )

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)

        response.raise_for_status()

        data = response.json()
        current = data.get("current", {})

        temperature = current.get("temperature_2m", 0)
        wind_speed = current.get("wind_speed_10m", 0)
        precipitation = current.get("precipitation", 0)
        weather_code = current.get("weather_code", 0)

        # Start with maximum safety
        safety_score = 100

        # Heavy wind reduces safety
        if wind_speed >= 50:
            safety_score -= 40
        elif wind_speed >= 30:
            safety_score -= 25
        elif wind_speed >= 20:
            safety_score -= 10

        # Heavy precipitation reduces safety
        if precipitation >= 20:
            safety_score -= 30
        elif precipitation >= 10:
            safety_score -= 20
        elif precipitation >= 5:
            safety_score -= 10

        # Extreme temperature reduces safety
        if temperature >= 45 or temperature <= 5:
            safety_score -= 20
        elif temperature >= 40 or temperature <= 10:
            safety_score -= 10

        # Severe weather codes
        if weather_code in [95, 96, 99]:
            safety_score -= 30

        safety_score = max(
            0,
            min(100, safety_score)
        )

        return {
            "success": True,
            "risk_safety": round(safety_score, 2),
            "source": "Open-Meteo",
            "current_weather": {
                "temperature_c": temperature,
                "wind_speed_kmh": wind_speed,
                "precipitation_mm": precipitation,
                "weather_code": weather_code
            }
        }

    except Exception as e:
        return {
            "success": False,
            "risk_safety": None,
            "source": "Open-Meteo",
            "message": str(e)
        }