
from datetime import datetime, timedelta, timezone

import httpx


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


async def fetch_wind_actuals(
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Fetch actual UK wind generation for a time range."""

    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "fuelType": "WIND",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/datasets/FUELHH",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    return data if isinstance(data, list) else data.get("data", [])


async def fetch_wind_forecasts(
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Fetch wind generation forecast records for a time range."""

    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/datasets/WINDFOR",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    return data if isinstance(data, list) else data.get("data", [])


def default_time_range() -> tuple[datetime, datetime]:
    """Return a recent time range in UTC."""

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    return start, end
