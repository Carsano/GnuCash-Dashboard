"""Domain models for financial aggregates."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class NetWorthSummary:
    """Summary of net worth figures.

    Attributes:
        asset_total: Sum of asset balances.
        liability_total: Sum of liability balances.
        net_worth: Assets minus liabilities.
    """

    asset_total: Decimal
    liability_total: Decimal
    net_worth: Decimal
    currency_code: str


@dataclass(frozen=True)
class AssetCategoryAmount:
    """Amount aggregated for a given asset category."""

    category: str
    amount: Decimal
    parent_category: str | None = None


@dataclass(frozen=True)
class AssetCategoryBreakdown:
    """Breakdown of asset amounts by category."""

    currency_code: str
    categories: list[AssetCategoryAmount]


__all__ = [
    "NetWorthSummary",
    "AssetCategoryAmount",
    "AssetCategoryBreakdown",
]
