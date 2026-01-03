# Personal Finances Dashboard

This repository is a starting point for building a Streamlit dashboard connected to GnuCash. The setup already uses PostgreSQL as the primary GnuCash backend, so the work mainly consists in reading that database, shaping analytical tables or views, and serving them inside the dashboard.

## Planned Architecture

1. **Source**: GnuCash PostgreSQL database (tables `accounts`, `transactions`, `splits`, etc.).
2. **Python ETL**:
   - read live data through `sqlalchemy` or `asyncpg`;
   - enrich entries (custom categories, budget tags, FX normalization);
   - persist curated data into a dedicated analytics schema (same cluster or separate DB).
3. **Warehouse**: PostgreSQL analytical schema with modeled tables `dim_accounts`, `fact_transactions`, `fact_budgets`.
4. **Dashboard**: Streamlit app showing balance sheet, cashflow, budgets, alerts.

```nocode
GnuCash (PostgreSQL) -> Transformation job -> Analytics schema/views -> Streamlit
```

## Target Features

- Daily sync from GnuCash with anomaly detection.
- Aggregated datasets (income, expenses, cashflow, savings).
- Interactive visuals (line charts, heatmaps, goals vs actuals).
- Budget alerts (email or notification) when thresholds are exceeded.
- CSV/Parquet exports for offline analysis.

## Tech Stack

- Python 3.13 (managed via `uv`, `pyenv`, or `rye`).
- Streamlit for the front end.
- PostgreSQL 15+ for both GnuCash and analytics layers.
- Proposed libraries: `pandas`, `sqlalchemy`, `asyncpg`, `plotly`.
- Supporting tools: `docker compose` (local Postgres), `make` or `uv run` scripts.

## Quick Start

1. **Install dependencies**:

   ```bash
   uv sync
   ```

2. **Launch the Streamlit skeleton** (placeholder):

   ```bash
   uv run streamlit run main.py
   ```

3. **Configure PostgreSQL access**:
   - create a read-only role pointing to the existing GnuCash database;
   - create a separate schema/database (`finances_analytics`) for derived tables;
   - set environment variables `GNUCASH_DB_URL` and `ANALYTICS_DB_URL` (can be the same DB with two schemas).
   - optional: set `GNUCASH_BACKEND=piecash` and `PIECASH_FILE=/path/to/book.gnucash` to use piecash from a local file.
   - optional: for piecash + PostgreSQL, set `PIECASH_FILE=postgresql://user:pass@host/dbname` (requires `piecash[postgres]`).
4. **Schedule synchronization**:
   - run `uv run python sync_gnucash.py` via cron/systemd or GitHub Actions to refresh analytics tables.

## Usage

### Without piecash (SQL-only)

- Install dependencies: `uv sync`
- Use the SQL backend (default): `GNUCASH_BACKEND=sqlalchemy`
- Sync analytics tables: `uv run python -m src.adapters.sync_gnucash_analytics_cli`
- Run the dashboard against analytics: `uv run python -m streamlit run src/adapters/interface/streamlit/app.py`

### With piecash (optional)

- Install dependencies: `uv sync --extra piecash`
- Use a local book: `GNUCASH_BACKEND=piecash` + `PIECASH_FILE=/path/to/book.gnucash`
- Or use Postgres: `PIECASH_FILE=postgresql://user:pass@host/dbname`
- Run the sync: `uv run python -m src.adapters.sync_gnucash_analytics_cli`
- Run the dashboard against analytics: `uv run python -m streamlit run src/adapters/interface/streamlit/app.py`

### Analytics Views (optional)

If you want the dashboard to read from precomputed analytics views instead of raw
tables, set:

```
ANALYTICS_READ_MODE=views
```

Expected views (analytics DB):
- `vw_currency_lookup(guid, mnemonic, namespace)`
- `vw_net_worth_balances(account_type, commodity_guid, mnemonic, namespace, balance, post_date)`
- `vw_asset_category_balances(account_type, commodity_guid, mnemonic, namespace, actif_category, actif_subcategory, balance, actif_root_name, post_date)`
- `vw_latest_prices(commodity_guid, currency_guid, value_num, value_denom, date)`

- Sync accounts: `uv run python -m src.adapters.sync_accounts_cli`
- Sync GnuCash tables into analytics: `uv run python -m src.adapters.sync_gnucash_analytics_cli`
- Compare SQL vs piecash: `uv run python -m src.adapters.compare_backends_cli`

## Shaping GnuCash Data

1. Connect directly to the GnuCash PostgreSQL backend using `sqlalchemy.create_engine(GNUCASH_DB_URL)`.
2. Copy or transform the canonical tables into analytics-friendly tables (e.g., `fact_transactions`, `fact_splits`).
3. Add derived columns such as hierarchical categories, budget tags, normalized currency, or counterparty metadata.
4. Upsert into the analytics schema using immutable identifiers like the GnuCash `guid`.
5. Build materialized views for dashboard KPIs (`vw_monthly_cashflow`, `vw_budget_gap`, `vw_alerts`).

## Streamlit Dashboard

- Read Postgres views via `sqlalchemy` + `pandas`.
- Cache DataFrames with `st.cache_data` to avoid overload.
- Offer one page per theme: `Overview`, `Cashflow`, `Budgets`, `Alerts`.
- Add a control panel (period selection, accounts, currency).

## Switching Backends

Use the SQLAlchemy backend by default (`GNUCASH_BACKEND=sqlalchemy`). To switch the dashboard to analytics:

- run `uv run python -m src.adapters.sync_gnucash_analytics_cli`
- run the dashboard (it reads analytics tables by default)

To prepare a piecash migration:

- set `GNUCASH_BACKEND=piecash`
- set `PIECASH_FILE=/absolute/path/to/book.gnucash`
- or use `PIECASH_FILE=postgresql://user:pass@host/dbname` for a Postgres-backed book

The Streamlit front end stays unchanged; only the backend selector changes.

## Migration Checklist

- Install `piecash` (optional) and ensure the GnuCash book is readable locally.
- For Postgres-backed books, install the optional extra `piecash[postgres]`.
- Set `GNUCASH_BACKEND=piecash` and `PIECASH_FILE` to the book path or URI.
- Run the contract tests (`uv run pytest tests/application/test_gnucash_repository_contracts.py`).
- Compare logged source summaries (balances/prices) between SQL and piecash runs.
- Validate dashboards and sync outputs on a staging dataset before switching.

## Immediate Roadmap

- [ ] Add ETL dependencies (`sqlalchemy`, `asyncpg`, `pandas`).
- [ ] Write `sync_gnucash.py` to copy/transform data between the GnuCash schema and the analytics schema, backed by fixtures exported from Postgres.
- [ ] Deploy local PostgreSQL via `docker compose` and ship the schema.
- [ ] Build first Streamlit visualizations and connect the database.
- [ ] Document security (env vars, optional encryption).

## Suggested Project Structure

Current layout (hexagonal):

```code
src/
├── domain/
│   ├── constants.py
│   ├── models/
│   ├── policies/
│   └── services/
├── application/
│   ├── ports/
│   └── use_cases/
├── infrastructure/
├── adapters/
│   └── interface/
└── utils/
tests/
```

This split keeps each layer explicit:
- `domain/` is pure business logic and models (no SQL/IO).
- `application/` orchestrates use cases and defines ports.
- `infrastructure/` implements the ports (SQLAlchemy, piecash, ETL).
- `adapters/` wires UI/CLI to the application layer.
