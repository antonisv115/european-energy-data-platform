
from datetime import date, timedelta

from energy_platform.api import fetch_dataset
from energy_platform.data_quality import (
    validate_daily_coverage,
    validate_dataset_metadata,
)
from energy_platform.db import get_connection
from energy_platform.loader import load_generation, load_prices
from energy_platform.raw_storage import (
    get_raw_path,
    load_raw,
    save_raw,
)
from energy_platform.transform import (
    transform_generation,
    transform_prices,
)


# dataset configuration
DATASETS = {
    "prices": {
        "endpoint": "/v2/price",
        "area": "DE-LU",
        "area_param": "bzn",
    },
    "generation": {
        "endpoint": "/v2/public_power",
        "area": "de",
        "area_param": "country",
    },
}


def iter_days(start_day, end_day):
    # validate date range
    start = date.fromisoformat(start_day)
    end = date.fromisoformat(end_day)

    if start.isoformat() != start_day:
        raise ValueError("Invalid start date format")

    if end.isoformat() != end_day:
        raise ValueError("Invalid end date format")

    if start > end:
        raise ValueError("Start date must not be after end date")

    # generate dates
    current = start

    while current <= end:
        yield current.isoformat()
        current += timedelta(days=1)


def load_or_fetch_raw(dataset, day):
    # read dataset settings
    config = DATASETS[dataset]
    area = config["area"]

    # check local raw cache
    path = get_raw_path(dataset, area, day)

    if path.exists():
        payload, _ = load_raw(dataset, area, day)
        return payload, "cache"

    # fetch missing raw data
    params = {
        config["area_param"]: area,
        "start": day,
        "end": day,
    }

    payload, source_url = fetch_dataset(
        config["endpoint"],
        params,
    )

    # save original response
    save_raw(
        dataset,
        area,
        day,
        payload,
        source_url,
    )

    # verify saved data
    payload, _ = load_raw(dataset, area, day)

    return payload, "api"


def process_day(day):
    # get raw datasets
    prices, price_source = load_or_fetch_raw("prices", day)
    generation, generation_source = load_or_fetch_raw(
        "generation", day
    )

    # validate prices
    validate_dataset_metadata(prices, "prices", "DE-LU")
    validate_daily_coverage(prices, day)

    # validate generation
    validate_dataset_metadata(generation, "generation", "de")
    validate_daily_coverage(generation, day)

    # transform datasets
    price_records = transform_prices(prices)
    generation_records = transform_generation(generation)

    # load both datasets in one transaction
    with get_connection() as conn:
        price_count = load_prices(conn, price_records)
        generation_count = load_generation(conn, generation_records)

    return {
        "day": day,
        "prices": price_count,
        "generation": generation_count,
        "price_source": price_source,
        "generation_source": generation_source,
    }
