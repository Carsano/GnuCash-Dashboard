"""Domain models for analytics accounts."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AccountDTO:
    """Serializable representation of an analytics account."""

    guid: str
    name: str
    account_type: str
    commodity_guid: str | None
    parent_guid: str | None


@dataclass(frozen=True)
class AccountBalanceRow:
    """Raw balance row for an account from analytics."""

    guid: str
    name: str
    account_type: str
    commodity_guid: str | None
    parent_guid: str | None
    mnemonic: str | None
    namespace: str | None
    balance: Decimal


@dataclass(frozen=True)
class AccountBalanceDTO:
    """Serializable account balance in a target currency."""

    guid: str
    name: str
    account_type: str
    parent_guid: str | None
    balance: Decimal | None
    currency_code: str


__all__ = ["AccountDTO", "AccountBalanceRow", "AccountBalanceDTO"]
