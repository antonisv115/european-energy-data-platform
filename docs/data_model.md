
# V1 Data Model

## Overview

The V1 data model stores electricity prices and generation data
from the Fraunhofer ISE Energy-Charts API.

Raw JSON responses are preserved separately in `data/raw/`.

## 1. Electricity Prices

Table: `electricity_prices`

| Column | PostgreSQL Type | Description |
|---|---|---|
| bidding_zone | TEXT | Electricity market zone |
| timestamp_utc | TIMESTAMPTZ | Delivery interval start |
| price_eur_mwh | NUMERIC(12,3) | Day-ahead electricity price |
| interval_minutes | SMALLINT | Interval duration |

Primary key: `(bidding_zone, timestamp_utc)`

## 2. Electricity Generation

Table: `electricity_generation`

| Column | PostgreSQL Type | Description |
|---|---|---|
| country | TEXT | Country code |
| timestamp_utc | TIMESTAMPTZ | Delivery interval start |
| technology | TEXT | Generation technology |
| power_mw | NUMERIC(14,3) | Electricity generation power |
| interval_minutes | SMALLINT | Interval duration |

Primary key: `(country, timestamp_utc, technology)`

## 3. Generation Technologies

The V1 pipeline includes:

- solar
- wind_onshore
- wind_offshore
- biomass
- geothermal
- hydro_run_of_river
- hydro_water_reservoir
- hydro_pumped_storage
- fossil_gas
- fossil_oil
- fossil_hard_coal
- fossil_brown_coal_lignite
- fossil_coal_derived_gas
- waste
- others

Consumption, electricity trading, load, residual load,
and renewable share metrics are excluded from the generation table.

## 4. Data Quality Rules

- Required fields must not be null.
- Duplicate primary keys are not allowed.
- Timestamps must represent UTC instants.
- Interval duration must be positive.
- Price values may be negative.
- Generation values may be zero.
- Generation values must be validated against series semantics.
- Missing measurements must not be silently replaced with zero.
- Time interval continuity must be checked.
- Raw JSON data must remain unchanged.

## 5. Timezone Handling

Source timezone: Europe/Berlin.

Database timestamps: TIMESTAMPTZ, handled in UTC.

Days affected by daylight saving time may contain
92 or 100 fifteen-minute intervals instead of 96.

## 6. Geographic Scope

Price data uses the DE-LU bidding zone.

Generation data uses Germany (de).

These geographic scopes are not identical and must be
considered when comparing prices and generation.

## 7. Future Extensions

- pipeline execution metadata
- data quality monitoring
- incremental loading
- additional countries and bidding zones
- analytical models and dashboards

## 8. Database Constraints

### Electricity Prices

- Primary key: (bidding_zone, timestamp_utc)
- price_eur_mwh: NOT NULL
- interval_minutes: NOT NULL
- interval_minutes: CHECK > 0
- Negative electricity prices are allowed.

### Electricity Generation

- Primary key: (country, timestamp_utc, technology)
- power_mw: NOT NULL
- interval_minutes: NOT NULL
- interval_minutes: CHECK > 0
- Zero generation values are allowed.
- Negative generation values require investigation.

## 9. Validation Responsibilities

### Python Validation

The transformation layer will check:

- Required API fields and schema version
- Source units and time resolution
- Missing and invalid measurements
- Duplicate timestamps and time gaps
- UTC timestamp conversion
- Allowed generation technologies
- Generation values requiring investigation

### PostgreSQL Validation

The database will enforce:

- Required columns
- Correct data types
- Composite primary keys
- Positive interval duration

## 10. Table Relationships

The V1 model contains two independent fact tables:

- electricity_prices
- electricity_generation

No foreign key relationship is required between them.

The tables may be joined by timestamp for analytical purposes.

Price and generation data have different geographic scopes.
This limitation must be considered in analytical queries.

## 11. Loading Strategy

Loading will use PostgreSQL upserts to support idempotency.

Existing records will be identified by their primary keys.

Repeated pipeline executions must not create duplicate rows.

## 12. Indexing Strategy

Primary keys automatically create unique indexes.

Additional indexes will be considered based on actual SQL queries.

A potential future index for generation analytics is:

(country, technology, timestamp_utc)

## 13. Operational Metadata

A pipeline_runs table may be introduced when implementing
end-to-end pipeline orchestration.

It can track execution time, status, processed records,
and errors.

## 14. Implementation Notes

- Source timestamps will be converted to UTC.
- Database sessions should use UTC for consistent display.
- Raw JSON files will remain unchanged.
- Database tables will be created in Step 9.
- Transformation and loading logic will be implemented separately.
