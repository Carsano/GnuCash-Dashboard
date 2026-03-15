# API Contracts (`main`)

## Summary

- HTTP API surface exists and is implemented with FastAPI.
- Primary interaction surfaces are:
  - HTTP API (`/api/v1/*`),
  - React UI (consumer of HTTP API),
  - CLI entry points (ops/sync tools),
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

- `src.adapters.test_db_connection`
- `src.adapters.sync_gnucash_analytics_cli`
- `src.adapters.sync_accounts_cli`
- `src.adapters.compare_backends_cli`

## Frontend/API Contract Surface

- Frontend API queries are implemented in `frontend/src/lib/api/queries.ts`.
- Development proxy forwards `/api/v1` from Vite to `http://127.0.0.1:8000`.

## Database “Contracts”

Database inputs are effective runtime contracts. Key inputs/controls:

- `GNUCASH_DB_URL`: SQLAlchemy Postgres URL for the GnuCash source.
- `ANALYTICS_DB_URL`: SQLAlchemy Postgres URL for the analytics layer.
- `GNUCASH_BACKEND`: `sqlalchemy` (default), `analytics`, or `piecash`.
- `ANALYTICS_READ_MODE`: `tables` (default) or `views`.
