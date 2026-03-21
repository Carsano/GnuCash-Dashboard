"""Tests for the GetAccountsTreeUseCase."""

from unittest.mock import MagicMock

from src.application.use_cases.get_accounts_tree import GetAccountsTreeUseCase
from src.domain.models.accounts import AccountDTO


def test_execute_returns_all_accounts_from_analytics_tree() -> None:
    """Use case should return every imported account from the tree source."""
    rows = [
        AccountDTO(
            guid="root",
            name="Assets",
            account_type="ASSET",
            commodity_guid="EUR",
            parent_guid=None,
            is_placeholder=False,
        ),
        AccountDTO(
            guid="hex",
            name="b13e492052bf4acfaf4bd739b1351b5d",
            account_type="ASSET",
            commodity_guid="EUR",
            parent_guid="root",
            is_placeholder=True,
        ),
    ]
    repository = MagicMock()
    repository.fetch_accounts_tree.return_value = rows

    use_case = GetAccountsTreeUseCase(repository=repository)

    result = use_case.execute()

    assert result == rows
    repository.fetch_accounts_tree.assert_called_once_with()
