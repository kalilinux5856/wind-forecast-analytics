
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.services.elexon import fetch_wind_actuals

router = APIRouter(prefix="/api/wind", tags=["Wind"])


@router.get("/actuals")
async def get_wind_actuals(
    days: int = Query(default=7, ge=1, le=30),
):
    """Return actual UK wind generation for the requested period."""

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    try:
        rows = await fetch_wind_actuals(start, end)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve wind actuals from Elexon.",
        ) from exc

    records = [
        {
            "startTime": row.get("startTime"),
            "publishTime": row.get("publishTime"),
            "generation": row.get("generation"),
            "fuelType": row.get("fuelType"),
        }
        for row in rows
        if row.get("startTime") is not None
        and row.get("generation") is not None
    ]

    records.sort(key=lambda row: row["startTime"])

    return {
        "source": "Elexon BMRS",
        "metric": "actual_wind_generation",
        "days": days,
        "count": len(records),
        "data": records,
    }
