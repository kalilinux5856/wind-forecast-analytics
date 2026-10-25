import asyncio
from datetime import datetime, timedelta, timezone
from pprint import pprint

from app.services.elexon import (
    fetch_wind_actuals,
    fetch_wind_forecasts,
)


async def main():
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=1)

    actuals = await fetch_wind_actuals(start, end)
    forecasts = await fetch_wind_forecasts(start, end)

    print("\nACTUALS — first 5 records")
    pprint(actuals[:5])

    print("\nFORECASTS — first 10 records")
    pprint(forecasts[:10])

    print("\nActual record count:", len(actuals))
    print("Forecast record count:", len(forecasts))

    publication_times = sorted({
    row["publishTime"]
    for row in forecasts
    if row.get("publishTime")
    })

    delivery_times = sorted({
        row["startTime"]
        for row in forecasts
        if row.get("startTime")
    })

    print("\nDistinct forecast publication times:", len(publication_times))
    print("First 10 publication times:", publication_times[:10])
    print("Distinct forecast delivery times:", len(delivery_times))
    print("First 10 delivery times:", delivery_times[:10])


asyncio.run(main())