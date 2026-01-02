"""Domain models for analytics accounts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AccountDTO:
    """Serializable representation of an analytics account."""

    guid: str
    name: str
    account_type: str
    commodity_guid: str | None
    parent_guid: str | None


__all__ = ["AccountDTO"]
