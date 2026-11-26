
-- electricity prices
CREATE TABLE public.electricity_prices (
    bidding_zone TEXT NOT NULL,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    price_eur_mwh NUMERIC(12, 3) NOT NULL,
    interval_minutes SMALLINT NOT NULL,

    CONSTRAINT electricity_prices_pkey
        PRIMARY KEY (bidding_zone, timestamp_utc),

    CONSTRAINT electricity_prices_positive_interval
        CHECK (interval_minutes > 0)
);


-- electricity generation
CREATE TABLE public.electricity_generation (
    country TEXT NOT NULL,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    technology TEXT NOT NULL,
    power_mw NUMERIC(14, 3) NOT NULL,
    interval_minutes SMALLINT NOT NULL,

    CONSTRAINT electricity_generation_pkey
        PRIMARY KEY (country, timestamp_utc, technology),

    CONSTRAINT electricity_generation_positive_interval
        CHECK (interval_minutes > 0)
);
