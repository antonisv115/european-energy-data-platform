
from energy_platform.api import fetch_dataset
from energy_platform.raw_storage import get_raw_path, load_raw, save_raw


# dataset configuration
DATASETS = {
    "prices": {
        "endpoint": "/v2/price",
        "area": "DE-LU",
        "area_param": "bzn"
    },
    "generation": {
        "endpoint": "/v2/public_power",
        "area": "de",
        "area_param": "country"
    }
}

# dates to download
DAYS = [
    "2026-09-01",
    "2026-09-02"
]

for day in DAYS:
    for dataset, config in DATASETS.items():
        area = config["area"]

        # check cached file
        raw_path = get_raw_path(dataset, area, day)

        if raw_path.exists():
            print("Using existing raw file:", raw_path)

        else:
            # build api parameters
            params = {
                config["area_param"]: area,
                "start": day,
                "end": day
            }

            # download dataset
            payload, source_url = fetch_dataset(
                config["endpoint"],
                params
            )

            # save raw data
            raw_path = save_raw(
                dataset,
                area,
                day,
                payload,
                source_url
            )

            print("Raw file saved:", raw_path)

        # verify saved dataset
        payload, metadata = load_raw(dataset, area, day)

        print("Dataset:", dataset)
        print("Date:", day)
        print("Schema version:", payload.get("schema_version"))
        print("Timestamps:", len(payload["data"]))
        print("Series:", len(payload["series"]))
        print()
