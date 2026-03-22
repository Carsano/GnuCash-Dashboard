"""Tests for the SyncAccountCategoriesUseCase."""

from pathlib import Path

from sqlalchemy import create_engine, text

from src.application.ports.database import DatabaseEnginePort
from src.application.use_cases.sync_account_categories import (
    SyncAccountCategoriesUseCase,
)


class _FakeDatabasePort(DatabaseEnginePort):
    def __init__(self, gnucash_url: str, analytics_url: str) -> None:
        self._gnucash_engine = create_engine(gnucash_url)
        self._analytics_engine = create_engine(analytics_url)

    def get_gnucash_engine(self):
        return self._gnucash_engine

    def get_analytics_engine(self):
        return self._analytics_engine


def test_sync_account_categories_materializes_business_table(
    tmp_path: Path,
) -> None:
    analytics_db = tmp_path / "analytics.db"
    db_port = _FakeDatabasePort(
        f"sqlite:///{tmp_path / 'gnucash.db'}",
        f"sqlite:///{analytics_db}",
    )
    _seed_accounts(db_port.get_analytics_engine())

    use_case = SyncAccountCategoriesUseCase(db_port=db_port)

    result = use_case.run()

    assert result.source_count == 6
    assert result.inserted_count == 5

    with db_port.get_analytics_engine().connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT guid, parent_guid, business_category, balance_sheet_category
                FROM accounts_business
                ORDER BY guid
                """
            )
        ).all()

    assert [
        (
            row.guid,
            row.parent_guid,
            row.business_category,
            row.balance_sheet_category,
        )
        for row in rows
    ] == [
        ("acc-1", None, "Actions & Fonds", "Actif"),
        ("acc-2", "root-bank", "Comptes Bancaires", "Actif"),
        ("acc-3", None, "Immobilier", "Actif"),
        ("acc-4", None, "Autres", "Actif"),
        ("acc-6", None, "Cartes de Crédit", "Dette"),
    ]


def test_sync_account_categories_upgrades_existing_table_schema(
    tmp_path: Path,
) -> None:
    analytics_db = tmp_path / "analytics_existing.db"
    db_port = _FakeDatabasePort(
        f"sqlite:///{tmp_path / 'gnucash_existing.db'}",
        f"sqlite:///{analytics_db}",
    )
    _seed_accounts(db_port.get_analytics_engine())

    with db_port.get_analytics_engine().begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE accounts_business (
                guid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                is_placeholder BOOLEAN DEFAULT FALSE,
                business_category TEXT NOT NULL
            )
            """
        )

    use_case = SyncAccountCategoriesUseCase(db_port=db_port)
    use_case.run()

    with db_port.get_analytics_engine().connect() as conn:
        columns = {
            row[1]
            for row in conn.exec_driver_sql(
                "PRAGMA table_info(accounts_business)"
            ).all()
        }

    assert "parent_guid" in columns
    assert "balance_sheet_category" in columns


def _seed_accounts(engine) -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE accounts (
                guid TEXT PRIMARY KEY,
                name TEXT,
                account_type TEXT,
                commodity_guid TEXT,
                parent_guid TEXT,
                is_placeholder BOOLEAN DEFAULT FALSE
            )
            """
        )
        conn.execute(
            text(
                """
                INSERT INTO accounts (
                    guid,
                    name,
                    account_type,
                    commodity_guid,
                    parent_guid,
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
            ),
            [
                {
                    "guid": "acc-1",
                    "name": "Apple",
                    "account_type": "STOCK",
                    "commodity_guid": "eur",
                    "parent_guid": None,
                    "is_placeholder": False,
                },
                {
                    "guid": "acc-2",
                    "name": "Crédit Mutuel",
                    "account_type": "BANK",
                    "commodity_guid": "eur",
                    "parent_guid": "root-bank",
                    "is_placeholder": False,
                },
                {
                    "guid": "acc-3",
                    "name": "Maison",
                    "account_type": "ASSET",
                    "commodity_guid": "eur",
                    "parent_guid": None,
                    "is_placeholder": False,
                },
                {
                    "guid": "acc-4",
                    "name": "Créances",
                    "account_type": "ASSET",
                    "commodity_guid": "eur",
                    "parent_guid": None,
                    "is_placeholder": False,
                },
                {
                    "guid": "acc-5",
                    "name": "80b22cfd37ac483a9a331cb47876e5d4",
                    "account_type": "BANK",
                    "commodity_guid": "eur",
                    "parent_guid": None,
                    "is_placeholder": False,
                },
                {
                    "guid": "acc-6",
                    "name": "Carte de crédit",
                    "account_type": "LIABILITY",
                    "commodity_guid": "eur",
                    "parent_guid": None,
                    "is_placeholder": False,
                },
            ],
        )
