# Comprehensive Analysis (`main`)

## Scope and Scan Notes

- **Scan level:** `exhaustive`
- **Repository type:** monolith
- **Project type:** backend + web frontend (FastAPI adapter + React UI + CLI adapters)

## Architecture and Data Flow (High Level)

1. **Adapters**
   - FastAPI HTTP adapter: `src/adapters/interface/http_api/` maps requests to application use cases.
   - CLI modules: `src/adapters/*.py` invoke use cases for sync/ops tasks.
   - React UI: `frontend/src/` fetches `/api/v1/*` endpoints.
2. **Application (Use Cases + Ports)**
   - Use cases live in `src/application/use_cases/` and depend on `src/application/ports/` (protocols).
3. **Infrastructure**
   - `src/infrastructure/container.py` is the composition root: builds adapters and chooses analytics read mode (`tables` vs `views`) and GnuCash backend (`sqlalchemy|analytics|piecash`).
   - SQLAlchemy engines are configured in `src/infrastructure/db.py` from env vars.
4. **Domain**
   - Domain DTOs (`dataclasses`) and pure domain services exist in `src/domain/`.

## Key Execution Paths

### HTTP API + React UI

- API entry: `uv run uvicorn src.adapters.interface.http_api.main:app --host 127.0.0.1 --port 8000 --reload`
- Frontend entry: `frontend/src/main.tsx` (Vite dev server, proxy `/api/v1` to backend).
- Data access pattern: React page → API query hook → FastAPI route → application use case → repository/port → SQLAlchemy query.

### Sync / Ops CLIs

- `src.adapters.test_db_connection`: tests that both DB URLs are reachable.
- `src.adapters.sync_gnucash_analytics_cli`: mirrors core tables into the analytics DB (creates tables if missing).
- `src.adapters.sync_accounts_cli`: builds the dimensional `accounts_dim` table (truncate + reload).
- `src.adapters.compare_backends_cli`: compares SQLAlchemy vs PieCash outputs (requires `PIECASH_FILE`).

## Configuration and Environment

### Environment Variables

Core:

- `GNUCASH_DB_URL`: SQLAlchemy URL for the source GnuCash Postgres DB/schema.
- `ANALYTICS_DB_URL`: SQLAlchemy URL for the analytics Postgres DB/schema.
- `GNUCASH_BACKEND`: `sqlalchemy` (default), `analytics`, or `piecash`.
- `ANALYTICS_READ_MODE`: `tables` (default) or `views`.
- `PIECASH_FILE`: optional `.gnucash` path/URI (for PieCash backend).

Sanity-check CLI:

- `SANITY_START_DATE`, `SANITY_END_DATE`, `SANITY_CURRENCY`

### Config Files Detected

- `.env` (loaded by `dotenv.load_dotenv()` in `src/infrastructure/db.py`)
- `pyproject.toml` (dependencies + pytest config)
- `pytest.ini`

## Authentication / Security

- No authentication/authorization subsystem detected.
- Primary security boundary is database credentials in `.env` / env vars.

## Protocols / Schemas

- No OpenAPI artifact committed, though routes are defined in FastAPI router code.

## CI/CD and Deployment Automation

- No CI pipelines detected (`.github/workflows` not present).
- No containerization detected (no `Dockerfile` or `docker-compose.*`).
- Deployment appears environment-driven: provide Postgres connectivity + run API/frontend/CLIs.
