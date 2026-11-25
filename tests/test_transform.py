
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from energy_platform.transform import (
    GENERATION_TECHNOLOGIES,
    transform_generation,
    transform_prices,
)


@pytest.fixture
def price_payload():
    # sample price data
    return {
        "schema_version": "2.0",
        "interval_minutes": 15,
        "unit": "EUR / MWh",
        "series": [
            {"id": "day_ahead_price", "unit": "EUR / MWh"}
        ],
        "data": [
            {
                "timestamp": "2026-09-01T00:00:00+02:00",
                "values": {"day_ahead_price": 163.91}
            }
        ]
    }


@pytest.fixture
def generation_payload():
    # sample generation data
    return {
        "schema_version": "2.0",
        "interval_minutes": 15,
        "unit": "MW",
        "series": [
            {"id": tech, "unit": "MW"}
            for tech in GENERATION_TECHNOLOGIES
        ],
        "data": [
            {
                "timestamp": "2026-09-01T00:00:00+02:00",
                "values": {
                    tech: 0.0
                    for tech in GENERATION_TECHNOLOGIES
                }
            }
        ]
    }


def test_price_transformation(price_payload):
    # check price record
    records = transform_prices(price_payload)

    assert len(records) == 1
    assert records[0]["bidding_zone"] == "DE-LU"
    assert records[0]["price_eur_mwh"] == Decimal("163.91")
    assert records[0]["interval_minutes"] == 15

    assert records[0]["timestamp_utc"] == datetime(
        2026, 8, 31, 22, 0,
        tzinfo=timezone.utc
    )


def test_generation_transformation(generation_payload):
    # check long format
    records = transform_generation(generation_payload)

    assert len(records) == 15
    assert len({r["technology"] for r in records}) == 15
    assert all(r["country"] == "de" for r in records)
    assert all(r["power_mw"] == Decimal("0.0") for r in records)


def test_negative_price(price_payload):
    # allow negative prices
    price_payload["data"][0]["values"]["day_ahead_price"] = -25.5

    records = transform_prices(price_payload)

    assert records[0]["price_eur_mwh"] == Decimal("-25.5")


def test_duplicate_timestamp(price_payload):
    # add duplicate row
    price_payload["data"].append(
        deepcopy(price_payload["data"][0])
    )

    with pytest.raises(ValueError, match="Duplicate timestamp"):
        transform_prices(price_payload)


def test_missing_timezone(price_payload):
    # remove timezone offset
    price_payload["data"][0]["timestamp"] = "2026-09-01T00:00:00"

    with pytest.raises(ValueError, match="no timezone"):
        transform_prices(price_payload)


@pytest.mark.parametrize(
    "bad_value",
    [None, True, "unknown", float("nan")]
)
def test_invalid_price(price_payload, bad_value):
    # reject invalid numbers
    price_payload["data"][0]["values"]["day_ahead_price"] = bad_value

    with pytest.raises(ValueError):
        transform_prices(price_payload)


def test_wrong_price_unit(price_payload):
    # reject unexpected unit
    price_payload["unit"] = "USD / MWh"

    with pytest.raises(ValueError, match="Unexpected dataset unit"):
        transform_prices(price_payload)


def test_wrong_interval(price_payload):
    # reject unexpected resolution
    price_payload["interval_minutes"] = 60

    with pytest.raises(ValueError, match="Unexpected time interval"):
        transform_prices(price_payload)


def test_missing_technology(generation_payload):
    # remove required series
    generation_payload["series"].pop()

    with pytest.raises(ValueError, match="Missing generation series"):
        transform_generation(generation_payload)


def test_wrong_generation_unit(generation_payload):
    # reject percentage as power
    generation_payload["series"][0]["unit"] = "%"

    with pytest.raises(ValueError, match="Unexpected unit"):
        transform_generation(generation_payload)


def test_missing_generation_value(generation_payload):
    # remove required measurement
    generation_payload["data"][0]["values"].pop("solar")

    with pytest.raises(ValueError, match="Invalid numeric value"):
        transform_generation(generation_payload)


def test_raw_data_unchanged(price_payload, generation_payload):
    # keep raw data unchanged
    original_prices = deepcopy(price_payload)
    original_generation = deepcopy(generation_payload)

    transform_prices(price_payload)
    transform_generation(generation_payload)

    assert price_payload == original_prices
    assert generation_payload == original_generation
