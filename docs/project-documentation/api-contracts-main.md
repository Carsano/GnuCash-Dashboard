# API Contracts (`main`)

## Summary

- HTTP API surface exists and is implemented with FastAPI.
- Primary interaction surfaces are:
  - HTTP API (`/api/v1/*`).
  - React UI (consumer of HTTP API).
  - CLI entry points (ops/sync tools).
  - PostgreSQL database access (SQL queries via SQLAlchemy).

## HTTP Endpoints

Routes are defined in `src/adapters/interface/http_api/router.py` with prefix `/api/v1`.

- `GET /health`
- `GET /meta`
- `POST /sync/analytics`
- `GET /accounts`
- `GET /accounts/tree`
- `GET /net-worth`
- `GET /account-balances`
- `GET /asset-category-breakdown`
- `GET /cashflow/asset-selection`
- `GET /cashflow`
- `GET /budgets`
- `GET /budget/applicability`
- `GET /budget/month-view`
- `GET /diagnostics/env`
- `GET /diagnostics/db`

## CLI Interfaces

These are Python modules intended to be executed as modules:

- `src.adapters.test_db_connection` — smoke test DB connectivity.
- `src.adapters.sync_gnucash_analytics_cli` — mirror core GnuCash tables into the analytics DB.
- `src.adapters.sync_accounts_cli` — sync the accounts dimension into `accounts_dim`.
- `src.adapters.compare_backends_cli` — sanity-check SQLAlchemy vs PieCash backends.

Typical invocation pattern (as documented in `README.md`):

- `uv run python -m <module>`

## Frontend Surface

- React app entry: `frontend/src/main.tsx`
- API query layer: `frontend/src/lib/api/queries.ts`

## Database “Contracts”

Database inputs are effective runtime contracts. Key inputs/controls:

- `GNUCASH_DB_URL`: SQLAlchemy Postgres URL for the GnuCash source.
- `ANALYTICS_DB_URL`: SQLAlchemy Postgres URL for the analytics layer.
- `GNUCASH_BACKEND`: `sqlalchemy` (default), `analytics`, or `piecash`.
- `ANALYTICS_READ_MODE`: `tables` (default) or `views`.
