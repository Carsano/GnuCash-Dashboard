"""Use case to mirror GnuCash tables into the analytics database."""

from dataclasses import dataclass

from sqlalchemy import text

from src.application.ports.database import DatabaseEnginePort
from src.infrastructure.logging.logger import get_app_logger


@dataclass(frozen=True)
class SyncGnuCashAnalyticsResult:
    """Result of a GnuCash analytics sync.

    Attributes:
        accounts_count: Number of accounts copied.
        commodities_count: Number of commodities copied.
        splits_count: Number of splits copied.
        transactions_count: Number of transactions copied.
        prices_count: Number of prices copied.
    """

    accounts_count: int
    commodities_count: int
    splits_count: int
    transactions_count: int
    prices_count: int


class SyncGnuCashAnalyticsUseCase:
    """Mirror core GnuCash tables into the analytics database."""

    def __init__(
        self,
        db_port: DatabaseEnginePort,
        logger=None,
        chunk_size: int = 5000,
    ) -> None:
        """Initialize the use case.

        Args:
            db_port: Port providing access to GnuCash and analytics engines.
            logger: Optional logger compatible with logging.Logger-like API.
            chunk_size: Number of rows per bulk insert batch.
        """
        self._db_port = db_port
        self._logger = logger or get_app_logger()
        self._chunk_size = chunk_size

    def run(self) -> SyncGnuCashAnalyticsResult:
        """Execute the sync job.

        Returns:
            SyncGnuCashAnalyticsResult: Summary of copied row counts.
        """
        counts = {}
        for spec in _SYNC_SPECS:
            count = self._sync_table(spec)
            counts[spec.name] = count
            self._logger.info(
                f"Synced {count} rows into analytics.{spec.name}"
            )
        return SyncGnuCashAnalyticsResult(
            accounts_count=counts["accounts"],
            commodities_count=counts["commodities"],
            splits_count=counts["splits"],
            transactions_count=counts["transactions"],
            prices_count=counts["prices"],
        )

    def _sync_table(self, spec: "SyncTableSpec") -> int:
        source_engine = self._db_port.get_gnucash_engine()
        target_engine = self._db_port.get_analytics_engine()

        with target_engine.begin() as conn:
            conn.exec_driver_sql(spec.create_sql)
            self._truncate_table(conn, spec.name)

        total = 0
        with source_engine.connect() as source_conn:
            result = source_conn.execute(text(spec.select_sql))
            while True:
                rows = result.fetchmany(self._chunk_size)
                if not rows:
                    break
                payload = [dict(row._mapping) for row in rows]
                with target_engine.begin() as target_conn:
                    target_conn.execute(text(spec.insert_sql), payload)
                total += len(payload)
        return total

    @staticmethod
    def _truncate_table(conn, table_name: str) -> None:
        dialect = conn.engine.dialect.name
        if dialect == "sqlite":
            conn.exec_driver_sql(f"DELETE FROM {table_name}")
            return
        conn.exec_driver_sql(f"TRUNCATE TABLE {table_name}")


@dataclass(frozen=True)
class SyncTableSpec:
    """Specification for syncing a single table."""

    name: str
    select_sql: str
    insert_sql: str
    create_sql: str


_SYNC_SPECS = (
    SyncTableSpec(
        name="accounts",
        select_sql="""
            SELECT guid, name, account_type, commodity_guid, parent_guid
            FROM accounts
        """,
        insert_sql="""
            INSERT INTO accounts (
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
        """,
        create_sql="""
            CREATE TABLE IF NOT EXISTS accounts (
                guid TEXT PRIMARY KEY,
                name TEXT,
                account_type TEXT,
                commodity_guid TEXT,
                parent_guid TEXT
            )
        """,
    ),
    SyncTableSpec(
        name="commodities",
        select_sql="""
            SELECT guid, mnemonic, namespace
            FROM commodities
        """,
        insert_sql="""
            INSERT INTO commodities (
                guid,
                mnemonic,
                namespace
            )
            VALUES (
                :guid,
                :mnemonic,
                :namespace
            )
        """,
        create_sql="""
            CREATE TABLE IF NOT EXISTS commodities (
                guid TEXT PRIMARY KEY,
                mnemonic TEXT,
                namespace TEXT
            )
        """,
    ),
    SyncTableSpec(
        name="splits",
        select_sql="""
            SELECT guid,
                   account_guid,
                   tx_guid,
                   value_num,
                   value_denom,
                   quantity_num,
                   quantity_denom
            FROM splits
        """,
        insert_sql="""
            INSERT INTO splits (
                guid,
                account_guid,
                tx_guid,
                value_num,
                value_denom,
                quantity_num,
                quantity_denom
            )
            VALUES (
                :guid,
                :account_guid,
                :tx_guid,
                :value_num,
                :value_denom,
                :quantity_num,
                :quantity_denom
            )
        """,
        create_sql="""
            CREATE TABLE IF NOT EXISTS splits (
                guid TEXT PRIMARY KEY,
                account_guid TEXT,
                tx_guid TEXT,
                value_num NUMERIC,
                value_denom NUMERIC,
                quantity_num NUMERIC,
                quantity_denom NUMERIC
            )
        """,
    ),
    SyncTableSpec(
        name="transactions",
        select_sql="""
            SELECT guid, post_date
            FROM transactions
        """,
        insert_sql="""
            INSERT INTO transactions (
                guid,
                post_date
            )
            VALUES (
                :guid,
                :post_date
            )
        """,
        create_sql="""
            CREATE TABLE IF NOT EXISTS transactions (
                guid TEXT PRIMARY KEY,
                post_date DATE
            )
        """,
    ),
    SyncTableSpec(
        name="prices",
        select_sql="""
            SELECT guid,
                   commodity_guid,
                   currency_guid,
                   value_num,
                   value_denom,
                   date
            FROM prices
        """,
        insert_sql="""
            INSERT INTO prices (
                guid,
                commodity_guid,
                currency_guid,
                value_num,
                value_denom,
                date
            )
            VALUES (
                :guid,
                :commodity_guid,
                :currency_guid,
                :value_num,
                :value_denom,
                :date
            )
        """,
        create_sql="""
            CREATE TABLE IF NOT EXISTS prices (
                guid TEXT PRIMARY KEY,
                commodity_guid TEXT,
                currency_guid TEXT,
                value_num NUMERIC,
                value_denom NUMERIC,
                date DATE
            )
        """,
    ),
)


__all__ = ["SyncGnuCashAnalyticsUseCase", "SyncGnuCashAnalyticsResult"]
