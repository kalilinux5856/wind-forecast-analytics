
from datetime import datetime

import math


def parse_datetime(value: str) -> datetime:
    """Parse ISO timestamps, including timestamps ending in Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compare_forecasts(
    forecasts: list[dict],
    actuals: list[dict],
) -> dict:
    """
    Match forecasts to actuals by delivery interval.

    Selection rule: for each delivery interval, select the most
    recently published forecast available at or before that
    interval's start time.

    Error convention: forecast - actual.
    """

    # Keep the latest published actual record for each interval.
    actual_by_interval = {}

    for row in actuals:
        start_time = row.get("startTime")
        generation = row.get("generation")

        if start_time is None or generation is None:
            continue

        try:
            actual_value = float(generation)
            interval_time = parse_datetime(start_time)
            publish_time = parse_datetime(
                row.get("publishTime") or start_time
            )
        except (ValueError, TypeError):
            continue

        key = interval_time.isoformat()
        existing = actual_by_interval.get(key)

        if existing is None or publish_time > existing["publish_time"]:
            actual_by_interval[key] = {
                "interval_time": interval_time,
                "publish_time": publish_time,
                "actual": actual_value,
            }

    # Choose the latest forecast published no later than
    # the start of its delivery interval.
    forecast_by_interval = {}

    for row in forecasts:
        start_time = row.get("startTime")
        publish_time = row.get("publishTime")
        generation = row.get("generation")

        if not start_time or not publish_time or generation is None:
            continue

        try:
            interval_time = parse_datetime(start_time)
            published_at = parse_datetime(publish_time)
            forecast_value = float(generation)
        except (ValueError, TypeError):
            continue

        if published_at > interval_time:
            continue

        key = interval_time.isoformat()
        existing = forecast_by_interval.get(key)

        if (
            existing is None
            or published_at > existing["publish_time"]
        ):
            forecast_by_interval[key] = {
                "interval_time": interval_time,
                "publish_time": published_at,
                "forecast": forecast_value,
            }

    # Match the selected forecast to the actual for each interval.
    matched = []

    for key, forecast_row in forecast_by_interval.items():
        actual_row = actual_by_interval.get(key)

        if actual_row is None:
            continue

        forecast_value = forecast_row["forecast"]
        actual_value = actual_row["actual"]
        error = forecast_value - actual_value

        matched.append({
            "startTime": forecast_row["interval_time"].isoformat(),
            "forecastPublishTime": forecast_row["publish_time"].isoformat(),
            "forecast": forecast_value,
            "actual": actual_value,
            "error": error,
            "absoluteError": abs(error),
        })

    matched.sort(key=lambda row: row["startTime"])

    if not matched:
        return {
            "selectionRule": "latest forecast published at or before interval start",
            "errorConvention": "forecast - actual",
            "matchedIntervals": 0,
            "unmatchedActualIntervals": len(actual_by_interval),
            "unmatchedForecastIntervals": len(forecast_by_interval),
            "metrics": None,
            "data": [],
        }

    errors = [row["error"] for row in matched]
    absolute_errors = [abs(error) for error in errors]

    mae = sum(absolute_errors) / len(errors)
    rmse = math.sqrt(sum(error ** 2 for error in errors) / len(errors))
    bias = sum(errors) / len(errors)

    return {
        "selectionRule": "latest forecast published at or before interval start",
        "errorConvention": "forecast - actual",
        "matchedIntervals": len(matched),
        "unmatchedActualIntervals": len(actual_by_interval) - len(matched),
        "unmatchedForecastIntervals": len(forecast_by_interval) - len(matched),
        "metrics": {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "bias": round(bias, 2),
        },
        "data": matched,
    }
