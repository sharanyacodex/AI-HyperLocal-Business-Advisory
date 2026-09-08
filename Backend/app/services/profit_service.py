def calculate_profit_potential(
    business_type: str,
    market_demand: float,
    competitor_count: int
):
    """
    Estimate profit potential using available
    real market and competition indicators.
    """

    # Higher market demand increases profit potential
    demand_component = market_demand * 0.7

    # Lower competition improves profit potential
    if competitor_count <= 5:
        competition_component = 30
    elif competitor_count <= 10:
        competition_component = 25
    elif competitor_count <= 20:
        competition_component = 20
    elif competitor_count <= 30:
        competition_component = 15
    else:
        competition_component = 5

    profit_potential = (
        demand_component + competition_component
    )

    profit_potential = max(
        0,
        min(100, profit_potential)
    )

    return round(profit_potential, 2)