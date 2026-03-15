# Data Models (`main`)

## Summary

This project models data through:

- typed DTOs (`dataclasses`) in `src/domain/models/`,
- database schemas in PostgreSQL (GnuCash source + analytics mirror),
- lightweight DDL embedded in sync jobs for analytics tables.

## Domain DTOs (Examples)

- Accounts: `AccountDTO`, `AccountBalanceRow`, `AccountBalanceDTO`
- GnuCash rows: `NetWorthBalanceRow`, `AssetCategoryBalanceRow`, `CashflowRow`, `PriceRow`
- Aggregates: `NetWorthSummary`, `CashflowView`, `AssetCategoryBreakdown`

## Analytics Tables / Views

- **Tables mode** (`ANALYTICS_READ_MODE=tables`): created/filled by sync use cases.
- **Views mode** (`ANALYTICS_READ_MODE=views`): expects precomputed SQL views (see `README.md`).

