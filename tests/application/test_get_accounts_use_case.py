"""Tests for the GetAccountsUseCase."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.application.use_cases.get_accounts import (
    AccountDTO,
    GetAccountsUseCase,
)


def _build_db_port(rows: list[SimpleNamespace]) -> MagicMock:
    engine = MagicMock()
    conn = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = conn
    engine.connect.return_value = context
    conn.execute.return_value.all.return_value = rows

    db_port = MagicMock()
    db_port.get_analytics_engine.return_value = engine
    return db_port


def test_execute_returns_accounts_from_analytics_db() -> None:
    """Use case should return AccountDTO objects for every analytics entry."""
    rows = [
        SimpleNamespace(
            guid="a",
            name="Checking",
            account_type="BANK",
            commodity_guid="USD",
            parent_guid=None,
        ),
        SimpleNamespace(
            guid="b",
            name="Savings",
            account_type="BANK",
            commodity_guid="USD",
            parent_guid="a",
        ),
    ]
    db_port = _build_db_port(rows)

    use_case = GetAccountsUseCase(db_port=db_port)

    result = use_case.execute()

    assert result == [
        AccountDTO(
            guid="a",
            name="Checking",
            account_type="BANK",
            commodity_guid="USD",
            parent_guid=None,
        ),
        AccountDTO(
            guid="b",
            name="Savings",
            account_type="BANK",
            commodity_guid="USD",
            parent_guid="a",
        ),
    ]
    db_port.get_analytics_engine.assert_called_once()
