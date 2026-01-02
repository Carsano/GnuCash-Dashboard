"""Infrastructure adapters for synchronizing accounts via SQLAlchemy."""

from dataclasses import asdict
from pathlib import Path

from sqlalchemy import text

from src.application.ports.accounts_sync import (
    AccountRecord,
    AccountsDestinationPort,
    AccountsSourcePort,
)
from src.application.ports.database import DatabaseEnginePort
from src.infrastructure.logging.logger import get_app_logger
from src.infrastructure.piecash_compat import load_piecash, open_piecash_book


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


class SqlAlchemyAccountsSource(AccountsSourcePort):
    """Account source backed by the GnuCash SQL database."""

    def __init__(self, db_port: DatabaseEnginePort) -> None:
        """Initialize the source adapter.

        Args:
            db_port: Port providing access to the GnuCash engine.
        """
        self._db_port = db_port

    def fetch_accounts(self) -> list[AccountRecord]:
        """Return account records from the GnuCash source database.

        Returns:
            list[AccountRecord]: Accounts fetched from the source database.
        """
        engine = self._db_port.get_gnucash_engine()
        with engine.connect() as conn:
            rows = conn.execute(SELECT_ACCOUNTS_SQL).all()
        accounts = [
            AccountRecord(
                guid=row.guid,
                name=row.name,
                account_type=row.account_type,
                commodity_guid=row.commodity_guid,
                parent_guid=row.parent_guid,
            )
            for row in rows
        ]
        return sorted(accounts, key=lambda row: row.guid)


class SqlAlchemyAccountsDestination(AccountsDestinationPort):
    """Analytics destination backed by SQLAlchemy."""

    def __init__(self, db_port: DatabaseEnginePort) -> None:
        """Initialize the destination adapter.

        Args:
            db_port: Port providing access to the analytics engine.
        """
        self._db_port = db_port

    def prepare_destination(self) -> None:
        """Ensure the analytics destination table exists."""
        engine = self._db_port.get_analytics_engine()
        with engine.begin() as conn:
            conn.exec_driver_sql(CREATE_ACCOUNTS_DIM_SQL)

    def refresh_accounts(self, accounts: list[AccountRecord]) -> int:
        """Replace analytics accounts with the provided records.

        Args:
            accounts: Account records to write to analytics storage.

        Returns:
            int: Number of account records inserted.
        """
        payload = [asdict(account) for account in accounts]
        engine = self._db_port.get_analytics_engine()
        with engine.begin() as conn:
            conn.exec_driver_sql(TRUNCATE_ACCOUNTS_SQL)
            if payload:
                conn.execute(INSERT_ACCOUNTS_SQL, payload)
        return len(payload)


class PieCashAccountsSource(AccountsSourcePort):
    """Account source backed by a piecash book."""

    def __init__(self, book_path: Path | str, logger=None) -> None:
        """Initialize the source adapter.

        Args:
            book_path: Path or URI to the piecash book.
            logger: Optional logger compatible with logging.Logger-like API.
        """
        try:
            self._piecash = load_piecash()
        except ImportError as exc:
            raise RuntimeError(
                "piecash is not installed; install it to use the piecash backend"
            ) from exc
        self._book_path = book_path
        self._logger = logger or get_app_logger()

    def fetch_accounts(self) -> list[AccountRecord]:
        """Return account records from the piecash book.

        Returns:
            list[AccountRecord]: Accounts fetched from the piecash book.
        """
        book = open_piecash_book(
            self._piecash,
            self._book_path,
            readonly=True,
            open_if_lock=True,
            check_exists=False,
        )
        try:
            accounts = []
            for account in book.accounts:
                account_type = getattr(account, "type", "")
                if hasattr(account_type, "name"):
                    account_type = str(account_type.name).upper()
                else:
                    account_type = str(account_type).upper()
                commodity = getattr(account, "commodity", None)
                accounts.append(
                    AccountRecord(
                        guid=account.guid,
                        name=account.name,
                        account_type=account_type,
                        commodity_guid=(
                            commodity.guid if commodity is not None else None
                        ),
                        parent_guid=(
                            account.parent.guid
                            if getattr(account, "parent", None) is not None
                            else None
                        ),
                    )
                )
            return sorted(accounts, key=lambda row: row.guid)
        finally:
            close_method = getattr(book, "close", None)
            if callable(close_method):
                close_method()


__all__ = [
    "SqlAlchemyAccountsSource",
    "SqlAlchemyAccountsDestination",
    "PieCashAccountsSource",
    "SELECT_ACCOUNTS_SQL",
    "INSERT_ACCOUNTS_SQL",
    "TRUNCATE_ACCOUNTS_SQL",
    "CREATE_ACCOUNTS_DIM_SQL",
]
