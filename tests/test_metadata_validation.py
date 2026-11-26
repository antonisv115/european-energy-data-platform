
import pytest

from energy_platform.data_quality import validate_dataset_metadata
from energy_platform.transform import GENERATION_TECHNOLOGIES


@pytest.fixture
def price_payload():
    # sample price dataset
    return {
        "schema_version": "2.0",
        "endpoint": "price",
        "bidding_zone": "DE-LU",
        "timezone": "Europe/Berlin",
        "interval_minutes": 15,
        "unit": "EUR / MWh",
        "series": [{"id": "day_ahead_price"}],
        "data": [
            {
                "timestamp": "2026-09-01T00:00:00+02:00",
                "values": {"day_ahead_price": 163.91},
            }
        ],
    }


@pytest.fixture
def generation_payload():
    # sample generation dataset
    series = [
        {"id": tech}
        for tech in GENERATION_TECHNOLOGIES
    ]

    series.append({
        "id": "renewable_share_of_load",
        "unit": "%",
    })

    values = {
        tech: 0.0
        for tech in GENERATION_TECHNOLOGIES
    }

    values["renewable_share_of_load"] = 84.3

    return {
        "schema_version": "2.0",
        "endpoint": "public_power",
        "country": "de",
        "timezone": "Europe/Berlin",
        "interval_minutes": 15,
        "unit": "MW",
        "series": series,
        "data": [
            {
                "timestamp": "2026-09-01T00:00:00+02:00",
                "values": values,
            }
        ],
    }


def test_valid_price_metadata(price_payload):
    # accept valid price data
    result = validate_dataset_metadata(
        price_payload, "prices", "DE-LU"
    )

    assert result["series_count"] == 1
    assert result["rows_count"] == 1


def test_valid_generation_metadata(generation_payload):
    # accept mw and percentage series
    result = validate_dataset_metadata(
        generation_payload, "generation", "de"
    )

    assert result["series_count"] == 16


def test_wrong_endpoint(price_payload):
    # reject wrong endpoint
    price_payload["endpoint"] = "public_power"

    with pytest.raises(ValueError, match="Unexpected endpoint"):
        validate_dataset_metadata(price_payload, "prices", "DE-LU")


def test_wrong_area(price_payload):
    # reject wrong market area
    price_payload["bidding_zone"] = "FR"

    with pytest.raises(ValueError, match="Unexpected area"):
        validate_dataset_metadata(price_payload, "prices", "DE-LU")


def test_wrong_country(generation_payload):
    # reject wrong country
    generation_payload["country"] = "fr"

    with pytest.raises(ValueError, match="Unexpected area"):
        validate_dataset_metadata(generation_payload, "generation", "de")


def test_duplicate_series(price_payload):
    # reject duplicate series ids
    price_payload["series"].append({"id": "day_ahead_price"})

    with pytest.raises(ValueError, match="Duplicate series ids"):
        validate_dataset_metadata(price_payload, "prices", "DE-LU")


def test_missing_technology(generation_payload):
    # reject missing technology
    generation_payload["series"].pop(0)

    with pytest.raises(ValueError, match="Missing required series"):
        validate_dataset_metadata(generation_payload, "generation", "de")


def test_wrong_technology_unit(generation_payload):
    # reject incorrect power unit
    generation_payload["series"][0]["unit"] = "%"

    with pytest.raises(ValueError, match="Unexpected unit"):
        validate_dataset_metadata(generation_payload, "generation", "de")


def test_wrong_percentage_unit(generation_payload):
    # reject incorrect percentage unit
    generation_payload["series"][-1]["unit"] = "MW"

    with pytest.raises(ValueError, match="Unexpected percentage unit"):
        validate_dataset_metadata(generation_payload, "generation", "de")


def test_missing_required_value(price_payload):
    # reject missing measurement
    price_payload["data"][0]["values"] = {}

    with pytest.raises(ValueError, match="Missing required values"):
        validate_dataset_metadata(price_payload, "prices", "DE-LU")


def test_unknown_value_key(price_payload):
    # reject undeclared measurement
    price_payload["data"][0]["values"]["unknown"] = 10.0

    with pytest.raises(ValueError, match="Unknown value keys"):
        validate_dataset_metadata(price_payload, "prices", "DE-LU")
