from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.wind import router as wind_router

app = FastAPI(
    title="Wind Forecast Analytics API",
    description=(
        "Analyse UK wind generation forecasts "
        "against actual generation."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(wind_router)

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Check whether the API is running."""
    return {
        "status": "healthy",
        "service": "wind-forecast-analytics",
    }