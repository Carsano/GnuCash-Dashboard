# Project Parts Metadata (Initial Scan)

## Parts

### `main`

- **Root path:** `{project-root}` (`/Users/damien/Documents/Dev/GnuCash-Dashboard`)
- **Repository type:** `monolith`
- **Project type (documentation requirements):** `backend`
- **Key tech signals:**
  - `streamlit` + `plotly` (UI adapter in `src/adapters/interface/streamlit/`)
  - `sqlalchemy<2.0`, `psycopg`, `psycopg2` (Postgres persistence)
  - `pytest` + `pytest-cov` (tests)

## Classification Summary

- **Overall:** Monolith backend service with a Streamlit UI adapter and CLI adapters, following ports-and-adapters layering.

