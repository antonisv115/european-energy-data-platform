
from energy_platform.data_quality import (
    validate_daily_coverage,
    validate_dataset_metadata,
)
from energy_platform.db import get_connection
from energy_platform.loader import load_generation, load_prices
from energy_platform.raw_storage import load_raw
from energy_platform.transform import (
    transform_generation,
    transform_prices,
)


# dates to load
DAYS = ["2026-09-01", "2026-09-02"]


for day in DAYS:
    print(f"\n--- loading {day} ---")

    # load raw data
    prices, _ = load_raw("prices", "DE-LU", day)
    generation, _ = load_raw("generation", "de", day)

    # validate prices
    validate_dataset_metadata(prices, "prices", "DE-LU")
    validate_daily_coverage(prices, day)

    # validate generation
    validate_dataset_metadata(generation, "generation", "de")
    validate_daily_coverage(generation, day)

    # transform records
    price_records = transform_prices(prices)
    generation_records = transform_generation(generation)

    # load both datasets in one transaction
    with get_connection() as conn:
        price_count = load_prices(conn, price_records)
        generation_count = load_generation(conn, generation_records)

    print("Prices processed:", price_count)
    print("Generation processed:", generation_count)


# verify total rows
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM public.electricity_prices")
        total_prices = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM public.electricity_generation")
        total_generation = cur.fetchone()[0]

print("\nTotal price rows:", total_prices)
print("Total generation rows:", total_generation)
