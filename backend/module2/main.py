from fastapi import FastAPI

from routes.financial import router as financial_router
from routes.repayment import router as repayment_router

app = FastAPI(
    title="AI Hyper-Local Business Advisory - Module 2",
    version="1.0.0"
)

app.include_router(financial_router)
app.include_router(repayment_router)


@app.get("/")
def root():
    return {
        "message": "Module 2 Backend is running!"
    }