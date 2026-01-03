"""Use case to compute asset category breakdown in a target currency."""

from datetime import date
from typing import Iterable

from src.application.ports.analytics_repository import AnalyticsRepositoryPort
from src.domain.constants import DEFAULT_ASSET_TYPES
from src.domain.models.finance import AssetCategoryBreakdown
from src.domain.services.finance import compute_asset_category_breakdown
from src.infrastructure.logging.logger import get_app_logger


class GetAssetCategoryBreakdownUseCase:
    """Compute asset category breakdown from analytics data."""

    def __init__(
        self,
        gnucash_repository: AnalyticsRepositoryPort,
        logger=None,
        asset_types: Iterable[str] | None = None,
        actif_root_name: str = "Actif",
    ) -> None:
        """Initialize the use case.

        Args:
            gnucash_repository: Port providing GnuCash reporting data.
            logger: Optional logger compatible with logging.Logger-like API.
            asset_types: Optional iterable of account types treated as assets.
            actif_root_name: Name of the root account containing asset buckets.
        """
        self._gnucash_repository = gnucash_repository
        self._logger = logger or get_app_logger()
        self._asset_types = tuple(asset_types or DEFAULT_ASSET_TYPES)
        self._actif_root_name = actif_root_name

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        target_currency: str = "EUR",
        level: int = 1,
    ) -> AssetCategoryBreakdown:
        """Return the asset breakdown in the target currency.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.
            target_currency: Currency code to convert into.
            level: Depth level under the Actif root (1 or 2).

        Returns:
            AssetCategoryBreakdown: Aggregated asset totals by category.
        """
        currency_guid = self._gnucash_repository.fetch_currency_guid(
            target_currency
        )
        rows = self._gnucash_repository.fetch_asset_category_balances(
            start_date,
            end_date,
            self._actif_root_name,
        )
        price_rows = self._gnucash_repository.fetch_latest_prices(
            currency_guid,
            end_date,
        )
        self._logger.info(
            f"Fetched {len(rows)} category balances and "
            f"{len(price_rows)} prices for breakdown"
        )
        return compute_asset_category_breakdown(
            rows,
            price_rows,
            asset_types=self._asset_types,
            currency_guid=currency_guid,
            target_currency=target_currency,
            level=level,
            logger=self._logger,
        )


__all__ = [
    "GetAssetCategoryBreakdownUseCase",
    "AssetCategoryBreakdown",
    "AssetCategoryAmount",
]
