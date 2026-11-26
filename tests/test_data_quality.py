
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from energy_platform.data_quality import validate_daily_coverage


def make_payload(day):
    # create sample timestamps
    zone = ZoneInfo("Europe/Berlin")
    target_day = date.fromisoformat(day)

    start = datetime.combine(
        target_day,
        time.min,
        tzinfo=zone
    ).astimezone(timezone.utc)

    end = datetime.combine(
        target_day + timedelta(days=1),
        time.min,
        tzinfo=zone
    ).astimezone(timezone.utc)

    step = timedelta(minutes=15)
    count = int((end - start) / step)

    rows = [
        {
            "timestamp": (start + i * step).isoformat(),
            "values": {}
        }
        for i in range(count)
    ]

    return {
        "timezone": "Europe/Berlin",
        "interval_minutes": 15,
        "data": rows
    }


@pytest.mark.parametrize(
    "day,expected",
    [
        ("2026-09-01", 96),
        ("2026-03-29", 92),
        ("2026-10-25", 100),
    ]
)
def test_valid_daily_coverage(day, expected):
    # check normal and dst days
    payload = make_payload(day)

    result = validate_daily_coverage(payload, day)

    assert result["expected_timestamps"] == expected
    assert result["actual_timestamps"] == expected


def test_missing_interval():
    # remove one timestamp
    payload = make_payload("2026-09-01")
    payload["data"].pop(10)

    with pytest.raises(ValueError, match="Day coverage mismatch"):
        validate_daily_coverage(payload, "2026-09-01")


def test_duplicate_interval():
    # add duplicate timestamp
    payload = make_payload("2026-09-01")
    payload["data"].append(payload["data"][0])

    with pytest.raises(ValueError, match="Duplicate timestamps"):
        validate_daily_coverage(payload, "2026-09-01")


def test_wrong_timezone():
    # reject wrong timezone
    payload = make_payload("2026-09-01")
    payload["timezone"] = "UTC"

    with pytest.raises(ValueError, match="Unexpected timezone"):
        validate_daily_coverage(payload, "2026-09-01")


def test_wrong_interval():
    # reject wrong resolution
    payload = make_payload("2026-09-01")
    payload["interval_minutes"] = 60

    with pytest.raises(ValueError, match="Unexpected interval"):
        validate_daily_coverage(payload, "2026-09-01")


def test_unexpected_timestamp():
    # move a timestamp outside the day
    payload = make_payload("2026-09-01")

    first = datetime.fromisoformat(payload["data"][0]["timestamp"])
    payload["data"][0]["timestamp"] = (
        first - timedelta(minutes=15)
    ).isoformat()

    with pytest.raises(ValueError, match="Day coverage mismatch"):
        validate_daily_coverage(payload, "2026-09-01")
