"""Use case to compute net worth from the GnuCash database."""

from datetime import date
from typing import Iterable

from src.application.ports.analytics_repository import AnalyticsRepositoryPort
from src.domain.constants import (
    DEFAULT_ASSET_TYPES,
    DEFAULT_LIABILITY_TYPES,
)
from src.domain.models.finance import NetWorthSummary
from src.domain.services.finance import compute_net_worth_summary
from src.infrastructure.logging.logger import get_app_logger


class GetNetWorthSummaryUseCase:
    """Compute net worth from analytics data."""

    def __init__(
        self,
        gnucash_repository: AnalyticsRepositoryPort,
        logger=None,
        asset_types: Iterable[str] | None = None,
        liability_types: Iterable[str] | None = None,
    ) -> None:
        """Initialize the use case.

        Args:
            gnucash_repository: Port providing GnuCash reporting data.
            logger: Optional logger compatible with logging.Logger-like API.
            asset_types: Optional iterable of account types treated as assets.
            liability_types: Optional iterable treated as liabilities.
        """
        self._gnucash_repository = gnucash_repository
        self._logger = logger or get_app_logger()
        self._asset_types = tuple(asset_types or DEFAULT_ASSET_TYPES)
        self._liability_types = tuple(
            liability_types or DEFAULT_LIABILITY_TYPES
        )

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        target_currency: str = "EUR",
    ) -> NetWorthSummary:
        """Return the net worth summary.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.

        Returns:
            NetWorthSummary: Computed asset, liability, and net worth totals.
        """
        currency_guid = self._gnucash_repository.fetch_currency_guid(
            target_currency
        )
        balances = self._gnucash_repository.fetch_net_worth_balances(
            start_date,
            end_date,
        )
        price_rows = self._gnucash_repository.fetch_latest_prices(
            currency_guid,
            end_date,
        )
        self._logger.info(
            f"Fetched {len(balances)} balances and "
            f"{len(price_rows)} prices for net worth"
        )
        summary = compute_net_worth_summary(
            balances,
            price_rows,
            asset_types=self._asset_types,
            liability_types=self._liability_types,
            currency_guid=currency_guid,
            target_currency=target_currency,
            logger=self._logger,
        )

        self._logger.info(
            f"Net worth computed: assets={summary.asset_total}, "
            f"liabilities={summary.liability_total}, "
            f"currency={target_currency}"
        )

        return summary

__all__ = ["GetNetWorthSummaryUseCase", "NetWorthSummary"]
