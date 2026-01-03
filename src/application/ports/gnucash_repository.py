"""Application port for GnuCash data access."""

from datetime import date
from typing import Protocol

from src.domain.models import (
    AssetCategoryBalanceRow,
    NetWorthBalanceRow,
    PriceRow,
)


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
