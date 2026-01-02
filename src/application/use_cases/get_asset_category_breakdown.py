"""Use case to compute asset category breakdown in a target currency."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from src.application.ports.gnucash_repository import GnuCashRepositoryPort
from src.application.use_cases.constants import DEFAULT_ASSET_TYPES
from src.application.use_cases.fx_utils import (
    build_price_map,
    coerce_decimal,
    convert_balance,
)
from src.application.use_cases.gnucash_invariants import (
    normalize_mnemonic,
    normalize_namespace,
    validate_balance_sign,
)
from src.infrastructure.logging.logger import get_app_logger


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


class GetAssetCategoryBreakdownUseCase:
    """Compute asset category breakdown from the GnuCash database."""

    def __init__(
        self,
        gnucash_repository: GnuCashRepositoryPort,
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
        prices = build_price_map(price_rows, self._logger)

        totals: dict[tuple[str | None, str], Decimal] = {}
        for row in rows:
            account_type = row.account_type
            if account_type not in self._asset_types:
                continue
            category = self._resolve_category(row, level)
            parent_category = (
                row.actif_category
                if level == 2
                else None
            )
            if not category:
                continue
            balance = coerce_decimal(row.balance)
            validate_balance_sign(
                account_type,
                balance,
                self._asset_types,
                (),
                self._logger,
            )
            converted = convert_balance(
                balance,
                row.commodity_guid,
                normalize_mnemonic(row.mnemonic),
                normalize_namespace(row.namespace),
                currency_guid,
                target_currency,
                prices,
                self._logger,
            )
            if converted is None:
                continue
            key = (parent_category, category)
            totals[key] = totals.get(key, Decimal("0")) + converted

        categories = [
            AssetCategoryAmount(
                category=category,
                amount=amount,
                parent_category=parent_category,
            )
            for (parent_category, category), amount in sorted(totals.items())
        ]

        return AssetCategoryBreakdown(
            currency_code=target_currency,
            categories=categories,
        )

    @staticmethod
    def _resolve_category(row, level: int) -> str | None:
        if level == 1:
            return row.actif_category
        if level == 2:
            return row.actif_subcategory
        return row.actif_category


__all__ = [
    "GetAssetCategoryBreakdownUseCase",
    "AssetCategoryBreakdown",
    "AssetCategoryAmount",
]
