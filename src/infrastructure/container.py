"""Composition root for wiring infrastructure adapters."""

import os

from src.application.ports.accounts_sync import (
    AccountsDestinationPort,
    AccountsSourcePort,
)
from src.application.ports.accounts_repository import AccountsRepositoryPort
from src.application.ports.accounts_tree_repository import (
    AccountsTreeRepositoryPort,
)
from src.application.ports.analytics_repository import AnalyticsRepositoryPort
from src.application.ports.database import DatabaseEnginePort
from src.application.ports.gnucash_repository import GnuCashRepositoryPort
from src.infrastructure.accounts_sync import (
    PieCashAccountsSource,
    SqlAlchemyAccountsDestination,
    SqlAlchemyAccountsSource,
)
from src.infrastructure.accounts_repository import (
    SqlAlchemyAccountsRepository,
)
from src.infrastructure.accounts_tree_repository import (
    SqlAlchemyAccountsTreeRepository,
)
from src.infrastructure.analytics_gnucash_repository import (
    AnalyticsGnuCashRepository,
)
from src.infrastructure.analytics_views_repository import (
    AnalyticsViewsRepository,
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
    settings = GnuCashSettings.from_env()
    if settings.backend == "piecash":
        if settings.piecash_file is None:
            raise RuntimeError(
                "PieCash backend requires a PIECASH_FILE value."
            )
        return PieCashAccountsSource(
            settings.piecash_file,
            logger=get_app_logger(),
        )
    resolved_db = db_port or build_database_adapter()
    return SqlAlchemyAccountsSource(resolved_db)


def build_accounts_destination(
    db_port: DatabaseEnginePort | None = None,
) -> AccountsDestinationPort:
    """Return the configured accounts destination adapter."""
    resolved_db = db_port or build_database_adapter()
    return SqlAlchemyAccountsDestination(resolved_db)


def build_accounts_repository(
    db_port: DatabaseEnginePort | None = None,
) -> AccountsRepositoryPort:
    """Return the analytics accounts repository."""
    resolved_db = db_port or build_database_adapter()
    return SqlAlchemyAccountsRepository(resolved_db)


def build_accounts_tree_repository(
    db_port: DatabaseEnginePort | None = None,
) -> AccountsTreeRepositoryPort:
    """Return the analytics mirrored accounts repository."""
    resolved_db = db_port or build_database_adapter()
    return SqlAlchemyAccountsTreeRepository(resolved_db)


def build_analytics_repository(
    db_port: DatabaseEnginePort | None = None,
) -> AnalyticsRepositoryPort:
    """Return the analytics repository for dashboard reads."""
    resolved_db = db_port or build_database_adapter()
    mode = os.getenv("ANALYTICS_READ_MODE", "tables").strip().lower()
    if mode == "views":
        return AnalyticsViewsRepository(resolved_db)
    return AnalyticsGnuCashRepository(resolved_db)


__all__ = [
    "build_database_adapter",
    "build_gnucash_repository",
    "build_accounts_source",
    "build_accounts_destination",
    "build_accounts_repository",
    "build_accounts_tree_repository",
    "build_analytics_repository",
]
