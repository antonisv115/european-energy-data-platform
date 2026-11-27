
import os
from datetime import datetime, timezone
from decimal import Decimal

import psycopg
import pytest

from energy_platform.db import get_connection
from energy_platform.loader import load_generation, load_prices


# run only when explicitly enabled
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Requires local PostgreSQL",
)


def test_real_price_upsert():
    # prepare test records
    timestamp = datetime(2099, 1, 1, tzinfo=timezone.utc)

    record = {
        "bidding_zone": "TEST-UPSERT-STEP11",
        "timestamp_utc": timestamp,
        "price_eur_mwh": Decimal("50.00"),
        "interval_minutes": 15,
    }

    updated_record = {
        **record,
        "price_eur_mwh": Decimal("99.25"),
    }

    conn = get_connection()

    try:
        # insert then update same key
        load_prices(conn, [record])
        load_prices(conn, [updated_record])

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*), MAX(price_eur_mwh)
                FROM public.electricity_prices
                WHERE bidding_zone = %s
                  AND timestamp_utc = %s
                """,
                (record["bidding_zone"], timestamp),
            )

            count, price = cur.fetchone()

        assert count == 1
        assert price == Decimal("99.250")

    finally:
        # discard all test changes
        conn.rollback()
        conn.close()


def test_real_transaction_rollback():
    # prepare test records
    timestamp = datetime(2099, 1, 2, tzinfo=timezone.utc)
    test_zone = "TEST-ROLLBACK-STEP11"

    price_record = {
        "bidding_zone": test_zone,
        "timestamp_utc": timestamp,
        "price_eur_mwh": Decimal("50.00"),
        "interval_minutes": 15,
    }

    generation_record = {
        "country": "test",
        "timestamp_utc": timestamp,
        "technology": "solar",
        "power_mw": Decimal("100.00"),
        "interval_minutes": 0,
    }

    # generation violates the interval constraint
    with pytest.raises(psycopg.errors.CheckViolation):
        with get_connection() as conn:
            load_prices(conn, [price_record])
            load_generation(conn, [generation_record])

    # verify that price insert was rolled back
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM public.electricity_prices
                WHERE bidding_zone = %s
                  AND timestamp_utc = %s
                """,
                (test_zone, timestamp),
            )

            count = cur.fetchone()[0]

    assert count == 0
