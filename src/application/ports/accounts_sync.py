"""Ports for synchronizing account data into analytics storage."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AccountRecord:
    """Immutable account record for synchronization workflows."""

    guid: str
    name: str
    account_type: str
    commodity_guid: str | None
    parent_guid: str | None


class AccountsSourcePort(Protocol):
    """Port exposing read access to account records."""

    def fetch_accounts(self) -> list[AccountRecord]:
        """Return all source accounts for synchronization."""


class AccountsDestinationPort(Protocol):
    """Port exposing write access to analytics account storage."""

    def prepare_destination(self) -> None:
        """Ensure the analytics destination is ready to receive data."""

    def refresh_accounts(self, accounts: list[AccountRecord]) -> int:
        """Replace the destination accounts with the provided records."""


__all__ = [
    "AccountRecord",
    "AccountsSourcePort",
    "AccountsDestinationPort",
]
