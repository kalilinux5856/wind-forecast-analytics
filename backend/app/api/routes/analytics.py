from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from app.analysis.metrics import compare_forecasts
from app.services.elexon import (
    fetch_wind_actuals,
    fetch_wind_forecasts,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/wind-accuracy")
async def get_wind_accuracy(
    days: int = Query(default=7, ge=1, le=30),
    lead_hours: int = Query(default=1, ge=0, le=48),
):
    """Compare available wind forecasts with actual generation."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    
    try:
        actuals = await fetch_wind_actuals(start, end)
        forecast_start = start - timedelta(hours=lead_hours + 12)
        forecasts = await fetch_wind_forecasts(forecast_start, end)
        forecasts = [forecast for forecast in forecasts if start <= datetime.fromisoformat(forecast["startTime"].replace("Z", "+00:00")) <= end
]
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve wind data from Elexon.",
        ) from exc
        
    result = compare_forecasts(
        forecasts,
        actuals,
        lead_hours=lead_hours,
    )
    
    return {
        "source": "Elexon BMRS",
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": days,
        },
        **result,
    }
