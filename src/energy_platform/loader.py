
# price upsert query
PRICE_UPSERT_SQL = """
INSERT INTO public.electricity_prices (
    bidding_zone,
    timestamp_utc,
    price_eur_mwh,
    interval_minutes
)
VALUES (
    %(bidding_zone)s,
    %(timestamp_utc)s,
    %(price_eur_mwh)s,
    %(interval_minutes)s
)
ON CONFLICT (bidding_zone, timestamp_utc)
DO UPDATE SET
    price_eur_mwh = EXCLUDED.price_eur_mwh,
    interval_minutes = EXCLUDED.interval_minutes;
"""


def load_prices(conn, records):
    # skip empty batches
    if not records:
        return 0

    # insert or update records
    with conn.cursor() as cur:
        cur.executemany(PRICE_UPSERT_SQL, records)

    return len(records)

# generation upsert query
GENERATION_UPSERT_SQL = """
INSERT INTO public.electricity_generation (
    country,
    timestamp_utc,
    technology,
    power_mw,
    interval_minutes
)
VALUES (
    %(country)s,
    %(timestamp_utc)s,
    %(technology)s,
    %(power_mw)s,
    %(interval_minutes)s
)
ON CONFLICT (country, timestamp_utc, technology)
DO UPDATE SET
    power_mw = EXCLUDED.power_mw,
    interval_minutes = EXCLUDED.interval_minutes;
"""


def load_generation(conn, records):
    # skip empty batches
    if not records:
        return 0

    # insert or update records
    with conn.cursor() as cur:
        cur.executemany(GENERATION_UPSERT_SQL, records)

    return len(records)
