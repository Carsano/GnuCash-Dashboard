"""Use case to read imported analytics accounts."""

from typing import List

from src.application.ports.accounts_repository import AccountsRepositoryPort
from src.domain.models.accounts import AccountDTO


class GetAccountsUseCase:
    """Fetch accounts from the canonical analytics mirror."""

    def __init__(self, repository: AccountsRepositoryPort) -> None:
        """Initialize the use case with its required dependencies."""
        self._repository = repository

    def execute(self) -> List[AccountDTO]:
        """Return every account currently stored in the analytics mirror."""
        return self._repository.fetch_accounts()


__all__ = ["GetAccountsUseCase", "AccountDTO"]
