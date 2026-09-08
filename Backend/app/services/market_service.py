from pytrends.request import TrendReq
from datetime import datetime, timedelta

# Store recent results in memory
market_cache = {}

# Cache validity: 30 minutes
CACHE_MINUTES = 30


def get_market_demand(business_type: str):
    try:
        business_type = business_type.strip().lower()

        # -------------------------------
        # 1. Check cache first
        # -------------------------------
        if business_type in market_cache:
            cached_time, cached_data = market_cache[business_type]

            if datetime.now() - cached_time < timedelta(
                minutes=CACHE_MINUTES
            ):
                return cached_data

        # -------------------------------
        # 2. Request Google Trends
        # -------------------------------
        pytrends = TrendReq(
            hl="en-IN",
            tz=330,
            timeout=(10, 25)
        )

        pytrends.build_payload(
            [business_type],
            timeframe="today 12-m",
            geo="IN"
        )

        data = pytrends.interest_over_time()

        # -------------------------------
        # 3. No data
        # -------------------------------
        if data.empty:
            return {
                "success": False,
                "market_demand": None,
                "source": "Google Trends",
                "message": "No market data available"
            }

        # -------------------------------
        # 4. Calculate demand
        # -------------------------------
        average_interest = float(
            data[business_type].mean()
        )

        result = {
            "success": True,
            "market_demand": round(
                average_interest, 2
            ),
            "source": "Google Trends",
            "period": "Last 12 months"
        }

        # -------------------------------
        # 5. Save result in cache
        # -------------------------------
        market_cache[business_type] = (
            datetime.now(),
            result
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "market_demand": None,
            "source": "Google Trends",
            "message": str(e)
        }