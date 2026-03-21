"""Tests for the GetAccountsUseCase."""

from unittest.mock import MagicMock

from src.application.use_cases.get_accounts import (
    AccountDTO,
    GetAccountsUseCase,
)


def test_execute_returns_all_accounts_from_analytics_db() -> None:
    """Use case should return every imported analytics account."""
    rows = [
        AccountDTO(
            guid="a",
            name="Checking",
            account_type="BANK",
            commodity_guid="USD",
            parent_guid=None,
            is_placeholder=False,
        ),
        AccountDTO(
            guid="hex",
            name="b13e492052bf4acfaf4bd739b1351b5d",
            account_type="BANK",
            commodity_guid="USD",
            parent_guid=None,
            is_placeholder=True,
        ),
        AccountDTO(
            guid="b",
            name="Savings",
            account_type="BANK",
            commodity_guid="USD",
            parent_guid="a",
            is_placeholder=False,
        ),
    ]
    repository = MagicMock()
    repository.fetch_accounts.return_value = rows

    use_case = GetAccountsUseCase(repository=repository)

    result = use_case.execute()

    assert result == rows
    repository.fetch_accounts.assert_called_once_with()
