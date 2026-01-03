"""Port for retrieving a full accounts tree from analytics storage."""

from typing import Protocol

from src.domain.models.accounts import AccountDTO


class AccountsTreeRepositoryPort(Protocol):
    """Port exposing a full accounts hierarchy for UI selection."""

    def fetch_accounts_tree(self) -> list[AccountDTO]:
        """Return accounts from the analytics mirror of GnuCash tables."""


__all__ = ["AccountsTreeRepositoryPort"]

