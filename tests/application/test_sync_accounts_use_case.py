"""Tests for the SyncAccountsUseCase."""

from __future__ import annotations

from typing import Iterable
from unittest.mock import MagicMock

import src.application.use_cases.sync_accounts as sync_accounts_module
from src.application.use_cases.sync_accounts import SyncAccountsUseCase


class FakeRow:
    """Simple stand-in for SQLAlchemy rows with a _mapping attribute."""

    def __init__(self, mapping: dict[str, object]) -> None:
        self._mapping = mapping


def _build_db_port(rows: Iterable[FakeRow]) -> tuple[MagicMock, MagicMock]:
    """Create a configured database port mock for the tests."""

    gnucash_engine = MagicMock()
    gnucash_conn = MagicMock()
    gnucash_ctx = MagicMock()
    gnucash_ctx.__enter__.return_value = gnucash_conn
    gnucash_engine.connect.return_value = gnucash_ctx
    gnucash_conn.execute.return_value.all.return_value = list(rows)

    analytics_engine = MagicMock()
    create_conn = MagicMock()
    create_ctx = MagicMock()
    create_ctx.__enter__.return_value = create_conn
    refresh_conn = MagicMock()
    refresh_ctx = MagicMock()
    refresh_ctx.__enter__.return_value = refresh_conn
    analytics_engine.begin.side_effect = [create_ctx, refresh_ctx]

    db_port = MagicMock()
    db_port.get_gnucash_engine.return_value = gnucash_engine
    db_port.get_analytics_engine.return_value = analytics_engine

    return db_port, refresh_conn


def test_run_refreshes_analytics_with_sorted_accounts() -> None:
    """The use case should insert sorted accounts into the analytics table."""
    db_port, refresh_conn = _build_db_port(
        rows=[
            FakeRow(
                {
                    "guid": "b",
                    "name": "Savings",
                    "account_type": "BANK",
                    "commodity_guid": "USD",
                    "parent_guid": "ROOT",
                }
            ),
            FakeRow(
                {
                    "guid": "a",
                    "name": "Checking",
                    "account_type": "BANK",
                    "commodity_guid": "USD",
                    "parent_guid": "ROOT",
                }
            ),
        ]
    )

    use_case = SyncAccountsUseCase(db_port=db_port)

    result = use_case.run()

    refresh_conn.exec_driver_sql.assert_called_once_with(
        sync_accounts_module.TRUNCATE_ACCOUNTS_SQL
    )
    refresh_conn.execute.assert_called_once_with(
        sync_accounts_module.INSERT_ACCOUNTS_SQL,
        [
            {
                "account_type": "BANK",
                "commodity_guid": "USD",
                "guid": "a",
                "name": "Checking",
                "parent_guid": "ROOT",
            },
            {
                "account_type": "BANK",
                "commodity_guid": "USD",
                "guid": "b",
                "name": "Savings",
                "parent_guid": "ROOT",
            },
        ],
    )
    assert result.source_count == 2
    assert result.inserted_count == 2


def test_run_handles_empty_source_without_insert() -> None:
    """No insert should happen when the GnuCash source is empty."""
    db_port, refresh_conn = _build_db_port(rows=[])

    use_case = SyncAccountsUseCase(db_port=db_port)

    result = use_case.run()

    refresh_conn.exec_driver_sql.assert_called_once_with(
        sync_accounts_module.TRUNCATE_ACCOUNTS_SQL
    )
    refresh_conn.execute.assert_not_called()
    assert result.source_count == 0
    assert result.inserted_count == 0
