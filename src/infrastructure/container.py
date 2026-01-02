"""Composition root for wiring infrastructure adapters."""

from src.application.ports.accounts_sync import (
    AccountsDestinationPort,
    AccountsSourcePort,
)
from src.application.ports.database import DatabaseEnginePort
from src.application.ports.gnucash_repository import GnuCashRepositoryPort
from src.infrastructure.accounts_sync import (
    SqlAlchemyAccountsDestination,
    SqlAlchemyAccountsSource,
)
from src.infrastructure.db import SqlAlchemyDatabaseEngineAdapter
from src.infrastructure.gnucash_repository_factory import (
    create_gnucash_repository,
)
from src.infrastructure.logging.logger import get_app_logger
from src.infrastructure.settings import GnuCashSettings


def build_database_adapter() -> DatabaseEnginePort:
    """Return the database adapter instance."""
    return SqlAlchemyDatabaseEngineAdapter()


def build_gnucash_repository(
    db_port: DatabaseEnginePort | None = None,
) -> GnuCashRepositoryPort:
    """Return the configured GnuCash repository."""
    resolved_db = db_port or build_database_adapter()
    settings = GnuCashSettings.from_env()
    return create_gnucash_repository(
        resolved_db,
        logger=get_app_logger(),
        settings=settings,
    )


def build_accounts_source(
    db_port: DatabaseEnginePort | None = None,
) -> AccountsSourcePort:
    """Return the configured accounts source adapter."""
    resolved_db = db_port or build_database_adapter()
    return SqlAlchemyAccountsSource(resolved_db)


def build_accounts_destination(
    db_port: DatabaseEnginePort | None = None,
) -> AccountsDestinationPort:
    """Return the configured accounts destination adapter."""
    resolved_db = db_port or build_database_adapter()
    return SqlAlchemyAccountsDestination(resolved_db)


__all__ = [
    "build_database_adapter",
    "build_gnucash_repository",
    "build_accounts_source",
    "build_accounts_destination",
]
