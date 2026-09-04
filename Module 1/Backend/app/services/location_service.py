import httpx


async def geocode_location(location: str):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "AI-HyperLocal-Business-Advisory/1.0"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            url,
            params=params,
            headers=headers
        )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    return {
        "display_name": results[0]["display_name"],
        "latitude": float(results[0]["lat"]),
        "longitude": float(results[0]["lon"])
    }