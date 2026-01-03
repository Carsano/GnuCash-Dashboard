"""Use case to read the full analytics accounts tree for UI selection."""

from src.application.ports.accounts_tree_repository import (
    AccountsTreeRepositoryPort,
)
from src.domain.models.accounts import AccountDTO
from src.domain.policies.account_filters import is_valid_account_name


class GetAccountsTreeUseCase:
    """Fetch full accounts hierarchy from analytics."""

    def __init__(self, repository: AccountsTreeRepositoryPort) -> None:
        """Initialize the use case with its required dependencies."""
        self._repository = repository

    def execute(self) -> list[AccountDTO]:
        """Return every account currently stored in the analytics mirror."""
        accounts = self._repository.fetch_accounts_tree()
        return [
            account
            for account in accounts
            if is_valid_account_name(account.name)
        ]


__all__ = ["GetAccountsTreeUseCase"]

