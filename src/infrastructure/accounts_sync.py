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
    SELECT guid,
           name,
           account_type,
           commodity_guid,
           parent_guid,
           FALSE AS is_placeholder
    FROM accounts
    """
)

SELECT_ACCOUNTS_WITH_PLACEHOLDER_SQL = text(
    """
    SELECT a.guid,
           a.name,
           a.account_type,
           a.commodity_guid,
           a.parent_guid,
           CASE
               WHEN EXISTS (
                   SELECT 1
                   FROM slots s
                   WHERE s.obj_guid = a.guid
                     AND LOWER(s.name) = 'placeholder'
                     AND (
                         COALESCE(s.int64_val, 0) <> 0
                         OR LOWER(COALESCE(s.string_val, '')) IN (
                             '1', 'true', 't', 'yes', 'y'
                         )
                     )
               )
               THEN TRUE
               ELSE FALSE
           END AS is_placeholder
    FROM accounts a
    """
)

INSERT_ACCOUNTS_SQL = text(
    """
    INSERT INTO accounts (
        guid,
        name,
        account_type,
        commodity_guid,
        parent_guid
        ,
        is_placeholder
    )
    VALUES (
        :guid,
        :name,
        :account_type,
        :commodity_guid,
        :parent_guid,
        :is_placeholder
    )
    """
)

TRUNCATE_ACCOUNTS_SQL = "TRUNCATE TABLE accounts"

CREATE_ACCOUNTS_SQL = """
CREATE TABLE IF NOT EXISTS accounts (
    guid TEXT PRIMARY KEY,
    name TEXT,
    account_type TEXT,
    commodity_guid TEXT,
    parent_guid TEXT,
    is_placeholder BOOLEAN DEFAULT FALSE
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
        query = self._select_query(engine)
        with engine.connect() as conn:
            rows = conn.execute(query).all()
        accounts = [
            AccountRecord(
                guid=row.guid,
                name=row.name,
                account_type=row.account_type,
                commodity_guid=row.commodity_guid,
                parent_guid=row.parent_guid,
                is_placeholder=bool(row.is_placeholder),
            )
            for row in rows
        ]
        return sorted(accounts, key=lambda row: row.guid)

    @staticmethod
    def _select_query(engine):
        inspector = engine.dialect.get_columns
        try:
            with engine.connect() as conn:
                column_names = {
                    column["name"].lower()
                    for column in inspector(
                        conn,
                        "slots",
                    )
                }
        except Exception:
            return SELECT_ACCOUNTS_SQL

        required = {"obj_guid", "name", "string_val", "int64_val"}
        if required.issubset(column_names):
            return SELECT_ACCOUNTS_WITH_PLACEHOLDER_SQL
        return SELECT_ACCOUNTS_SQL


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
            conn.exec_driver_sql(CREATE_ACCOUNTS_SQL)
            self._ensure_placeholder_column(conn)

    def refresh_accounts(self, accounts: list[AccountRecord]) -> int:
        """Replace canonical analytics accounts with the provided records.

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

    @staticmethod
    def _ensure_placeholder_column(conn) -> None:
        dialect = conn.engine.dialect.name
        if dialect == "sqlite":
            columns = {
                row[1]
                for row in conn.exec_driver_sql(
                    "PRAGMA table_info(accounts)"
                ).all()
            }
            if "is_placeholder" not in columns:
                conn.exec_driver_sql(
                    "ALTER TABLE accounts "
                    "ADD COLUMN is_placeholder BOOLEAN DEFAULT FALSE"
                )
            return

        exists = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'accounts'
                  AND column_name = 'is_placeholder'
                LIMIT 1
                """
            )
        ).first()
        if not exists:
            conn.exec_driver_sql(
                "ALTER TABLE accounts "
                "ADD COLUMN is_placeholder BOOLEAN DEFAULT FALSE"
            )


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
                "piecash is not installed; "
                "install it to use the piecash backend"
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
                        is_placeholder=bool(
                            getattr(account, "placeholder", False)
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
    "CREATE_ACCOUNTS_SQL",
]
