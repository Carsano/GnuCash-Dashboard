# Critical Folders Summary

- `src/adapters/`: UI + CLI entry points; should stay thin (no business logic).
- `src/application/use_cases/`: primary “business orchestration” layer; returns DTOs for adapters.
- `src/application/ports/`: Protocols defining boundaries for DB/repositories/sync.
- `src/infrastructure/`: SQLAlchemy engines, repository implementations, backend selection, DI container.
- `src/domain/`: domain DTOs and pure-domain services/policies (validation, normalization, finance).
- `tests/`: contract and behavioral tests across layers.

