"""Use case for synchronizing GnuCash accounts into the analytics database.

This module defines a simple ETL-style use case that:

* reads accounts from the GnuCash PostgreSQL backend;
* ensures an analytics table for dimensional accounts exists;
* truncates the analytics table and reloads its content from the source.
"""

from dataclasses import dataclass

from sqlalchemy import text

from src.application.ports.database import DatabaseEnginePort
from src.infrastructure.logging.logger import get_app_logger


@dataclass(frozen=True)
class SyncAccountsResult:
    """Result of a sync_accounts run.

    Attributes:
        source_count: Number of accounts read from the GnuCash database.
        inserted_count: Number of accounts inserted into the analytics table.
    """

    source_count: int
    inserted_count: int


class SyncAccountsUseCase:
    """Synchronize GnuCash accounts into the analytics database.

    The use case uses the DatabaseEnginePort to remain decoupled from concrete
    database drivers or configuration details.
    """

    def __init__(self, db_port: DatabaseEnginePort, logger=None) -> None:
        """Initialize the use case.

        Args:
            db_port: Port providing access to GnuCash and analytics engines.
            logger: Optional logger compatible with logging.Logger-like API.
        """
        self._db_port = db_port
        self._logger = logger or get_app_logger()

    def run(self) -> SyncAccountsResult:
        """Execute the synchronization job.

        The method creates the analytics table if needed, truncates it, and
        reloads all accounts from the GnuCash source database.

        Returns:
            SyncAccountsResult: Summary of how many rows were processed.
        """
        gnucash_engine = self._db_port.get_gnucash_engine()
        analytics_engine = self._db_port.get_analytics_engine()

        self._ensure_analytics_table(analytics_engine)

        select_sql = text(
            """
            SELECT guid, name, account_type, commodity_guid, parent_guid
            FROM accounts
            """
        )

        with gnucash_engine.connect() as conn:
            rows = conn.execute(select_sql).all()

        row_dicts = [dict(row._mapping) for row in rows]
        source_count = len(row_dicts)

        self._logger.info(
            "Fetched %d accounts from GnuCash source", source_count
        )

        insert_sql = text(
            """
            INSERT INTO accounts_dim (
                guid,
                name,
                account_type,
                commodity_guid,
                parent_guid
            )
            VALUES (
                :guid,
                :name,
                :account_type,
                :commodity_guid,
                :parent_guid
            )
            """
        )

        with analytics_engine.begin() as conn:
            conn.exec_driver_sql("TRUNCATE TABLE accounts_dim")
            if row_dicts:
                conn.execute(insert_sql, row_dicts)

        self._logger.info(
            "Inserted %d accounts into analytics.accounts_dim", source_count
        )

        return SyncAccountsResult(
            source_count=source_count,
            inserted_count=source_count,
        )

    def _ensure_analytics_table(self, analytics_engine) -> None:
        """Create the analytics accounts_dim table if it does not exist.

        Args:
            analytics_engine: SQLAlchemy engine for the analytics database.
        """
        create_sql = """
        CREATE TABLE IF NOT EXISTS accounts_dim (
            guid TEXT PRIMARY KEY,
            name TEXT,
            account_type TEXT,
            commodity_guid TEXT,
            parent_guid TEXT
        )
        """
        with analytics_engine.begin() as conn:
            conn.exec_driver_sql(create_sql)


__all__ = ["SyncAccountsUseCase", "SyncAccountsResult"]
