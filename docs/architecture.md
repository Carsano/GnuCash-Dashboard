# Architecture

## Executive Summary

GnuCash-Dashboard provides:

- a FastAPI HTTP API for financial and diagnostics data,
- a React frontend consuming `/api/v1/*`,
- a set of CLI tools for syncing/mirroring GnuCash tables into an analytics schema,
- optional alternate backends for reading data (`sqlalchemy`, `analytics`, `piecash`).

The codebase follows a ports-and-adapters (hexagonal) structure: adapters call application use cases, which depend on port protocols, implemented by infrastructure adapters.

## Technology Stack

- Python 3.11, `uv`
- FastAPI + Uvicorn (HTTP API)
- React + Vite + TypeScript (frontend)
- SQLAlchemy (<2.0) + Postgres drivers (`psycopg`, `psycopg2`)
- pytest + pytest-cov

## Architecture Pattern

- **Adapters** (`src/adapters/`): HTTP API + CLIs.
- **Application** (`src/application/use_cases/`): orchestrates use cases; returns DTOs for API consumption.
- **Ports** (`src/application/ports/`): Protocols defining boundary contracts (DB, repos, sync).
- **Infrastructure** (`src/infrastructure/`): concrete SQLAlchemy repositories, engine creation, backend selection, DI container.
- **Domain** (`src/domain/`): immutable dataclasses and domain services/policies.

## Data Architecture

- **Source DB:** GnuCash schema in Postgres (read via SQL queries).
- **Analytics DB/schema:** either mirrored tables (sync jobs) or precomputed views (`ANALYTICS_READ_MODE=views`).

Sync strategy highlights:

- `SyncGnuCashAnalyticsUseCase`: creates/truncates analytics mirror tables and bulk-copies rows.
- `SyncAccountsUseCase`: populates `accounts_dim` (truncate + reload).

## API Design

- HTTP API routes are implemented in `src/adapters/interface/http_api/router.py`.
- Primary interfaces are:
  - FastAPI HTTP endpoints,
  - React frontend (via HTTP calls),
  - CLI entry points,
  - database schema and views/tables.

## Component Overview

- HTTP API adapter: `src/adapters/interface/http_api/`
- Frontend app: `frontend/src/`

## Source Tree

See `docs/source-tree-analysis.md`.

## Development Workflow

See `docs/development-guide.md`.

## Deployment Architecture

See `docs/deployment-configuration.md`.

## Testing Strategy

- Unit/contract tests across layers under `tests/`.
- Repository behavior is validated via stubs/mocks; ordering is typically normalized (sorted) for deterministic assertions.
