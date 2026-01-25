# API Contracts (`main`)

## Summary

- No HTTP/REST API surface was detected in this repository (no FastAPI/Flask/Django routes).
- Primary interaction surfaces are:
  - Streamlit UI (human-facing).
  - CLI entry points (ops/sync tools).
  - PostgreSQL database access (SQL queries via SQLAlchemy).

## HTTP Endpoints

- **Not detected.**

If an HTTP API is planned but not yet implemented, the best starting point would be to define an OpenAPI contract and introduce an adapter (e.g., FastAPI) that calls existing `src/application/use_cases/*` methods.

## CLI Interfaces

These are Python modules intended to be executed as modules:

- `src.adapters.test_db_connection` — smoke test DB connectivity.
- `src.adapters.sync_gnucash_analytics_cli` — mirror core GnuCash tables into the analytics DB.
- `src.adapters.sync_accounts_cli` — sync the accounts dimension into `accounts_dim`.
- `src.adapters.compare_backends_cli` — sanity-check SQLAlchemy vs PieCash backends.

Typical invocation pattern (as documented in `README.md`):

- `uv run python -m <module>`

## Streamlit UI Surface

Entry point:

- `src.adapters.interface.streamlit.app` (`uv run python -m streamlit run src/adapters/interface/streamlit/app.py`)

Pages referenced in `README.md` / wiring:

- Dashboard
- Accounts
- Cashflow
- Budget
- Diagnostics

## Database “Contracts”

Database inputs are the effective “API” for this app. Key inputs/controls:

- `GNUCASH_DB_URL`: SQLAlchemy Postgres URL for the GnuCash source.
- `ANALYTICS_DB_URL`: SQLAlchemy Postgres URL for the analytics layer.
- `GNUCASH_BACKEND`: `sqlalchemy` (default), `analytics`, or `piecash`.
- `ANALYTICS_READ_MODE`: `tables` (default) or `views`.

