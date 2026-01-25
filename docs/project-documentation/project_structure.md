# Project Structure (Initial Scan)

## Summary

- **Repository type:** Monolith (single Python codebase)
- **Primary language/runtime:** Python 3.11 (`pyproject.toml`)
- **UI:** Streamlit adapter (`src/adapters/interface/streamlit/`)
- **Persistence:** SQLAlchemy (<2.0) + Postgres drivers (`psycopg`, `psycopg2`)
- **Architecture style:** Ports & adapters / hexagonal

## Top-Level Layout

- `src/`: Application source code (layered architecture)
- `tests/`: Pytest test suite (unit + adapter/interface tests)
- `migrations/`: Database migration assets (if any)
- `logs/`: Runtime logs
- `docs/`: Project knowledge / generated documentation (this workflow writes here)
- `_bmad/`, `_bmad-output/`: BMAD workflow assets and outputs

## Code Layers (src/)

- `src/adapters/`: Thin entry points (CLIs + Streamlit UI wiring)
  - `src/adapters/interface/streamlit/app.py`: Streamlit app entry point
- `src/application/`: Use cases and ports (application services)
  - `src/application/use_cases/`: Orchestrates domain + repositories, returns DTOs
  - `src/application/ports/`: Protocols for infrastructure dependencies
- `src/domain/`: Domain model, services, policies, validation
- `src/infrastructure/`: Implementations for ports (DB, repositories, container, settings, logging)

## How To Run

- Streamlit app: `uv run python -m streamlit run src/adapters/interface/streamlit/app.py`

## How To Test

- `uv run pytest`

