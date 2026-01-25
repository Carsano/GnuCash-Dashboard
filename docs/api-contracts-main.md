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

- `src.adapters.test_db_connection`
- `src.adapters.sync_gnucash_analytics_cli`
- `src.adapters.sync_accounts_cli`
- `src.adapters.compare_backends_cli`

## Streamlit UI Surface

- Entry point: `src.adapters.interface.streamlit.app`

