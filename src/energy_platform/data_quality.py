
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from energy_platform.transform import GENERATION_TECHNOLOGIES, parse_timestamp

# market settings
MARKET_TIMEZONE = ZoneInfo("Europe/Berlin")
INTERVAL = timedelta(minutes=15)


def validate_daily_coverage(payload, day):
    # check metadata
    if not isinstance(payload, dict):
        raise ValueError("Invalid payload")

    if payload.get("timezone") != "Europe/Berlin":
        raise ValueError("Unexpected timezone")

    if payload.get("interval_minutes") != 15:
        raise ValueError("Unexpected interval")

    rows = payload.get("data")

    if not isinstance(rows, list):
        raise ValueError("Invalid data structure")

    # calculate local day boundaries
    target_day = date.fromisoformat(day)

    start_local = datetime.combine(
        target_day,
        time.min,
        tzinfo=MARKET_TIMEZONE
    )

    end_local = datetime.combine(
        target_day + timedelta(days=1),
        time.min,
        tzinfo=MARKET_TIMEZONE
    )

    # convert boundaries to utc
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    # generate expected timestamps
    expected_count = int((end_utc - start_utc) / INTERVAL)

    expected = {
        start_utc + i * INTERVAL
        for i in range(expected_count)
    }

    # read actual timestamps
    actual = [
        parse_timestamp(row["timestamp"])
        for row in rows
    ]

    actual_set = set(actual)

    # check duplicates
    if len(actual) != len(actual_set):
        raise ValueError("Duplicate timestamps")

    # check missing or unexpected timestamps
    missing = expected - actual_set
    unexpected = actual_set - expected

    if missing or unexpected:
        raise ValueError(
            f"Day coverage mismatch: "
            f"missing={len(missing)}, "
            f"unexpected={len(unexpected)}"
        )

    return {
        "day": day,
        "expected_timestamps": expected_count,
        "actual_timestamps": len(actual),
        "first_utc": start_utc,
        "last_utc": end_utc - INTERVAL,
    }

def validate_dataset_metadata(payload, dataset, area):
    # expected dataset settings
    configs = {
        "prices": {
            "endpoint": "price",
            "area_field": "bidding_zone",
            "unit": "EUR / MWh",
        },
        "generation": {
            "endpoint": "public_power",
            "area_field": "country",
            "unit": "MW",
        },
    }

    if dataset not in configs:
        raise ValueError("Unknown dataset")

    config = configs[dataset]

    # check basic metadata
    if not isinstance(payload, dict):
        raise ValueError("Invalid payload")

    if payload.get("schema_version") != "2.0":
        raise ValueError("Unexpected schema version")

    if payload.get("endpoint") != config["endpoint"]:
        raise ValueError("Unexpected endpoint")

    if payload.get(config["area_field"]) != area:
        raise ValueError("Unexpected area")

    if payload.get("timezone") != "Europe/Berlin":
        raise ValueError("Unexpected timezone")

    if payload.get("interval_minutes") != 15:
        raise ValueError("Unexpected interval")

    if payload.get("unit") != config["unit"]:
        raise ValueError("Unexpected dataset unit")

    # check series structure
    series = payload.get("series")

    if not isinstance(series, list):
        raise ValueError("Invalid series")

    ids = []

    for item in series:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not item["id"]
        ):
            raise ValueError("Invalid series id")

        ids.append(item["id"])

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate series ids")

    # check required series
    required = (
        {"day_ahead_price"}
        if dataset == "prices"
        else set(GENERATION_TECHNOLOGIES)
    )

    missing = required - set(ids)

    if missing:
        raise ValueError(f"Missing required series: {sorted(missing)}")

    # check individual units
    percentage_series = {
        "renewable_share_of_load",
        "renewable_share_of_generation",
    }

    for item in series:
        series_id = item["id"]
        unit = item.get("unit") or payload["unit"]

        if series_id in required and unit != config["unit"]:
            raise ValueError(f"Unexpected unit: {series_id}")

        if series_id in percentage_series and unit != "%":
            raise ValueError(f"Unexpected percentage unit: {series_id}")

    # check row structure
    rows = payload.get("data")

    if not isinstance(rows, list) or not rows:
        raise ValueError("Invalid data rows")

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Invalid row: {index}")

        values = row.get("values")

        if not isinstance(values, dict):
            raise ValueError(f"Invalid values: {index}")

        if not required.issubset(values):
            raise ValueError(f"Missing required values: {index}")

        unknown = set(values) - set(ids)

        if unknown:
            raise ValueError(f"Unknown value keys: {sorted(unknown)}")

    return {
        "dataset": dataset,
        "area": area,
        "series_count": len(series),
        "rows_count": len(rows),
    }
