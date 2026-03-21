"""Use case to read the full analytics accounts tree for UI selection."""

from src.application.ports.accounts_tree_repository import (
    AccountsTreeRepositoryPort,
)
from src.domain.models.accounts import AccountDTO


class GetAccountsTreeUseCase:
    """Fetch full accounts hierarchy from analytics."""

    def __init__(self, repository: AccountsTreeRepositoryPort) -> None:
        """Initialize the use case with its required dependencies."""
        self._repository = repository

    def execute(self) -> list[AccountDTO]:
        """Return every account currently stored in the analytics mirror."""
        return self._repository.fetch_accounts_tree()


__all__ = ["GetAccountsTreeUseCase"]
