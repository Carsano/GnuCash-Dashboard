"""Tests for the SyncAccountDailyHistoryUseCase."""

from datetime import date, timedelta
from pathlib import Path
from decimal import Decimal

from sqlalchemy import create_engine, text

from src.application.ports.database import DatabaseEnginePort
from src.application.use_cases.sync_account_daily_history import (
    SyncAccountDailyHistoryUseCase,
)


class _FakeDatabasePort(DatabaseEnginePort):
    def __init__(self, gnucash_url: str, analytics_url: str) -> None:
        self._gnucash_engine = create_engine(gnucash_url)
        self._analytics_engine = create_engine(analytics_url)

    def get_gnucash_engine(self):
        return self._gnucash_engine

    def get_analytics_engine(self):
        return self._analytics_engine


def test_sync_account_daily_history_materializes_daily_rows(
    tmp_path: Path,
) -> None:
    analytics_db = tmp_path / "analytics.db"
    db_port = _FakeDatabasePort(
        f"sqlite:///{tmp_path / 'gnucash.db'}",
        f"sqlite:///{analytics_db}",
    )
    _seed_analytics(db_port.get_analytics_engine())

    use_case = SyncAccountDailyHistoryUseCase(db_port=db_port)

    result = use_case.run(target_currency="EUR")

    assert result.account_count == 3
    assert result.snapshot_count == 3
    assert result.inserted_count == 9

    with db_port.get_analytics_engine().connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT snapshot_date,
                       guid,
                       balance_native,
                       balance_converted,
                       business_category,
                       balance_sheet_category
                FROM accounts_daily_history
                ORDER BY snapshot_date, guid
                """
            )
        ).all()

    assert rows[0].guid == "bank-1"
    assert str(rows[0].snapshot_date) == "2024-01-01"
    assert Decimal(rows[0].balance_native) == Decimal("100")
    assert Decimal(rows[0].balance_converted) == Decimal("100")
    assert rows[0].business_category == "Comptes Bancaires"
    assert rows[0].balance_sheet_category == "Actif"

    assert rows[1].guid == "debt-1"
    assert str(rows[1].snapshot_date) == "2024-01-01"
    assert Decimal(rows[1].balance_native) == Decimal("-40")
    assert Decimal(rows[1].balance_converted) == Decimal("-40")
    assert rows[1].business_category == "Cartes de Crédit"
    assert rows[1].balance_sheet_category == "Dette"

    assert rows[2].guid == "stock-1"
    assert str(rows[2].snapshot_date) == "2024-01-01"
    assert Decimal(rows[2].balance_native) == Decimal("2")
    assert rows[2].balance_converted is None

    assert rows[5].guid == "stock-1"
    assert str(rows[5].snapshot_date) == "2024-01-02"
    assert Decimal(rows[5].balance_native) == Decimal("2")
    assert Decimal(rows[5].balance_converted) == Decimal("20")

    assert rows[8].guid == "stock-1"
    assert str(rows[8].snapshot_date) == "2024-01-03"
    assert Decimal(rows[8].balance_native) == Decimal("3")
    assert Decimal(rows[8].balance_converted) == Decimal("30")


def test_sync_account_daily_history_excludes_placeholder_and_hex_names(
    tmp_path: Path,
) -> None:
    analytics_db = tmp_path / "analytics_invalid.db"
    db_port = _FakeDatabasePort(
        f"sqlite:///{tmp_path / 'gnucash_invalid.db'}",
        f"sqlite:///{analytics_db}",
    )
    _seed_analytics(
        db_port.get_analytics_engine(),
        include_invalid_accounts=True,
    )

    use_case = SyncAccountDailyHistoryUseCase(db_port=db_port)
    use_case.run(target_currency="EUR")

    with db_port.get_analytics_engine().connect() as conn:
        guids = conn.execute(
            text(
                """
                SELECT DISTINCT guid
                FROM accounts_daily_history
                ORDER BY guid
                """
            )
        ).scalars().all()

    assert guids == ["bank-1", "debt-1", "stock-1"]


def test_sync_account_daily_history_does_not_materialize_future_dates(
    tmp_path: Path,
) -> None:
    analytics_db = tmp_path / "analytics_future.db"
    db_port = _FakeDatabasePort(
        f"sqlite:///{tmp_path / 'gnucash_future.db'}",
        f"sqlite:///{analytics_db}",
    )
    _seed_analytics(
        db_port.get_analytics_engine(),
        include_future_transaction=True,
    )

    use_case = SyncAccountDailyHistoryUseCase(db_port=db_port)
    use_case.run(target_currency="EUR")

    with db_port.get_analytics_engine().connect() as conn:
        max_snapshot = conn.execute(
            text(
                """
                SELECT MAX(snapshot_date) AS max_snapshot
                FROM accounts_daily_history
                """
            )
        ).scalar()

    assert str(max_snapshot) == str(date.today())


def _seed_analytics(
    engine,
    *,
    include_invalid_accounts: bool = False,
    include_future_transaction: bool = False,
) -> None:
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
                post_date DATE,
                currency_guid TEXT
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

        accounts = [
            {
                "guid": "bank-1",
                "name": "Crédit Mutuel",
                "account_type": "BANK",
                "commodity_guid": "eur-guid",
                "parent_guid": None,
                "is_placeholder": False,
            },
            {
                "guid": "stock-1",
                "name": "Apple",
                "account_type": "STOCK",
                "commodity_guid": "stock-guid",
                "parent_guid": None,
                "is_placeholder": False,
            },
            {
                "guid": "debt-1",
                "name": "Carte de crédit",
                "account_type": "LIABILITY",
                "commodity_guid": "eur-guid",
                "parent_guid": None,
                "is_placeholder": False,
            },
        ]
        if include_invalid_accounts:
            accounts.extend(
                [
                    {
                        "guid": "hex-1",
                        "name": "80b22cfd37ac483a9a331cb47876e5d4",
                        "account_type": "BANK",
                        "commodity_guid": "eur-guid",
                        "parent_guid": None,
                        "is_placeholder": False,
                    },
                    {
                        "guid": "placeholder-1",
                        "name": "Placeholder",
                        "account_type": "BANK",
                        "commodity_guid": "eur-guid",
                        "parent_guid": None,
                        "is_placeholder": True,
                    },
                ]
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
            accounts,
        )
        conn.execute(
            text(
                """
                INSERT INTO commodities (guid, mnemonic, namespace)
                VALUES (:guid, :mnemonic, :namespace)
                """
            ),
            [
                {
                    "guid": "eur-guid",
                    "mnemonic": "EUR",
                    "namespace": "CURRENCY",
                },
                {
                    "guid": "stock-guid",
                    "mnemonic": "AAPL",
                    "namespace": "NASDAQ",
                },
            ],
        )
        transactions = [
            {
                "guid": "tx-1",
                "post_date": date(2024, 1, 1),
                "currency_guid": "eur-guid",
            },
            {
                "guid": "tx-2",
                "post_date": date(2024, 1, 3),
                "currency_guid": "eur-guid",
            },
        ]
        if include_future_transaction:
            transactions.append(
                {
                    "guid": "tx-future",
                    "post_date": date.today() + timedelta(days=5),
                    "currency_guid": "eur-guid",
                }
            )

        conn.execute(
            text(
                """
                INSERT INTO transactions (guid, post_date, currency_guid)
                VALUES (:guid, :post_date, :currency_guid)
                """
            ),
            transactions,
        )
        splits = [
            {
                "guid": "split-1",
                "account_guid": "bank-1",
                "tx_guid": "tx-1",
                "value_num": 100,
                "value_denom": 1,
                "quantity_num": 100,
                "quantity_denom": 1,
            },
                {
                    "guid": "split-2",
                    "account_guid": "debt-1",
                    "tx_guid": "tx-1",
                    "value_num": -40,
                    "value_denom": 1,
                    "quantity_num": -40,
                    "quantity_denom": 1,
                },
                {
                    "guid": "split-3",
                    "account_guid": "stock-1",
                    "tx_guid": "tx-1",
                    "value_num": 0,
                    "value_denom": 1,
                    "quantity_num": 2,
                    "quantity_denom": 1,
                },
                {
                    "guid": "split-4",
                    "account_guid": "stock-1",
                    "tx_guid": "tx-2",
                    "value_num": 0,
                    "value_denom": 1,
                    "quantity_num": 1,
                "quantity_denom": 1,
            },
        ]
        if include_future_transaction:
            splits.append(
                {
                    "guid": "split-future",
                    "account_guid": "bank-1",
                    "tx_guid": "tx-future",
                    "value_num": 10,
                    "value_denom": 1,
                    "quantity_num": 10,
                    "quantity_denom": 1,
                }
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
            splits,
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
            [
                {
                    "guid": "price-1",
                    "commodity_guid": "stock-guid",
                    "currency_guid": "eur-guid",
                    "value_num": 10,
                    "value_denom": 1,
                    "date": date(2024, 1, 2),
                },
            ],
        )
