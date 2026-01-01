"""Factory helpers to select the GnuCash repository backend."""

import os
from pathlib import Path

from src.application.ports.database import DatabaseEnginePort
from src.application.ports.gnucash_repository import GnuCashRepositoryPort
from src.infrastructure.gnucash_repository import SqlAlchemyGnuCashRepository
from src.infrastructure.logging.logger import get_app_logger
from src.infrastructure.piecash_repository import PieCashGnuCashRepository


def _normalize_piecash_path(
    raw_path: str | Path | None,
    logger,
) -> Path | None:
    """Normalize and validate the piecash file path.

    Args:
        raw_path: Raw file path string or Path instance.
        logger: Logger used for warnings.

    Returns:
        Path | None: Normalized path when provided.
    """
    if not raw_path:
        logger.warning(
            "Missing piecash file path; set PIECASH_FILE to enable the backend"
        )
        return None
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        logger.warning(
            "PieCash file does not exist at %s", path
        )
    return path


def create_gnucash_repository(
    db_port: DatabaseEnginePort,
    logger=None,
    backend: str | None = None,
    piecash_path: str | Path | None = None,
) -> GnuCashRepositoryPort:
    """Return a GnuCash repository implementation based on configuration.

    Args:
        db_port: Port providing access to the GnuCash engine (SQL backend).
        logger: Optional logger compatible with logging.Logger-like API.
        backend: Optional backend override (sqlalchemy or piecash).
        piecash_path: Optional path override for the piecash backend.

    Returns:
        GnuCashRepositoryPort: Concrete repository implementation.
    """
    resolved_logger = logger or get_app_logger()
    selected_backend = (
        backend or os.getenv("GNUCASH_BACKEND", "sqlalchemy")
    ).strip().lower()

    if selected_backend == "sqlalchemy":
        return SqlAlchemyGnuCashRepository(db_port)

    if selected_backend == "piecash":
        path = _normalize_piecash_path(
            piecash_path or os.getenv("PIECASH_FILE"),
            resolved_logger,
        )
        if path is None:
            raise RuntimeError("PieCash backend requires a PIECASH_FILE path.")
        return PieCashGnuCashRepository(path, logger=resolved_logger)

    raise ValueError(
        "Unsupported GnuCash backend: "
        f"{selected_backend}. Expected sqlalchemy or piecash."
    )


__all__ = ["create_gnucash_repository"]
