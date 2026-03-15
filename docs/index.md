# Project Documentation Index

## Project Overview

- **Project:** GnuCash-Dashboard
- **Type:** monolith
- **Primary Language:** Python + TypeScript
- **Architecture:** Ports & Adapters (hexagonal)

## Quick Reference

- **Tech Stack:** Python 3.11, FastAPI, React, TypeScript, SQLAlchemy (<2.0), PostgreSQL
- **Entry Point (API):** `src/adapters/interface/http_api/main.py`
- **Entry Point (Frontend):** `frontend/src/main.tsx`
- **Entry Point (DI):** `src/infrastructure/container.py`

## Generated Documentation

- [Project Overview](./project-overview.md)
- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Critical Folders Summary](./critical-folders-summary.md)
- [Component Inventory](./component-inventory.md)
- [Development Guide](./development-guide.md)
- [Deployment Configuration](./deployment-configuration.md)
- [API Contracts - Main](./api-contracts-main.md)
- [Data Models - Main](./data-models-main.md)
- [Comprehensive Analysis - Main](./comprehensive-analysis-main.md)
- [Project Scan State](./project-scan-report.json)

## Existing Documentation

- [Repository README](../README.md)

## Getting Started

1. Set `GNUCASH_DB_URL` and `ANALYTICS_DB_URL` (or create a local `.env`).
2. Run API: `uv run uvicorn src.adapters.interface.http_api.main:app --host 127.0.0.1 --port 8000 --reload`
3. Run frontend in `frontend/`: `pnpm dev` (or `npm run dev`)
4. If needed, sync analytics tables:
   - `uv run python -m src.adapters.sync_gnucash_analytics_cli`
   - `uv run python -m src.adapters.sync_accounts_cli`
