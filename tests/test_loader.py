
from unittest.mock import MagicMock

from energy_platform.loader import load_generation, load_prices


def test_empty_prices():
    # skip empty price batch
    conn = MagicMock()

    assert load_prices(conn, []) == 0
    conn.cursor.assert_not_called()


def test_empty_generation():
    # skip empty generation batch
    conn = MagicMock()

    assert load_generation(conn, []) == 0
    conn.cursor.assert_not_called()


def test_price_upsert():
    # check price sql execution
    conn = MagicMock()

    records = [{
        "bidding_zone": "DE-LU",
        "timestamp_utc": "2026-09-01T00:00:00+02:00",
        "price_eur_mwh": 163.91,
        "interval_minutes": 15,
    }]

    assert load_prices(conn, records) == 1

    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.executemany.assert_called_once()

    sql, params = cursor.executemany.call_args.args

    assert "ON CONFLICT (bidding_zone, timestamp_utc)" in sql
    assert params == records


def test_generation_upsert():
    # check generation sql execution
    conn = MagicMock()

    records = [{
        "country": "de",
        "timestamp_utc": "2026-09-01T00:00:00+02:00",
        "technology": "solar",
        "power_mw": 0.0,
        "interval_minutes": 15,
    }]

    assert load_generation(conn, records) == 1

    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.executemany.assert_called_once()

    sql, params = cursor.executemany.call_args.args

    assert "ON CONFLICT (country, timestamp_utc, technology)" in sql
    assert params == records
