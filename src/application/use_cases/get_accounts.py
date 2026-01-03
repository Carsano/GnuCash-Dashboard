"""Use case to read analytics accounts for presentation layers."""

from typing import List

from src.application.ports.accounts_repository import AccountsRepositoryPort
from src.domain.models.accounts import AccountDTO
from src.domain.policies.account_filters import is_valid_account_name


class GetAccountsUseCase:
    """Fetch accounts from the analytics database."""

    def __init__(self, repository: AccountsRepositoryPort) -> None:
        """Initialize the use case with its required dependencies."""
        self._repository = repository

    def execute(self) -> List[AccountDTO]:
        """Return every account currently stored in accounts_dim."""
        accounts = self._repository.fetch_accounts()
        return [
            account
            for account in accounts
            if is_valid_account_name(account.name)
        ]


__all__ = ["GetAccountsUseCase", "AccountDTO"]
