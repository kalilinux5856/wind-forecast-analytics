
from app.analysis.metrics import compare_forecasts


def test_forecast_metrics_with_one_hour_lead():
    forecasts = [
        {
            "startTime": "2026-10-25T10:00:00Z",
            "publishTime": "2026-10-25T09:00:00Z",
            "generation": 120,
        },
        {
            "startTime": "2026-10-25T10:00:00Z",
            "publishTime": "2026-10-25T09:30:00Z",
            "generation": 110,
        },
    ]

    actuals = [
        {
            "startTime": "2026-10-25T10:00:00Z",
            "publishTime": "2026-10-25T10:30:00Z",
            "generation": 100,
        }
    ]

    result = compare_forecasts(
        forecasts, actuals, lead_hours=1
    )

    assert result["matchedIntervals"] == 1
    assert result["data"][0]["forecast"] == 120
    assert result["metrics"]["mae"] == 20
    assert result["metrics"]["rmse"] == 20
    assert result["metrics"]["bias"] == 20


def test_forecast_metrics_with_zero_hour_lead():
    forecasts = [
        {
            "startTime": "2026-10-25T10:00:00Z",
            "publishTime": "2026-10-25T09:00:00Z",
            "generation": 120,
        },
        {
            "startTime": "2026-10-25T10:00:00Z",
            "publishTime": "2026-10-25T09:30:00Z",
            "generation": 110,
        },
    ]

    actuals = [
        {
            "startTime": "2026-10-25T10:00:00Z",
            "publishTime": "2026-10-25T10:30:00Z",
            "generation": 100,
        }
    ]

    result = compare_forecasts(
        forecasts, actuals, lead_hours=0
    )

    assert result["matchedIntervals"] == 1
    assert result["data"][0]["forecast"] == 110
    assert result["metrics"]["mae"] == 10
    assert result["metrics"]["rmse"] == 10
    assert result["metrics"]["bias"] == 10
