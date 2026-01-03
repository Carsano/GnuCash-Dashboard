"""Domain models for GnuCash row data."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class NetWorthBalanceRow:
    """Row representing a balance for net worth computation."""

    account_type: str
    commodity_guid: str | None
    mnemonic: str | None
    namespace: str | None
    balance: Decimal


@dataclass(frozen=True)
class AssetCategoryBalanceRow:
    """Row representing a balance grouped by asset category."""

    account_type: str
    commodity_guid: str | None
    mnemonic: str | None
    namespace: str | None
    actif_category: str | None
    actif_subcategory: str | None
    balance: Decimal


@dataclass(frozen=True)
class PriceRow:
    """Row representing a commodity price."""

    commodity_guid: str
    value_num: Decimal
    value_denom: Decimal
    date: date


__all__ = [
    "NetWorthBalanceRow",
    "AssetCategoryBalanceRow",
    "PriceRow",
]
