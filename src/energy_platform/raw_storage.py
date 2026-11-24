
import json

from datetime import datetime, timezone
from pathlib import Path


# project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def get_raw_path(dataset, area, day):
    # build raw file path
    return RAW_DIR / dataset / f"{area}_{day}.json"


def save_raw(dataset, area, day, payload, source_url):
    path = get_raw_path(dataset, area, day)

    # create directories
    path.parent.mkdir(parents=True, exist_ok=True)

    # save complete json
    with path.open("x", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    # create download metadata
    metadata = {
        "dataset": dataset,
        "area": area,
        "day": day,
        "source_url": source_url,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "api_generated_at": payload.get("generated_at"),
        "schema_version": payload.get("schema_version")
    }

    metadata_path = path.with_suffix(".metadata.json")

    # save metadata
    with metadata_path.open("x", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    return path

def load_raw(dataset, area, day):
    path = get_raw_path(dataset, area, day)
    metadata_path = path.with_suffix(".metadata.json")

    # check metadata file
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing metadata: {metadata_path}")

    # read saved json
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    # read metadata
    with metadata_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    # check json structure
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("data"), list)
        or not isinstance(payload.get("series"), list)
    ):
        raise ValueError(f"Invalid raw data: {path}")

    # check dataset metadata
    if (
        metadata.get("dataset") != dataset
        or metadata.get("area") != area
        or metadata.get("day") != day
    ):
        raise ValueError(f"Metadata mismatch: {metadata_path}")

    # check schema version
    if metadata.get("schema_version") != payload.get("schema_version"):
        raise ValueError(f"Schema mismatch: {path}")

    return payload, metadata
