# ============================================================
# FEASIBILITY SERVICE
# ============================================================


def calculate_feasibility_score(
    market_demand: float,
    population_density: float,
    purchasing_power: float,
    opportunity: float,
    profit_potential: float,
    risk_safety: float,
    competition_level: float
):
    """
    Calculate the overall business feasibility score.

    All input scores are expected to be between 0 and 100.

    Weights:
        Market Demand       = 20%
        Population Density  = 15%
        Purchasing Power    = 15%
        Opportunity         = 20%
        Profit Potential    = 15%
        Risk/Safety         = 10%
        Competition         = 5%
    """

    # --------------------------------------------------------
    # LIMIT VALUES BETWEEN 0 AND 100
    # --------------------------------------------------------

    market_demand = max(
        0,
        min(float(market_demand), 100)
    )

    population_density = max(
        0,
        min(float(population_density), 100)
    )

    purchasing_power = max(
        0,
        min(float(purchasing_power), 100)
    )

    opportunity = max(
        0,
        min(float(opportunity), 100)
    )

    profit_potential = max(
        0,
        min(float(profit_potential), 100)
    )

    risk_safety = max(
        0,
        min(float(risk_safety), 100)
    )

    competition_level = max(
        0,
        min(float(competition_level), 100)
    )

    # --------------------------------------------------------
    # CALCULATE FEASIBILITY SCORE
    # --------------------------------------------------------

    score = (
        market_demand * 0.20
        + population_density * 0.15
        + purchasing_power * 0.15
        + opportunity * 0.20
        + profit_potential * 0.15
        + risk_safety * 0.10
        + (100 - competition_level) * 0.05
    )

    score = round(score, 2)

    # --------------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------------

    if score >= 75:
        recommendation = "GOOD OPPORTUNITY"

    elif score >= 50:
        recommendation = "MODERATE OPPORTUNITY"

    else:
        recommendation = "LOW OPPORTUNITY"

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "feasibility_score": score,
        "recommendation": recommendation
    }


# ============================================================
# COMPETITION LEVEL
# ============================================================

def calculate_competition_level(
    competitor_count: int
) -> float:
    """
    Convert number of competitors into a
    competition score between 0 and 100.

    Higher score = more competition.
    """

    if competitor_count <= 0:
        return 0

    elif competitor_count <= 5:
        return 20

    elif competitor_count <= 10:
        return 40

    elif competitor_count <= 20:
        return 60

    elif competitor_count <= 30:
        return 80

    else:
        return 100


# ============================================================
# POPULATION DENSITY LEVEL
# ============================================================

def get_population_density_level(
    population_density: float
) -> str:
    """
    Convert population density score into
    an easy-to-understand label.
    """

    if population_density >= 70:
        return "HIGH"

    elif population_density >= 40:
        return "MODERATE"

    else:
        return "LOW"


# ============================================================
# PURCHASING POWER LEVEL
# ============================================================

def get_purchasing_power_level(
    purchasing_power: float
) -> str:
    """
    Convert purchasing power score into
    an easy-to-understand label.
    """

    if purchasing_power >= 70:
        return "HIGH"

    elif purchasing_power >= 40:
        return "MODERATE"

    else:
        return "LOW"