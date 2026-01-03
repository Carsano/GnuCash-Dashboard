"""Port for analytics-backed finance reads."""

from datetime import date
from typing import Protocol

from src.domain.models import (
    AccountBalanceRow,
    AssetCategoryBalanceRow,
    CashflowRow,
    NetWorthBalanceRow,
    PriceRow,
)


class AnalyticsRepositoryPort(Protocol):
    """Port exposing analytics data needed for dashboard computations."""

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

    def fetch_account_balances(
        self,
        end_date: date | None,
    ) -> list[AccountBalanceRow]:
        """Return balances grouped by account."""

    def fetch_cashflow_rows(
        self,
        start_date: date | None,
        end_date: date | None,
        asset_root_name: str,
        currency_guid: str,
        asset_account_guids: list[str] | None = None,
    ) -> list[CashflowRow]:
        """Return cashflow rows grouped by account."""

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date: date | None,
    ) -> list[PriceRow]:
        """Return the latest price rows per commodity."""


__all__ = ["AnalyticsRepositoryPort"]
