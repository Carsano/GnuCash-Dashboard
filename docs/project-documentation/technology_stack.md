# Technology Stack (Initial Scan)

## Part: `main`

| Category | Technology | Version | Justification |
|---|---|---|---|
| Runtime | Python | `>=3.11,<3.12` (repo pins `3.11`) | `pyproject.toml`, `.python-version` |
| Package/deps | `uv` | (tooling) | `README.md` (`uv sync`, `uv run …`) |
| API | FastAPI, Uvicorn | `>=0.116.0`, `>=0.35.0` | `pyproject.toml`, `src/adapters/interface/http_api/` |
| UI | React, React DOM | `^19.0.0` | `frontend/package.json`, `frontend/src/main.tsx` |
| Routing | react-router-dom | `^7.1.1` | `frontend/package.json` |
| Frontend tooling | Vite, TypeScript | `^6.1.0`, `~5.7.2` | `frontend/package.json`, `frontend/vite.config.ts` |
| Persistence | PostgreSQL | (external service) | `README.md` (`GNUCASH_DB_URL`, `ANALYTICS_DB_URL`) |
| ORM/DB access | SQLAlchemy | `<2.0` | `pyproject.toml`, `src/infrastructure/db.py` |
| DB driver | psycopg | `>=3.1.0` | `pyproject.toml` |
| DB driver (legacy/compat) | psycopg2 | `>=2.9.11` | `pyproject.toml` |
| Env loading | dotenv | `>=0.9.9` | `pyproject.toml`, `src/infrastructure/db.py` (`dotenv.load_dotenv()`) |
| Optional backend | piecash | `>=1.1.2` (extra) | `pyproject.toml` optional deps, `src/infrastructure/settings.py` |
| Testing | pytest, pytest-cov | `>=8.3.2`, `>=5.0.0` | `pyproject.toml`, `tests/` |

## Runtime Configuration (ENV)

Key environment variables (see `README.md`):

- `GNUCASH_DB_URL`, `ANALYTICS_DB_URL`: SQLAlchemy/Postgres URLs
- `GNUCASH_BACKEND`: `sqlalchemy` (default), `analytics`, or `piecash`
- `ANALYTICS_READ_MODE`: `tables` (default) or `views`
- `PIECASH_FILE`: optional `.gnucash` path/URI (for PieCash backend)
