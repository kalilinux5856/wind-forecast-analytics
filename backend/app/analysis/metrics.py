from datetime import datetime, timedelta
import math


def parse_datetime(value: str) -> datetime:
    """Parse ISO timestamps, including timestamps ending in Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compare_forecasts(
    forecasts: list[dict],
    actuals: list[dict],
    lead_hours: int = 1,
) -> dict:
    """
    Compare hourly forecasts with hourly averages of actual generation.

    For each delivery hour, select the latest forecast published
    at or before delivery time minus the requested lead time.

    Error = forecast - actual.
    """

    if lead_hours < 0:
        raise ValueError("lead_hours must be non-negative")

    # Keep the latest published actual for each half-hourly interval.
    actual_by_interval = {}

    for row in actuals:
        try:
            start = parse_datetime(row["startTime"])
            generation = float(row["generation"])
            published = parse_datetime(
                row.get("publishTime") or row["startTime"]
            )
        except (KeyError, ValueError, TypeError):
            continue

        key = start.isoformat()
        previous = actual_by_interval.get(key)

        if previous is None or published > previous["publish_time"]:
            actual_by_interval[key] = {
                "start": start,
                "publish_time": published,
                "generation": generation,
            }

    # Group actual observations into UTC clock hours.
    hourly_actuals = {}

    for row in actual_by_interval.values():
        hour = row["start"].replace(minute=0, second=0, microsecond=0)
        hourly_actuals.setdefault(hour.isoformat(), []).append(
            row["generation"]
        )

    actual_by_hour = {
        hour: sum(values) / len(values)
        for hour, values in hourly_actuals.items()
    }

    # Group forecast revisions by delivery timestamp.
    forecasts_by_delivery = {}

    for row in forecasts:
        try:
            delivery = parse_datetime(row["startTime"])
            published = parse_datetime(row["publishTime"])
            generation = float(row["generation"])
        except (KeyError, ValueError, TypeError):
            continue

        forecasts_by_delivery.setdefault(
            delivery.isoformat(), []
        ).append({
            "delivery": delivery,
            "published": published,
            "generation": generation,
        })

    matched = []
    eligible_forecast_hours = 0

    for delivery_key, revisions in forecasts_by_delivery.items():
        delivery = revisions[0]["delivery"]
        hour_key = delivery.replace(
            minute=0, second=0, microsecond=0
        ).isoformat()

        if hour_key not in actual_by_hour:
            continue

        cutoff = delivery - timedelta(hours=lead_hours)
        eligible = [
            revision for revision in revisions
            if revision["published"] <= cutoff
        ]

        if not eligible:
            continue

        eligible_forecast_hours += 1
        selected = max(eligible, key=lambda item: item["published"])

        actual = actual_by_hour[hour_key]
        forecast = selected["generation"]
        error = forecast - actual

        matched.append({
            "startTime": delivery.isoformat(),
            "forecastPublishTime": selected["published"].isoformat(),
            "forecast": forecast,
            "actual": actual,
            "error": error,
            "absoluteError": abs(error),
        })

    # If duplicate forecast delivery timestamps map to the same
    # actual hour, retain one forecast per actual hour.
    matched_by_hour = {}

    for row in matched:
        hour_key = parse_datetime(row["startTime"]).replace(
            minute=0, second=0, microsecond=0
        ).isoformat()

        previous = matched_by_hour.get(hour_key)
        if previous is None or row["startTime"] < previous["startTime"]:
            matched_by_hour[hour_key] = row

    matched = sorted(
        matched_by_hour.values(),
        key=lambda row: row["startTime"],
    )

    if not matched:
        return {
            "selectionRule": (
                "latest forecast published at or before "
                "delivery time minus lead time"
            ),
            "leadHours": lead_hours,
            "errorConvention": "forecast - actual",
            "actualAggregation": "mean of available half-hourly observations per UTC hour",
            "matchedIntervals": 0,
            "metrics": None,
            "data": [],
        }

    errors = [row["error"] for row in matched]

    return {
        "selectionRule": (
            "latest forecast published at or before "
            "delivery time minus lead time"
        ),
        "leadHours": lead_hours,
        "errorConvention": "forecast - actual",
        "actualAggregation": "mean of available half-hourly observations per UTC hour",
        "matchedIntervals": len(matched),
        "metrics": {
            "mae": round(sum(abs(e) for e in errors) / len(errors), 2),
            "rmse": round(math.sqrt(sum(e * e for e in errors) / len(errors)), 2),
            "bias": round(sum(errors) / len(errors), 2),
        },
        "data": matched,
    }
