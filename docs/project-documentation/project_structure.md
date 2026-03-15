# Project Structure (Initial Scan)

## Summary

- **Repository type:** Monolith (single backend repo + colocated frontend)
- **Primary language/runtime:** Python 3.11 (`pyproject.toml`)
- **UI:** React frontend (`frontend/`)
- **API:** FastAPI adapter (`src/adapters/interface/http_api/`)
- **Persistence:** SQLAlchemy (<2.0) + Postgres drivers (`psycopg`, `psycopg2`)
- **Architecture style:** Ports & adapters / hexagonal

## Top-Level Layout

- `src/`: Backend source code (layered architecture)
- `frontend/`: React + TypeScript UI
- `tests/`: Pytest test suite (unit + adapter/interface tests)
- `migrations/`: Database migration assets (if any)
- `logs/`: Runtime logs
- `docs/`: Project knowledge / generated documentation (this workflow writes here)
- `_bmad/`, `_bmad-output/`: BMAD workflow assets and outputs

## Code Layers (src/)

- `src/adapters/`: Thin entry points (CLIs + HTTP API wiring)
  - `src/adapters/interface/http_api/app.py`: FastAPI app factory
  - `src/adapters/interface/http_api/router.py`: API routes
- `src/application/`: Use cases and ports (application services)
  - `src/application/use_cases/`: Orchestrates domain + repositories, returns DTOs
  - `src/application/ports/`: Protocols for infrastructure dependencies
- `src/domain/`: Domain model, services, policies, validation
- `src/infrastructure/`: Implementations for ports (DB, repositories, container, settings, logging)

## How To Run

- API: `uv run uvicorn src.adapters.interface.http_api.main:app --host 127.0.0.1 --port 8000 --reload`
- Frontend: `cd frontend && pnpm dev`

## How To Test

- `uv run pytest`
