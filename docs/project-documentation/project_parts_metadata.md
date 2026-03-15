# Project Parts Metadata (Initial Scan)

## Parts

### `main`

- **Root path:** `{project-root}` (`/Users/damien/Documents/Dev/GnuCash-Dashboard`)
- **Repository type:** `monolith`
- **Project type (documentation requirements):** `backend`
- **Key tech signals:**
  - FastAPI HTTP adapter (`src/adapters/interface/http_api/`)
  - React frontend (`frontend/`)
  - `sqlalchemy<2.0`, `psycopg`, `psycopg2` (Postgres persistence)
  - `pytest` + `pytest-cov` (tests)

## Classification Summary

- **Overall:** Monolith service with FastAPI API adapter, React frontend, and CLI adapters, following ports-and-adapters layering.
