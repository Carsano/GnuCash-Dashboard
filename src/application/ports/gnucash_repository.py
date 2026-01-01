"""Application port for GnuCash data access."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


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


class GnuCashRepositoryPort(Protocol):
    """Port exposing read access to GnuCash reporting data."""

    def fetch_currency_guid(self, currency: str) -> str:
        """Return the GUID for a currency mnemonic."""

    def fetch_net_worth_balances(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> list[NetWorthBalanceRow]:
        """Return balances needed for net worth aggregation."""

    def fetch_asset_category_balances(
        self,
        start_date: date | None,
        end_date: date | None,
        actif_root_name: str,
    ) -> list[AssetCategoryBalanceRow]:
        """Return balances grouped by asset category."""

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date: date | None,
    ) -> list[PriceRow]:
        """Return the latest price rows per commodity."""


__all__ = [
    "GnuCashRepositoryPort",
    "NetWorthBalanceRow",
    "AssetCategoryBalanceRow",
    "PriceRow",
]
