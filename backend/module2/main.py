from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.financial import router as financial_router
from routes.repayment import router as repayment_router
from routes.schemes import router as schemes_router
from routes.integration import router as integration_router


app = FastAPI(
    title="AI Hyper-Local Business Advisory - Module 2",
    version="1.0.0"
)

# Allow the Vite/React frontend to communicate with the FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(financial_router)
app.include_router(repayment_router)
app.include_router(schemes_router)
app.include_router(integration_router)


@app.get("/")
def root():
    return {
        "message": "Module 2 Backend is running!"
    }