"""Tests for SQLAlchemy-backed account sync adapters."""

from pathlib import Path

from sqlalchemy import create_engine, text

from src.infrastructure.accounts_sync import SqlAlchemyAccountsSource
from src.application.ports.database import DatabaseEnginePort


class _FakeDatabasePort(DatabaseEnginePort):
    def __init__(self, gnucash_url: str, analytics_url: str) -> None:
        self._gnucash_engine = create_engine(gnucash_url)
        self._analytics_engine = create_engine(analytics_url)

    def get_gnucash_engine(self):
        return self._gnucash_engine

    def get_analytics_engine(self):
        return self._analytics_engine


def test_sqlalchemy_accounts_source_reads_placeholder_slot(
    tmp_path: Path,
) -> None:
    gnucash_db = tmp_path / "gnucash.db"
    analytics_db = tmp_path / "analytics.db"
    db_port = _FakeDatabasePort(
        f"sqlite:///{gnucash_db}",
        f"sqlite:///{analytics_db}",
    )
    engine = db_port.get_gnucash_engine()

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
            CREATE TABLE slots (
                id INTEGER PRIMARY KEY,
                obj_guid TEXT,
                name TEXT,
                slot_type INTEGER,
                int64_val INTEGER,
                string_val TEXT
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
                    "commodity_guid": "EUR",
                    "parent_guid": None,
                },
                {
                    "guid": "acc-2",
                    "name": "Bank",
                    "account_type": "BANK",
                    "commodity_guid": "EUR",
                    "parent_guid": "acc-1",
                },
            ],
        )
        conn.execute(
            text(
                """
                INSERT INTO slots (id, obj_guid, name, slot_type, int64_val, string_val)
                VALUES (:id, :obj_guid, :name, :slot_type, :int64_val, :string_val)
                """
            ),
            {
                "id": 1,
                "obj_guid": "acc-1",
                "name": "placeholder",
                "slot_type": 4,
                "int64_val": 1,
                "string_val": None,
            },
        )

    source = SqlAlchemyAccountsSource(db_port)

    records = source.fetch_accounts()

    assert [record.guid for record in records] == ["acc-1", "acc-2"]
    assert records[0].is_placeholder is True
    assert records[1].is_placeholder is False
