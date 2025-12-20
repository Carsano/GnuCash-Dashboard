"""Use case for synchronizing GnuCash accounts into the analytics database.

This module defines a simple ETL-style use case that:

* reads accounts from the GnuCash PostgreSQL backend;
* ensures an analytics table for dimensional accounts exists;
* truncates the analytics table and reloads its content from the source.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.application.ports.database import DatabaseEnginePort
from src.application.use_cases.account_filters import is_valid_account_name
from src.infrastructure.logging.logger import get_app_logger


SELECT_ACCOUNTS_SQL = text(
    """
    SELECT guid, name, account_type, commodity_guid, parent_guid
    FROM accounts
    """
)

INSERT_ACCOUNTS_SQL = text(
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

TRUNCATE_ACCOUNTS_SQL = "TRUNCATE TABLE accounts_dim"

CREATE_ACCOUNTS_DIM_SQL = """
CREATE TABLE IF NOT EXISTS accounts_dim (
    guid TEXT PRIMARY KEY,
    name TEXT,
    account_type TEXT,
    commodity_guid TEXT,
    parent_guid TEXT
)
"""


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

        source_accounts = self._fetch_source_accounts(gnucash_engine)
        accounts = self._filter_accounts(source_accounts)
        self._prepare_analytics_destination(analytics_engine)
        inserted_count = self._refresh_analytics_accounts(
            analytics_engine,
            accounts,
        )

        return SyncAccountsResult(
            source_count=len(source_accounts),
            inserted_count=inserted_count,
        )

    def _fetch_source_accounts(
        self,
        gnucash_engine: Engine,
    ) -> list[dict[str, Any]]:
        """Read accounts from the GnuCash database.

        Args:
            gnucash_engine: SQLAlchemy engine for the GnuCash backend.

        Returns:
            list[dict[str, Any]]: Raw account rows converted into dictionaries.
        """
        with gnucash_engine.connect() as conn:
            rows = conn.execute(SELECT_ACCOUNTS_SQL).all()

        accounts = [dict(row._mapping) for row in rows]
        self._logger.info(
            f"Fetched {len(accounts)} accounts from GnuCash source"
        )
        return accounts

    def _filter_accounts(
        self,
        accounts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter out accounts with invalid names.

        Args:
            accounts: Raw records extracted from the GnuCash source.

        Returns:
            list[dict[str, Any]]: Records with validated, sorted names.
        """
        filtered = []
        for account in accounts:
            name_value = account.get("name")
            name = name_value if isinstance(name_value, str) else ""
            if is_valid_account_name(name):
                filtered.append(account)
        filtered = sorted(filtered, key=lambda row: row.get("guid", ""))
        filtered_count = len(accounts) - len(filtered)
        if filtered_count:
            self._logger.warning(
                f"Filtered out {filtered_count} accounts with invalid names"
            )
        return filtered

    def _prepare_analytics_destination(self, analytics_engine: Engine) -> None:
        """Ensure the analytics destination can receive data.

        Args:
            analytics_engine: SQLAlchemy engine for the analytics database.
        """
        self._ensure_analytics_table(analytics_engine)

    def _refresh_analytics_accounts(
        self,
        analytics_engine: Engine,
        accounts: list[dict[str, Any]],
    ) -> int:
        """Replace analytics accounts with the provided records.

        Args:
            analytics_engine: SQLAlchemy engine for the analytics database.
            accounts: Records extracted from the GnuCash source.

        Returns:
            int: Number of accounts inserted into the destination table.
        """
        with analytics_engine.begin() as conn:
            conn.exec_driver_sql(TRUNCATE_ACCOUNTS_SQL)
            if accounts:
                conn.execute(INSERT_ACCOUNTS_SQL, accounts)

        self._logger.info(
            f"Inserted {len(accounts)} accounts into analytics.accounts_dim"
        )
        return len(accounts)

    def _ensure_analytics_table(self, analytics_engine: Engine) -> None:
        """Create the analytics accounts_dim table if it does not exist.

        Args:
            analytics_engine: SQLAlchemy engine for the analytics database.
        """
        with analytics_engine.begin() as conn:
            conn.exec_driver_sql(CREATE_ACCOUNTS_DIM_SQL)

__all__ = ["SyncAccountsUseCase", "SyncAccountsResult"]
