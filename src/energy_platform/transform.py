
from datetime import datetime, timezone
from decimal import Decimal


# selected generation technologies
GENERATION_TECHNOLOGIES = (
    "solar",
    "wind_onshore",
    "wind_offshore",
    "biomass",
    "geothermal",
    "hydro_run_of_river",
    "hydro_water_reservoir",
    "hydro_pumped_storage",
    "fossil_gas",
    "fossil_oil",
    "fossil_hard_coal",
    "fossil_brown_coal_lignite",
    "fossil_coal_derived_gas",
    "waste",
    "others",
)


def parse_timestamp(value):
    # parse source timestamp
    timestamp = datetime.fromisoformat(value)

    # require timezone information
    if timestamp.utcoffset() is None:
        raise ValueError("Timestamp has no timezone")

    return timestamp.astimezone(timezone.utc)


def parse_number(value):
    # reject invalid values
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Invalid numeric value: {value}")

    # preserve decimal representation
    number = Decimal(str(value))

    if not number.is_finite():
        raise ValueError(f"Non-finite numeric value: {value}")

    return number


def validate_payload(payload, expected_unit):
    # check api structure
    if not isinstance(payload, dict):
        raise ValueError("Invalid API payload")

    if payload.get("schema_version") != "2.0":
        raise ValueError("Unsupported schema version")

    if payload.get("interval_minutes") != 15:
        raise ValueError("Unexpected time interval")

    if payload.get("unit") != expected_unit:
        raise ValueError("Unexpected dataset unit")

    if not isinstance(payload.get("series"), list):
        raise ValueError("Invalid series structure")

    if not isinstance(payload.get("data"), list):
        raise ValueError("Invalid data structure")


def transform_prices(payload, bidding_zone="DE-LU"):
    # validate price dataset
    validate_payload(payload, "EUR / MWh")

    series = {item["id"]: item for item in payload["series"]}

    if "day_ahead_price" not in series:
        raise ValueError("Missing day-ahead price series")

    price_unit = series["day_ahead_price"].get("unit") or payload["unit"]

    if price_unit != "EUR / MWh":
        raise ValueError("Unexpected price unit")

    records = []
    seen_timestamps = set()

    for row in payload["data"]:
        # convert timestamp
        timestamp = parse_timestamp(row["timestamp"])

        if timestamp in seen_timestamps:
            raise ValueError(f"Duplicate timestamp: {timestamp}")

        seen_timestamps.add(timestamp)

        # read price value
        values = row["values"]

        if not isinstance(values, dict):
            raise ValueError("Invalid values structure")

        price = parse_number(values.get("day_ahead_price"))

        # create database record
        record = {
            "bidding_zone": bidding_zone,
            "timestamp_utc": timestamp,
            "price_eur_mwh": price,
            "interval_minutes": 15,
        }

        records.append(record)

    return records


def transform_generation(payload, country="de"):
    # validate generation dataset
    validate_payload(payload, "MW")

    series = {item["id"]: item for item in payload["series"]}

    # check required technologies
    missing = set(GENERATION_TECHNOLOGIES) - set(series)

    if missing:
        raise ValueError(f"Missing generation series: {sorted(missing)}")

    # check technology units
    for technology in GENERATION_TECHNOLOGIES:
        unit = series[technology].get("unit") or payload["unit"]

        if unit != "MW":
            raise ValueError(f"Unexpected unit for {technology}")

    records = []
    seen_timestamps = set()

    for row in payload["data"]:
        # convert timestamp
        timestamp = parse_timestamp(row["timestamp"])

        if timestamp in seen_timestamps:
            raise ValueError(f"Duplicate timestamp: {timestamp}")

        seen_timestamps.add(timestamp)

        values = row["values"]

        if not isinstance(values, dict):
            raise ValueError("Invalid values structure")

        # create one record per technology
        for technology in GENERATION_TECHNOLOGIES:
            power = parse_number(values.get(technology))

            record = {
                "country": country,
                "timestamp_utc": timestamp,
                "technology": technology,
                "power_mw": power,
                "interval_minutes": 15,
            }

            records.append(record)

    return records
