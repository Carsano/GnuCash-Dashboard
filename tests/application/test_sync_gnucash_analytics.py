"""Tests for the GnuCash analytics sync use case."""

from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, text

from src.application.use_cases.sync_gnucash_analytics import (
    SyncGnuCashAnalyticsUseCase,
)
from src.application.ports.database import DatabaseEnginePort


class _FakeDatabasePort(DatabaseEnginePort):
    def __init__(self, gnucash_url: str, analytics_url: str) -> None:
        self._gnucash_engine = create_engine(gnucash_url)
        self._analytics_engine = create_engine(analytics_url)

    def get_gnucash_engine(self):
        return self._gnucash_engine

    def get_analytics_engine(self):
        return self._analytics_engine


def test_sync_gnucash_analytics_copies_tables(tmp_path: Path) -> None:
    """Sync should copy core tables into analytics."""
    gnucash_db = tmp_path / "gnucash.db"
    analytics_db = tmp_path / "analytics.db"
    db_port = _FakeDatabasePort(
        f"sqlite:///{gnucash_db}",
        f"sqlite:///{analytics_db}",
    )

    _seed_source_db(db_port.get_gnucash_engine())

    use_case = SyncGnuCashAnalyticsUseCase(db_port=db_port, chunk_size=2)
    result = use_case.run()

    assert result.accounts_count == 2
    assert result.commodities_count == 1
    assert result.splits_count == 2
    assert result.transactions_count == 1
    assert result.prices_count == 1

    analytics_engine = db_port.get_analytics_engine()
    with analytics_engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) AS count FROM accounts")
        ).first()
    assert count.count == 2


def _seed_source_db(engine) -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE accounts (
                guid TEXT PRIMARY KEY,
                name TEXT,
                account_type TEXT,
                commodity_guid TEXT,
                parent_guid TEXT
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE commodities (
                guid TEXT PRIMARY KEY,
                mnemonic TEXT,
                namespace TEXT
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE splits (
                guid TEXT PRIMARY KEY,
                account_guid TEXT,
                tx_guid TEXT,
                value_num NUMERIC,
                value_denom NUMERIC,
                quantity_num NUMERIC,
                quantity_denom NUMERIC
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE transactions (
                guid TEXT PRIMARY KEY,
                post_date DATE
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE prices (
                guid TEXT PRIMARY KEY,
                commodity_guid TEXT,
                currency_guid TEXT,
                value_num NUMERIC,
                value_denom NUMERIC,
                date DATE
            )
            """
        )
        conn.execute(
            text(
                """
                INSERT INTO accounts (guid, name, account_type, commodity_guid, parent_guid)
                VALUES (:guid, :name, :account_type, :commodity_guid, :parent_guid)
                """
            ),
            [
                {
                    "guid": "acc-1",
                    "name": "Assets",
                    "account_type": "ASSET",
                    "commodity_guid": "cur-1",
                    "parent_guid": None,
                },
                {
                    "guid": "acc-2",
                    "name": "Bank",
                    "account_type": "ASSET",
                    "commodity_guid": "cur-1",
                    "parent_guid": "acc-1",
                },
            ],
        )
        conn.execute(
            text(
                """
                INSERT INTO commodities (guid, mnemonic, namespace)
                VALUES (:guid, :mnemonic, :namespace)
                """
            ),
            {"guid": "cur-1", "mnemonic": "EUR", "namespace": "CURRENCY"},
        )
        conn.execute(
            text(
                """
                INSERT INTO transactions (guid, post_date)
                VALUES (:guid, :post_date)
                """
            ),
            {"guid": "tx-1", "post_date": date(2024, 1, 1)},
        )
        conn.execute(
            text(
                """
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
                """
            ),
            [
                {
                    "guid": "split-1",
                    "account_guid": "acc-1",
                    "tx_guid": "tx-1",
                    "value_num": 100,
                    "value_denom": 1,
                    "quantity_num": 100,
                    "quantity_denom": 1,
                },
                {
                    "guid": "split-2",
                    "account_guid": "acc-2",
                    "tx_guid": "tx-1",
                    "value_num": 50,
                    "value_denom": 1,
                    "quantity_num": 50,
                    "quantity_denom": 1,
                },
            ],
        )
        conn.execute(
            text(
                """
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
                """
            ),
            {
                "guid": "price-1",
                "commodity_guid": "cur-1",
                "currency_guid": "cur-1",
                "value_num": 1,
                "value_denom": 1,
                "date": date(2024, 1, 2),
            },
        )
