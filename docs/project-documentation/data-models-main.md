# Data Models (`main`)

## Summary

This project does not define ORM “models” as Python classes. Instead, it models data through:

- **Typed domain DTOs** (`dataclasses`) used across use-cases and adapters.
- **Database schemas** living in PostgreSQL (GnuCash source + analytics mirror), accessed via SQL queries.
- **Analytics mirror tables** created/managed by sync use-cases (lightweight DDL in Python).

## Domain DTOs (Python)

Key dataclasses (non-exhaustive):

- Accounts
  - `src.domain.models.accounts.AccountDTO`
  - `src.domain.models.accounts.AccountBalanceRow`
  - `src.domain.models.accounts.AccountBalanceDTO`
- GnuCash / analytics rows
  - `src.domain.models.gnucash_rows.NetWorthBalanceRow`
  - `src.domain.models.gnucash_rows.AssetCategoryBalanceRow`
  - `src.domain.models.gnucash_rows.PriceRow`
  - `src.domain.models.gnucash_rows.CashflowRow`
- Aggregates for UI
  - `src.domain.models.finance.NetWorthSummary`
  - `src.domain.models.finance.AssetCategoryBreakdown`
  - `src.domain.models.finance.CashflowView`

## Database Schemas

### GnuCash source (PostgreSQL)

Accessed read-only via SQL queries in repositories such as:

- `src/infrastructure/gnucash_repository.py` (tables: `accounts`, `commodities`, `splits`, `transactions`, `prices`, …)

### Analytics schema (PostgreSQL)

Two modes (selected by `ANALYTICS_READ_MODE`):

- **tables** (default): read analytics mirror tables created by sync jobs
  - Examples:
    - `accounts` (mirror)
    - `commodities` (mirror)
    - `splits` (mirror)
    - `transactions` (mirror)
    - `prices` (mirror)
    - `accounts_dim` (dimension table for UI)
- **views**: read from precomputed views (expected names in `README.md`)
  - Examples:
    - `vw_currency_lookup`
    - `vw_net_worth_balances`
    - `vw_asset_category_balances`
    - `vw_latest_prices`

## “Migration” Strategy

- No Alembic migrations were detected (`migrations/` exists but is empty).
- Schema evolution appears to be handled via:
  - analytics sync job(s) creating tables if missing (`CREATE TABLE IF NOT EXISTS …`),
  - optional column add for analytics transactions (`currency_guid`) during sync.

