import httpx


OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


# Normal business names → OpenStreetMap categories
BUSINESS_TAGS = {
    "grocery": ["supermarket", "convenience", "grocery"],
    "grocery shop": ["supermarket", "convenience", "grocery"],
    "supermarket": ["supermarket", "convenience"],
    "bakery": ["bakery"],
    "pharmacy": ["pharmacy"],
    "restaurant": ["restaurant", "fast_food"],
    "cafe": ["cafe"],
    "clothing": ["clothes"],
    "clothing shop": ["clothes"],
    "mobile shop": ["mobile_phone"],
    "electronics": ["electronics"],
    "hardware": ["hardware"],
}


async def find_nearby_competitors(
    latitude: float,
    longitude: float,
    business_type: str,
    radius: int = 5000
):
    business = business_type.lower().strip()

    tags = BUSINESS_TAGS.get(business, [business])

    tag_queries = []

    for tag in tags:
        tag_queries.append(
            f'nwr["shop"="{tag}"](around:{radius},{latitude},{longitude});'
        )

    query = f"""
    [out:json][timeout:60];
    (
        {" ".join(tag_queries)}
    );
    out center;
    """

    headers = {
        "User-Agent": "AI-HyperLocal-Business-Advisory/1.0"
    }

    errors = []

    for url in OVERPASS_URLS:

        try:
            async with httpx.AsyncClient(
                timeout=70.0,
                headers=headers
            ) as client:

                response = await client.post(
                    url,
                    data={"data": query}
                )

                response.raise_for_status()

                data = response.json()

            competitors = []
            seen = set()

            for element in data.get("elements", []):

                tags_data = element.get("tags", {})

                name = tags_data.get(
                    "name",
                    "Unnamed business"
                )

                # Get coordinates
                if element["type"] == "node":
                    lat = element.get("lat")
                    lon = element.get("lon")

                else:
                    center = element.get("center", {})
                    lat = center.get("lat")
                    lon = center.get("lon")

                # Avoid duplicate businesses
                key = (
                    name.lower(),
                    round(lat, 6) if lat else None,
                    round(lon, 6) if lon else None
                )

                if key in seen:
                    continue

                seen.add(key)

                competitors.append({
                    "name": name,
                    "latitude": lat,
                    "longitude": lon,
                    "category": tags_data.get("shop")
                })

            return {
                "success": True,
                "business_type": business_type,
                "search_radius_km": radius / 1000,
                "competitor_count": len(competitors),
                "competitors": competitors
            }

        except Exception as e:

            errors.append(
                f"{url} -> {type(e).__name__}: {str(e)}"
            )

    return {
        "success": False,
        "message": "Could not retrieve competitor data",
        "errors": errors
    }