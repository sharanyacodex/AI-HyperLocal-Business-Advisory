from fastapi import APIRouter, HTTPException

from models.integration import IntegrationInput, IntegrationResponse
from services.integration_service import evaluate_integration

router = APIRouter(
    prefix="/api/module2/integration",
    tags=["Module 2 Integration"],
)


@router.post(
    "/calculate",
    response_model=IntegrationResponse,
)
def calculate_integration(data: IntegrationInput):
    """
    Connect scheme matching with the deterministic financial engine.
    """

    try:
        return evaluate_integration(data)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Integration calculation failed.",
        ) from exc