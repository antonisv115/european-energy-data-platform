
import json

import pytest

from energy_platform import raw_storage


@pytest.fixture
def sample_raw(tmp_path, monkeypatch):
    # use temporary storage
    monkeypatch.setattr(raw_storage, "RAW_DIR", tmp_path)

    # sample api response
    payload = {
        "schema_version": "2.0",
        "series": [{"id": "day_ahead_price"}],
        "data": [
            {
                "timestamp": "2026-09-01T00:00:00+02:00",
                "values": {"day_ahead_price": 163.91}
            }
        ]
    }

    path = raw_storage.save_raw(
        "prices",
        "DE-LU",
        "2026-09-01",
        payload,
        "https://example.com/api"
    )

    return path, payload


def test_save_and_load(sample_raw):
    path, expected = sample_raw

    # load saved data
    payload, metadata = raw_storage.load_raw(
        "prices", "DE-LU", "2026-09-01"
    )

    assert path.exists()
    assert payload == expected
    assert metadata["schema_version"] == "2.0"
    assert path.with_suffix(".metadata.json").exists()


def test_prevent_overwrite(sample_raw):
    # reject duplicate file
    with pytest.raises(FileExistsError):
        raw_storage.save_raw(
            "prices",
            "DE-LU",
            "2026-09-01",
            {"data": [], "series": []},
            "https://example.com/api"
        )


def test_corrupted_json(sample_raw):
    path, _ = sample_raw

    # simulate corrupted file
    path.write_text("invalid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        raw_storage.load_raw(
            "prices", "DE-LU", "2026-09-01"
        )


def test_missing_metadata(sample_raw):
    path, _ = sample_raw

    # remove metadata file
    path.with_suffix(".metadata.json").unlink()

    with pytest.raises(FileNotFoundError):
        raw_storage.load_raw(
            "prices", "DE-LU", "2026-09-01"
        )


def test_metadata_mismatch(sample_raw):
    path, _ = sample_raw

    # modify stored metadata
    metadata_path = path.with_suffix(".metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    metadata["area"] = "FR"

    metadata_path.write_text(
        json.dumps(metadata),
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Metadata mismatch"):
        raw_storage.load_raw(
            "prices", "DE-LU", "2026-09-01"
        )
