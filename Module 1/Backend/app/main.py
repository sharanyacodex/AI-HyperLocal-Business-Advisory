from app.services.risk_service import calculate_risk_safety
from app.services.profit_service import calculate_profit_potential
from app.services.opportunity_service import calculate_opportunity
from app.services.market_service import get_market_demand
from app.services.competitor_service import find_nearby_competitors
from app.services.location_service import geocode_location
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.services.feasibility_service import (
    calculate_feasibility_score,
    calculate_competition_level
)


app = FastAPI(
    title="AI Hyper-Local Business Advisory",
    description="Backend API for business feasibility analysis",
    version="1.0.0"
)


class FeasibilityInput(BaseModel):
    market_demand: float = Field(..., ge=0, le=100)
    opportunity: float = Field(..., ge=0, le=100)
    profit_potential: float = Field(..., ge=0, le=100)
    risk_safety: float = Field(..., ge=0, le=100)
    competition_level: float = Field(..., ge=0, le=100)


@app.get("/")
def root():
    return {
        "message": "AI Hyper-Local Business Advisory API is running"
    }


@app.post("/module1/feasibility")
def calculate_feasibility(data: FeasibilityInput):
    return calculate_feasibility_score(
        market_demand=data.market_demand,
        opportunity=data.opportunity,
        profit_potential=data.profit_potential,
        risk_safety=data.risk_safety,
        competition_level=data.competition_level
    )
@app.get("/location")
async def get_location(location: str):
    result = await geocode_location(location)

    if result is None:
        return {
            "success": False,
            "message": "Location not found"
        }

    return {
        "success": True,
        "location": result
    }
@app.get("/competitors")
async def get_competitors(
    latitude: float,
    longitude: float,
    business_type: str
):
    result = await find_nearby_competitors(
        latitude=latitude,
        longitude=longitude,
        business_type=business_type
    )

    if not result.get("success"):
        return result

    competitor_count = result.get("competitor_count", 0)

    competition_level = calculate_competition_level(
        competitor_count
    )

    result["competition_level"] = competition_level

    return result
@app.get("/module1/analyze")
async def analyze_business(
    latitude: float,
    longitude: float,
    business_type: str
):
    # 1. Get real competitor data
    competitor_result = await find_nearby_competitors(
        latitude=latitude,
        longitude=longitude,
        business_type=business_type
    )

    if not competitor_result.get("success"):
        return competitor_result

    competitor_count = competitor_result.get(
        "competitor_count", 0
    )

    # 2. Calculate competition level
    competition_level = calculate_competition_level(
        competitor_count
    )

    # 3. Get real market demand
    market_result = get_market_demand(
        business_type
    )

    if not market_result.get("success"):
        return {
            "success": True,
            "business_type": business_type,
            "market_demand": None,
            "competitor_count": competitor_count,
            "competition_level": competition_level,
            "opportunity": None,
            "profit_potential": None,
            "risk_safety": None,
            "feasibility": None,
            "message": "Market demand data is temporarily unavailable.",
            "competitors": competitor_result.get(
                "competitors", []
            )
        }

    market_demand = market_result.get(
        "market_demand", 0
    )

    # 4. Calculate opportunity
    opportunity = calculate_opportunity(
        market_demand=market_demand,
        competitor_count=competitor_count
    )

    # 5. Calculate profit potential
    profit_potential = calculate_profit_potential(
        business_type=business_type,
        market_demand=market_demand,
        competitor_count=competitor_count
    )

    # 6. Get real weather/safety data
    risk_result = await calculate_risk_safety(
        latitude=latitude,
        longitude=longitude
    )

    if not risk_result.get("success"):
        return {
            "success": True,
            "business_type": business_type,
            "market_demand": market_demand,
            "market_data_source": market_result.get(
                "source"
            ),
            "competitor_count": competitor_count,
            "competition_level": competition_level,
            "opportunity": opportunity,
            "profit_potential": profit_potential,
            "risk_safety": None,
            "feasibility": None,
            "message": "Risk/safety data is temporarily unavailable.",
            "competitors": competitor_result.get(
                "competitors", []
            )
        }

    risk_safety = risk_result.get(
        "risk_safety"
    )

    # 7. Calculate final feasibility
    feasibility = calculate_feasibility_score(
        market_demand=market_demand,
        opportunity=opportunity,
        profit_potential=profit_potential,
        risk_safety=risk_safety,
        competition_level=competition_level
    )

    # 8. Return complete analysis
    return {
        "success": True,
        "business_type": business_type,
        "market_demand": market_demand,
        "market_data_source": market_result.get(
            "source"
        ),
        "competitor_count": competitor_count,
        "competition_level": competition_level,
        "opportunity": opportunity,
        "profit_potential": profit_potential,
        "risk_safety": risk_safety,
        "risk_data_source": risk_result.get(
            "source"
        ),
        "current_weather": risk_result.get(
            "current_weather"
        ),
        "feasibility": feasibility,
        "competitors": competitor_result.get(
            "competitors", []
        )
    }