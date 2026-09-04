def calculate_feasibility_score(
    market_demand: float,
    opportunity: float,
    profit_potential: float,
    risk_safety: float,
    competition_level: float
):
    score = (
        market_demand * 0.25
        + opportunity * 0.25
        + profit_potential * 0.25
        + risk_safety * 0.15
        + (100 - competition_level) * 0.10
    )

    score = round(score, 2)

    if score >= 75:
        recommendation = "GOOD OPPORTUNITY"
    elif score >= 50:
        recommendation = "MODERATE OPPORTUNITY"
    else:
        recommendation = "LOW OPPORTUNITY"

    return {
        "feasibility_score": score,
        "recommendation": recommendation
    }


def calculate_competition_level(competitor_count: int):
    if competitor_count <= 5:
        return 20
    elif competitor_count <= 10:
        return 40
    elif competitor_count <= 20:
        return 60
    elif competitor_count <= 30:
        return 80
    else:
        return 100