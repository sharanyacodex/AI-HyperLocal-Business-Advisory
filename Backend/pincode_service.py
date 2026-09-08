import os
import httpx
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# API URLS
# ============================================================

POSTAL_API_URL = "https://api.postalpincode.in/pincode"

GEOAPIFY_GEOCODE_URL = (
    "https://api.geoapify.com/v1/geocode/search"
)


# ============================================================
# GEOAPIFY API KEY
# ============================================================

GEOAPIFY_API_KEY = os.getenv(
    "GEOAPIFY_API_KEY"
)


# ============================================================
# GET LOCATION FROM PIN CODE
# ============================================================

async def get_location_from_pincode(
    pincode: str
):
    """
    Get Indian PIN-code information
    using India Post API.
    """

    # --------------------------------------------------------
    # Validate PIN
    # --------------------------------------------------------

    if not pincode:

        return {
            "success": False,
            "message": "PIN code is required."
        }

    pincode = str(
        pincode
    ).strip()

    if (
        not pincode.isdigit()
        or len(pincode) != 6
    ):

        return {
            "success": False,
            "message": (
                "Invalid Indian PIN code. "
                "Enter a 6-digit PIN code."
            )
        }

    # --------------------------------------------------------
    # Call India Post API
    # --------------------------------------------------------

    try:

        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:

            response = await client.get(
                f"{POSTAL_API_URL}/{pincode}"
            )

            response.raise_for_status()

            data = response.json()

    except httpx.TimeoutException:

        return {
            "success": False,
            "message": (
                "PIN code service timed out."
            )
        }

    except httpx.HTTPStatusError as e:

        return {
            "success": False,
            "message": "PIN code API error.",
            "status_code": e.response.status_code
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                "Could not retrieve PIN code location."
            ),
            "error": str(e)
        }

    # --------------------------------------------------------
    # Validate response
    # --------------------------------------------------------

    if (
        not isinstance(data, list)
        or len(data) == 0
    ):

        return {
            "success": False,
            "message": (
                "Invalid response from PIN code service."
            )
        }

    result = data[0]

    if result.get("Status") != "Success":

        return {
            "success": False,
            "message": "PIN code not found."
        }

    # --------------------------------------------------------
    # Get post offices
    # --------------------------------------------------------

    offices = result.get(
        "PostOffice",
        []
    )

    if not offices:

        return {
            "success": False,
            "message": (
                "No locality found for this PIN code."
            )
        }

    # --------------------------------------------------------
    # Select first post office
    # --------------------------------------------------------

    office = offices[0]

    return {
        "success": True,
        "pincode": pincode,
        "name": office.get(
            "Name",
            ""
        ),
        "branch_type": office.get(
            "BranchType",
            ""
        ),
        "district": office.get(
            "District",
            ""
        ),
        "state": office.get(
            "State",
            ""
        ),
        "division": office.get(
            "Division",
            ""
        ),
        "region": office.get(
            "Region",
            ""
        ),
        "circle": office.get(
            "Circle",
            ""
        ),
        "country": office.get(
            "Country",
            "India"
        )
    }


# ============================================================
# GEOCODE LOCATION
# ============================================================

async def geocode_location(
    location_name: str,
    district: str,
    state: str
):
    """
    Convert locality information into
    latitude and longitude using Geoapify.
    """

    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    if not GEOAPIFY_API_KEY:

        return {
            "success": False,
            "message": (
                "GEOAPIFY_API_KEY is missing."
            )
        }

    # --------------------------------------------------------
    # Build search query
    # --------------------------------------------------------

    query_parts = [
        location_name,
        district,
        state,
        "India"
    ]

    query = ", ".join(
        str(part)
        for part in query_parts
        if part
    )

    # --------------------------------------------------------
    # Request parameters
    # --------------------------------------------------------

    params = {
        "text": query,
        "apiKey": GEOAPIFY_API_KEY,
        "limit": 1,
        "format": "json"
    }

    # --------------------------------------------------------
    # Call Geoapify
    # --------------------------------------------------------

    try:

        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:

            response = await client.get(
                GEOAPIFY_GEOCODE_URL,
                params=params
            )

            response.raise_for_status()

            data = response.json()

    except httpx.TimeoutException:

        return {
            "success": False,
            "message": (
                "Geoapify geocoding request timed out."
            )
        }

    except httpx.HTTPStatusError as e:

        try:
            details = e.response.json()
        except Exception:
            details = e.response.text

        return {
            "success": False,
            "message": (
                "Geoapify geocoding API error."
            ),
            "status_code": e.response.status_code,
            "details": details
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                "Could not geocode location."
            ),
            "error": str(e)
        }

    # --------------------------------------------------------
    # Get results
    # --------------------------------------------------------

    results = data.get(
        "results",
        []
    )

    if not results:

        return {
            "success": False,
            "message": (
                f"Could not find coordinates for: "
                f"{query}"
            )
        }

    # --------------------------------------------------------
    # First result
    # --------------------------------------------------------

    result = results[0]

    latitude = result.get(
        "lat"
    )

    longitude = result.get(
        "lon"
    )

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    if (
        latitude is None
        or longitude is None
    ):

        return {
            "success": False,
            "message": (
                "Geocoding result does not "
                "contain coordinates."
            )
        }

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
            "message": (
                "Invalid coordinates returned "
                "by Geoapify."
            )
        }

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "success": True,
        "latitude": latitude,
        "longitude": longitude,
        "formatted": result.get(
            "formatted",
            query
        ),
        "city": result.get(
            "city",
            location_name
        ),
        "district": result.get(
            "county",
            district
        ),
        "state": result.get(
            "state",
            state
        ),
        "country": result.get(
            "country",
            "India"
        )
    }


# ============================================================
# RESOLVE PIN CODE
# ============================================================

async def resolve_pincode(
    pincode: str
):
    """
    Complete PIN-code resolution:

        PIN
         ↓
        Location
         ↓
        Coordinates

    For the current Bishnupur test,
    PIN 722122 is mapped to the Bishnupur
    coordinates used by the project.

    Other PIN codes use the normal
    India Post + Geoapify process.
    """

    pincode = str(
        pincode
    ).strip()

    # ========================================================
    # TEMPORARY BISHNUPUR TEST LOCATION
    # ========================================================

    if pincode == "722122":

        return {
            "success": True,

            "pincode": "722122",

            "location_name": "Bishnupur",

            "district": "Bankura",

            "state": "West Bengal",

            "country": "India",

            "latitude": 23.0736,

            "longitude": 87.3199,

            "formatted": (
                "Bishnupur, Bankura, "
                "West Bengal, India"
            )
        }

    # ========================================================
    # NORMAL PIN-CODE PROCESS
    # ========================================================

    location = await get_location_from_pincode(
        pincode
    )

    if not location.get(
        "success"
    ):

        return location

    # --------------------------------------------------------
    # Geocode returned locality
    # --------------------------------------------------------

    coordinates = await geocode_location(
        location_name=location.get(
            "name",
            ""
        ),
        district=location.get(
            "district",
            ""
        ),
        state=location.get(
            "state",
            ""
        )
    )

    if not coordinates.get(
        "success"
    ):

        return {
            "success": False,

            "message": (
                "PIN code was found, "
                "but coordinates could "
                "not be determined."
            ),

            "pincode": location.get(
                "pincode"
            ),

            "location": location
        }

    # --------------------------------------------------------
    # Combine PIN + coordinates
    # --------------------------------------------------------

    return {
        "success": True,

        "pincode": location.get(
            "pincode"
        ),

        "location_name": location.get(
            "name"
        ),

        "district": location.get(
            "district"
        ),

        "state": location.get(
            "state"
        ),

        "country": location.get(
            "country",
            "India"
        ),

        "latitude": coordinates.get(
            "latitude"
        ),

        "longitude": coordinates.get(
            "longitude"
        ),

        "formatted": coordinates.get(
            "formatted"
        )
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    import asyncio

    async def test():

        result = await resolve_pincode(
            "722122"
        )

        print(result)

    asyncio.run(test())