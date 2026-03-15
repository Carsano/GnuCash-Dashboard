# Contribution Guide

## Status

- No `CONTRIBUTING.md` detected.

## Conventions Inferred From Codebase

- Prefer ports/use-cases layering: `adapters → application → ports → infrastructure → domain`.
- Use type hints and immutable dataclasses for DTOs.
- Keep adapters thin; log via the existing logger utilities (no `print` in non-CLI code).
- Keep test expectations deterministic (sorted outputs, stable ordering).

