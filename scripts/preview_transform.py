
from energy_platform.raw_storage import load_raw
from energy_platform.transform import (
    transform_generation,
    transform_prices,
)


# dates to transform
DAYS = [
    "2026-09-01",
    "2026-09-02",
]


for day in DAYS:
    print(f"\n--- Date: {day} ---")

    # load raw prices
    prices_payload, _ = load_raw("prices", "DE-LU", day)

    # transform prices
    price_records = transform_prices(prices_payload)

    print("\nPrice records:", len(price_records))

    if price_records:
        print("First price record:", price_records[0])

    # load raw generation
    generation_payload, _ = load_raw("generation", "de", day)

    # transform generation
    generation_records = transform_generation(generation_payload)

    print("\nGeneration records:", len(generation_records))

    if generation_records:
        print("First generation record:", generation_records[0])
