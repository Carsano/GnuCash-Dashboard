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


@dataclass(frozen=True)
class CashflowSummary:
    """Summary of cashflow totals."""

    total_in: Decimal
    total_out: Decimal
    currency_code: str

    @property
    def difference(self) -> Decimal:
        """Return total_in minus total_out."""
        return self.total_in - self.total_out


@dataclass(frozen=True)
class CashflowItem:
    """Cashflow aggregate for a single account."""

    account_full_name: str
    amount: Decimal
    top_parent_name: str | None = None


@dataclass(frozen=True)
class CashflowView:
    """Cashflow summary and details for UI rendering."""

    summary: CashflowSummary
    incoming: list[CashflowItem]
    outgoing: list[CashflowItem]


__all__ = [
    "NetWorthSummary",
    "AssetCategoryAmount",
    "AssetCategoryBreakdown",
    "CashflowSummary",
    "CashflowItem",
    "CashflowView",
]
