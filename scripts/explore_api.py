
import requests
from datetime import datetime, timedelta, timezone


# api settings
BASE_URL = "https://api.energy-charts.info"
START_DATE = "2026-09-01"
END_DATE = "2026-09-01"


def inspect_dataset(endpoint, params):
    url = BASE_URL + endpoint

    # send api request
    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    print("\nEndpoint:", endpoint)
    print("Request URL:", response.url)
    print("HTTP Status:", response.status_code)

    response.raise_for_status()

    # parse json response
    data = response.json()

    # show metadata
    print("Schema version:", data.get("schema_version"))
    print("Timezone:", data.get("timezone"))
    print("Unit:", data.get("unit"))
    print("Interval minutes:", data.get("interval_minutes"))

    # list available series
    series = data.get("series", [])

    print("\nNumber of series:", len(series))

    for item in series:
        print(
            item.get("id"),
            "|",
            item.get("name"),
            "| Unit:",
            item.get("unit") or data.get("unit")
        )

    # inspect data rows
    rows = data.get("data", [])

    print("\nNumber of timestamps:", len(rows))

    if rows:
        print("First timestamp:", rows[0].get("timestamp"))
        print("First values:", rows[0].get("values"))

    # convert timestamps to utc
    print("\n--- Timestamp Profiling ---")

    timestamps = [
        datetime.fromisoformat(row["timestamp"]).astimezone(timezone.utc)
        for row in rows
    ]

    # find duplicate timestamps
    unique_timestamps = sorted(set(timestamps))
    duplicates = len(timestamps) - len(unique_timestamps)

    print("Duplicate timestamps:", duplicates)

    if unique_timestamps:
        print("First UTC:", unique_timestamps[0])
        print("Last UTC:", unique_timestamps[-1])

        # check time gaps
        expected_interval = timedelta(minutes=data["interval_minutes"])
        unexpected_intervals = 0

        for previous, current in zip(
            unique_timestamps,
            unique_timestamps[1:]
        ):
            if current - previous != expected_interval:
                unexpected_intervals += 1

        print("Unexpected intervals:", unexpected_intervals)

    # inspect each series
    print("\n--- Series Profiling ---")

    for item in series:
        series_id = item["id"]

        # collect series values
        values = [
            row.get("values", {}).get(series_id)
            for row in rows
        ]

        # keep numeric values
        numbers = [
            value for value in values
            if isinstance(value, (int, float))
            and not isinstance(value, bool)
        ]

        # count missing and invalid values
        missing = sum(value is None for value in values)
        invalid = len(values) - len(numbers) - missing

        print("\nSeries:", series_id)
        print("Numeric values:", len(numbers))
        print("Missing values:", missing)
        print("Invalid values:", invalid)

        # calculate basic statistics
        if numbers:
            print("Minimum:", min(numbers))
            print("Maximum:", max(numbers))
            print("Negative values:", sum(v < 0 for v in numbers))
            print("Zero values:", sum(v == 0 for v in numbers))


# explore electricity prices
inspect_dataset(
    "/v2/price",
    {
        "bzn": "DE-LU",
        "start": START_DATE,
        "end": END_DATE
    }
)

# explore electricity generation
inspect_dataset(
    "/v2/public_power",
    {
        "country": "de",
        "start": START_DATE,
        "end": END_DATE
    }
)
