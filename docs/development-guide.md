# Development Guide

## Prerequisites

- Python `>=3.11,<3.12` (repo pins `3.11`)
- `uv` installed
- PostgreSQL reachable for:
  - `GNUCASH_DB_URL` (source GnuCash DB/schema)
  - `ANALYTICS_DB_URL` (analytics DB/schema; can be the same DB)

## Install

```bash
uv sync
```

## Configure Environment

Create `.env` (optional) with:

- `GNUCASH_DB_URL=postgresql://...`
- `ANALYTICS_DB_URL=postgresql://...`
- `GNUCASH_BACKEND=sqlalchemy|analytics|piecash`
- `ANALYTICS_READ_MODE=tables|views`
- `PIECASH_FILE=/path/to/book.gnucash` (only for PieCash)

## Run (Streamlit)

```bash
uv run python -m streamlit run src/adapters/interface/streamlit/app.py
```

## Run (CLIs)

```bash
uv run python -m src.adapters.test_db_connection
uv run python -m src.adapters.sync_gnucash_analytics_cli
uv run python -m src.adapters.sync_accounts_cli
uv run python -m src.adapters.compare_backends_cli
```

## Tests

```bash
uv run pytest
```

