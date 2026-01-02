"""Factory helpers to select the GnuCash repository backend."""

from src.application.ports.database import DatabaseEnginePort
from src.application.ports.gnucash_repository import GnuCashRepositoryPort
from src.infrastructure.gnucash_repository import SqlAlchemyGnuCashRepository
from src.infrastructure.logging.logger import get_app_logger
from src.infrastructure.piecash_repository import PieCashGnuCashRepository
from src.infrastructure.settings import GnuCashSettings


def create_gnucash_repository(
    db_port: DatabaseEnginePort,
    logger=None,
    settings: GnuCashSettings | None = None,
) -> GnuCashRepositoryPort:
    """Return a GnuCash repository implementation based on configuration.

    Args:
        db_port: Port providing access to the GnuCash engine (SQL backend).
        logger: Optional logger compatible with logging.Logger-like API.
        settings: Optional backend settings override.

    Returns:
        GnuCashRepositoryPort: Concrete repository implementation.
    """
    resolved_logger = logger or get_app_logger()
    resolved_settings = settings or GnuCashSettings.from_env()
    selected_backend = resolved_settings.backend.strip().lower()
    resolved_logger.info("Using GnuCash backend: %s", selected_backend)

    if selected_backend == "sqlalchemy":
        return SqlAlchemyGnuCashRepository(db_port)

    if selected_backend == "piecash":
        path = resolved_settings.piecash_file
        if path is None:
            raise RuntimeError("PieCash backend requires a PIECASH_FILE path.")
        resolved_logger.info("Using piecash book: %s", path)
        return PieCashGnuCashRepository(path, logger=resolved_logger)

    raise ValueError(
        "Unsupported GnuCash backend: "
        f"{selected_backend}. Expected sqlalchemy or piecash."
    )


__all__ = ["create_gnucash_repository"]
