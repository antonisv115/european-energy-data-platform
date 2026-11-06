# European Energy Data Platform

An end-to-end Data Engineering project using Python, PostgreSQL, and real European electricity market data.

## Project Goal

Build a reliable ETL pipeline that collects electricity market data from an external API, validates and transforms the data, and stores it in PostgreSQL for SQL analytics.

## Data Sources

Fraunhofer ISE Energy-Charts API:

- Day-ahead electricity prices (DE-LU bidding zone)
- Public net electricity generation (Germany)

## V1 Architecture

Energy-Charts API
→ Raw JSON Storage
→ Python Transformation & Validation
→ PostgreSQL
→ SQL Analytics

## Tech Stack

- Python 3.13
- PostgreSQL 18
- Requests
- Psycopg
- Pytest
- Git & GitHub

## Project Status

V1 — In development.

Development environment initialized. The ETL pipeline is not yet implemented.
