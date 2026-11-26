
from energy_platform.data_quality import validate_daily_coverage
from energy_platform.raw_storage import load_raw
from energy_platform.transform import (
    transform_generation,
    transform_prices,
)
from energy_platform.data_quality import (
    validate_daily_coverage,
    validate_dataset_metadata,
)

# dates to process
DAYS = [
    "2026-09-01",
    "2026-09-02",
]


for day in DAYS:
    print(f"\n--- Date: {day} ---")

    # load raw prices
    prices_payload, _ = load_raw("prices", "DE-LU", day)

    # check price metadata
    price_metadata = validate_dataset_metadata(
        prices_payload, "prices", "DE-LU"
    )
    print("Price metadata:", price_metadata)

    # check daily coverage
    price_quality = validate_daily_coverage(prices_payload, day)

    print("Price coverage:", price_quality)

    # transform prices
    price_records = transform_prices(prices_payload)

    print("Price records:", len(price_records))

    # load raw generation
    generation_payload, _ = load_raw("generation", "de", day)

    # check generation metadata
    generation_metadata = validate_dataset_metadata(
        generation_payload, "generation", "de"
    )
    print("Generation metadata:", generation_metadata)

    # check daily coverage
    generation_quality = validate_daily_coverage(
        generation_payload,
        day
    )

    print("Generation coverage:", generation_quality)

    # transform generation
    generation_records = transform_generation(generation_payload)

    print("Generation records:", len(generation_records))
