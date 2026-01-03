"""Port for reading analytics accounts."""

from typing import Protocol

from src.domain.models.accounts import AccountDTO


class AccountsRepositoryPort(Protocol):
    """Port exposing read access to analytics accounts."""

    def fetch_accounts(self) -> list[AccountDTO]:
        """Return the analytics accounts."""


__all__ = ["AccountsRepositoryPort"]
