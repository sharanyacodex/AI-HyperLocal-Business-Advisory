def calculate_opportunity(
    market_demand: float,
    competitor_count: int
):
    """
    Calculate opportunity using market demand
    and real competitor count.
    """

    # Demand contribution
    demand_score = market_demand

    # Competition penalty
    if competitor_count <= 5:
        competition_penalty = 10
    elif competitor_count <= 10:
        competition_penalty = 20
    elif competitor_count <= 20:
        competition_penalty = 35
    elif competitor_count <= 30:
        competition_penalty = 50
    else:
        competition_penalty = 65

    # Final opportunity score
    opportunity = demand_score - competition_penalty

    # Keep score between 0 and 100
    opportunity = max(0, min(100, opportunity))

    return round(opportunity, 2)