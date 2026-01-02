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
   - optional: set `GNUCASH_BACKEND=piecash` and `PIECASH_FILE=/path/to/book.gnucash` when switching to piecash (adapter TODO).
4. **Schedule synchronization**:
   - run `uv run python sync_gnucash.py` via cron/systemd or GitHub Actions to refresh analytics tables.

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

Use the SQLAlchemy backend by default (`GNUCASH_BACKEND=sqlalchemy`). To prepare a piecash migration:

- set `GNUCASH_BACKEND=piecash`
- set `PIECASH_FILE=/absolute/path/to/book.gnucash`

The Streamlit front end stays unchanged; only the backend selector changes.

## Immediate Roadmap

- [ ] Add ETL dependencies (`sqlalchemy`, `asyncpg`, `pandas`).
- [ ] Write `sync_gnucash.py` to copy/transform data between the GnuCash schema and the analytics schema, backed by fixtures exported from Postgres.
- [ ] Deploy local PostgreSQL via `docker compose` and ship the schema.
- [ ] Build first Streamlit visualizations and connect the database.
- [ ] Document security (env vars, optional encryption).

## Suggested Project Structure

Below is the folder layout to keep hexagonal boundaries explicit while hosting Streamlit, ETL, and database adapters:

```code
personal_finance_dashboard/
├── app.py
├── pyproject.toml
├── README.md
├── src/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── commodity.py
│   │   │   └── budget.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── account_repository.py
│   │   │   ├── transaction_repository.py
│   │   │   └── budget_repository.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── balance_service.py
│   │   │   ├── cashflow_service.py
│   │   │   └── kpi_service.py
│   │   └── value_objects.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── ports/
│   │   │   ├── __init__.py
│   │   │   ├── account_port.py
│   │   │   ├── transaction_port.py
│   │   │   └── dashboard_port.py
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── get_dashboard_kpis.py
│   │   │   ├── get_expenses_by_category.py
│   │   │   └── get_cashflow_timeseries.py
│   │   └── dto/
│   │       ├── __init__.py
│   │       └── dashboard_dto.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── connection.py
│   │   │   └── migrations/
│   │   ├── orm/
│   │   │   ├── __init__.py
│   │   │   ├── account_table.py
│   │   │   ├── transaction_table.py
│   │   │   └── splits_table.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── postgres_account_repository.py
│   │   │   └── postgres_transaction_repository.py
│   │   └── gnucash/
│   │       ├── __init__.py
│   │       └── schema_mapping.py
│   ├── interface/
│   │   ├── __init__.py
│   │   ├── streamlit/
│   │   │   ├── __init__.py
│   │   │   ├── app.py
│   │   │   ├── pages/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dashboard.py
│   │   │   │   ├── cashflow.py
│   │   │   │   └── categories.py
│   │   │   └── components.py
│   │   └── cli/
│   │       ├── __init__.py
│   │       └── export_csv.py
│   └── config/
│       ├── __init__.py
│       ├── settings.py
│       └── logging_conf.py
├── tests/
│   ├── __init__.py
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interface/
└── .env.example
```

This split makes each layer’s responsibility explicit: the domain layer stays pure; application orchestrates use cases and ports; infrastructure houses secondary adapters (PostgreSQL, ORM, GnuCash mappings); interface hosts primary adapters such as Streamlit and CLI tooling. Tests mirror the production layout for focused coverage.

Ports (interfaces) reside under `personal_finance/application/ports/`. Each port defines the contract that infrastructure adapters must satisfy—e.g., `account_port.py` for repository operations or `dashboard_port.py` for data needed by Streamlit—so the use cases can remain framework-agnostic.
