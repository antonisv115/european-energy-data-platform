
import argparse

from energy_platform.pipeline import iter_days, process_day


def main():
    # configure command line
    parser = argparse.ArgumentParser(
        description="Run the European energy ETL pipeline"
    )

    parser.add_argument(
        "--start",
        required=True,
        help="Start date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--end",
        required=True,
        help="End date in YYYY-MM-DD format",
    )

    args = parser.parse_args()

    # validate dates before loading
    days = list(iter_days(args.start, args.end))

    print(f"Processing {len(days)} day(s)")

    # run daily pipeline
    for day in days:
        print(f"\n--- {day} ---")

        result = process_day(day)

        print(
            f"Prices: {result['prices']} "
            f"(source: {result['price_source']})"
        )

        print(
            f"Generation: {result['generation']} "
            f"(source: {result['generation_source']})"
        )

        print("Day completed successfully")

    print("\nPipeline completed successfully")


if __name__ == "__main__":
    main()
