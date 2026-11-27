
from unittest.mock import MagicMock

import pytest

from energy_platform import pipeline


def test_date_range():
    # check inclusive date range
    days = list(pipeline.iter_days("2026-09-01", "2026-09-03"))

    assert days == [
        "2026-09-01",
        "2026-09-02",
        "2026-09-03",
    ]


@pytest.mark.parametrize(
    "start,end",
    [
        ("2026-09-03", "2026-09-01"),
        ("2026-02-30", "2026-03-01"),
        ("20260901", "2026-09-03"),
    ],
)
def test_invalid_dates(start, end):
    # reject invalid ranges
    with pytest.raises(ValueError):
        list(pipeline.iter_days(start, end))


def test_cached_raw(monkeypatch, tmp_path):
    # create existing raw file
    path = tmp_path / "cached.json"
    path.write_text("{}", encoding="utf-8")

    payload = {"sample": "cached"}

    read_mock = MagicMock(return_value=(payload, {}))
    fetch_mock = MagicMock()

    monkeypatch.setattr(pipeline, "get_raw_path", lambda *args: path)
    monkeypatch.setattr(pipeline, "load_raw", read_mock)
    monkeypatch.setattr(pipeline, "fetch_dataset", fetch_mock)

    result, source = pipeline.load_or_fetch_raw(
        "prices", "2026-09-01"
    )

    assert result == payload
    assert source == "cache"

    read_mock.assert_called_once_with(
        "prices", "DE-LU", "2026-09-01"
    )
    fetch_mock.assert_not_called()


def test_fetch_missing_raw(monkeypatch, tmp_path):
    # simulate missing raw file
    path = tmp_path / "missing.json"
    payload = {"sample": "downloaded"}

    fetch_mock = MagicMock(
        return_value=(payload, "https://example.test/api")
    )
    save_mock = MagicMock()
    read_mock = MagicMock(return_value=(payload, {}))

    monkeypatch.setattr(pipeline, "get_raw_path", lambda *args: path)
    monkeypatch.setattr(pipeline, "fetch_dataset", fetch_mock)
    monkeypatch.setattr(pipeline, "save_raw", save_mock)
    monkeypatch.setattr(pipeline, "load_raw", read_mock)

    result, source = pipeline.load_or_fetch_raw(
        "generation", "2026-09-03"
    )

    assert result == payload
    assert source == "api"

    fetch_mock.assert_called_once_with(
        "/v2/public_power",
        {
            "country": "de",
            "start": "2026-09-03",
            "end": "2026-09-03",
        },
    )

    save_mock.assert_called_once_with(
        "generation",
        "de",
        "2026-09-03",
        payload,
        "https://example.test/api",
    )

    read_mock.assert_called_once()


@pytest.fixture
def mock_processing(monkeypatch):
    # replace external dependencies
    def fake_raw(dataset, day):
        return {"dataset": dataset}, "cache"

    monkeypatch.setattr(
        pipeline, "load_or_fetch_raw", fake_raw
    )

    metadata_mock = MagicMock()
    coverage_mock = MagicMock()

    monkeypatch.setattr(
        pipeline, "validate_dataset_metadata", metadata_mock
    )
    monkeypatch.setattr(
        pipeline, "validate_daily_coverage", coverage_mock
    )

    monkeypatch.setattr(
        pipeline, "transform_prices",
        lambda payload: [{"price": 10}],
    )

    monkeypatch.setattr(
        pipeline, "transform_generation",
        lambda payload: [{"power": 20}, {"power": 30}],
    )

    connection_context = MagicMock()
    connection = connection_context.__enter__.return_value

    monkeypatch.setattr(
        pipeline,
        "get_connection",
        MagicMock(return_value=connection_context),
    )

    price_loader = MagicMock(return_value=1)
    generation_loader = MagicMock(return_value=2)

    monkeypatch.setattr(pipeline, "load_prices", price_loader)
    monkeypatch.setattr(
        pipeline, "load_generation", generation_loader
    )

    return {
        "context": connection_context,
        "connection": connection,
        "metadata": metadata_mock,
        "coverage": coverage_mock,
        "prices": price_loader,
        "generation": generation_loader,
    }


def test_process_day_success(mock_processing):
    # check successful processing
    result = pipeline.process_day("2026-09-01")

    assert result["prices"] == 1
    assert result["generation"] == 2
    assert result["price_source"] == "cache"
    assert result["generation_source"] == "cache"

    mock_processing["prices"].assert_called_once()
    mock_processing["generation"].assert_called_once()

    mock_processing["context"].__exit__.assert_called_once_with(
        None, None, None
    )


def test_loading_failure(mock_processing):
    # simulate generation failure
    mock_processing["generation"].side_effect = RuntimeError(
        "generation failed"
    )

    with pytest.raises(RuntimeError, match="generation failed"):
        pipeline.process_day("2026-09-01")

    # verify error reaches transaction context
    exit_args = mock_processing["context"].__exit__.call_args.args

    assert exit_args[0] is RuntimeError
    mock_processing["prices"].assert_called_once()


def test_validation_failure(mock_processing):
    # stop before database loading
    mock_processing["metadata"].side_effect = ValueError(
        "invalid metadata"
    )

    with pytest.raises(ValueError, match="invalid metadata"):
        pipeline.process_day("2026-09-01")

    mock_processing["prices"].assert_not_called()
    mock_processing["generation"].assert_not_called()
    mock_processing["context"].__enter__.assert_not_called()
