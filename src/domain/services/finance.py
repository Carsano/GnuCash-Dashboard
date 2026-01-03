"""Domain services for finance aggregates."""

from collections.abc import Iterable
from decimal import Decimal
from logging import Logger

from src.domain.models import (
    AssetCategoryAmount,
    AssetCategoryBalanceRow,
    AssetCategoryBreakdown,
    NetWorthBalanceRow,
    NetWorthSummary,
    PriceRow,
)
from src.domain.services.fx import build_price_map, convert_balance
from src.domain.services.normalization import (
    normalize_mnemonic,
    normalize_namespace,
)
from src.domain.services.validation import validate_balance_sign
from src.utils.decimal_utils import coerce_decimal


def compute_net_worth_summary(
    balances: list[NetWorthBalanceRow],
    prices: list[PriceRow],
    *,
    asset_types: Iterable[str],
    liability_types: Iterable[str],
    currency_guid: str,
    target_currency: str,
    logger: Logger,
) -> NetWorthSummary:
    """Compute net worth totals from balances and prices.

    Args:
        balances: Net worth balances from the repository.
        prices: Latest price rows for FX conversion.
        asset_types: Account types treated as assets.
        liability_types: Account types treated as liabilities.
        currency_guid: GUID of the target currency.
        target_currency: Target currency mnemonic.
        logger: Logger used for warnings.

    Returns:
        NetWorthSummary: Computed asset, liability, and net worth totals.
    """
    prices_map = build_price_map(prices, logger)
    asset_total = Decimal("0")
    liability_total = Decimal("0")

    for row in balances:
        account_type = row.account_type
        if (
            account_type not in asset_types
            and account_type not in liability_types
        ):
            continue
        balance = coerce_decimal(row.balance)
        validate_balance_sign(
            account_type,
            balance,
            asset_types,
            liability_types,
            logger,
        )
        converted = convert_balance(
            balance,
            row.commodity_guid,
            normalize_mnemonic(row.mnemonic),
            normalize_namespace(row.namespace),
            currency_guid,
            target_currency,
            prices_map,
            logger,
        )
        if converted is None:
            continue
        if account_type in asset_types:
            asset_total += converted
        else:
            liability_total += abs(converted)

    net_worth = asset_total - liability_total
    return NetWorthSummary(
        asset_total=asset_total,
        liability_total=liability_total,
        net_worth=net_worth,
        currency_code=target_currency,
    )


def compute_asset_category_breakdown(
    rows: list[AssetCategoryBalanceRow],
    prices: list[PriceRow],
    *,
    asset_types: Iterable[str],
    currency_guid: str,
    target_currency: str,
    level: int,
    logger: Logger,
) -> AssetCategoryBreakdown:
    """Compute asset breakdown totals from balances and prices.

    Args:
        rows: Asset category balances from the repository.
        prices: Latest price rows for FX conversion.
        asset_types: Account types treated as assets.
        currency_guid: GUID of the target currency.
        target_currency: Target currency mnemonic.
        level: Depth level under the Actif root (1 or 2).
        logger: Logger used for warnings.

    Returns:
        AssetCategoryBreakdown: Aggregated asset totals by category.
    """
    prices_map = build_price_map(prices, logger)
    totals: dict[tuple[str | None, str], Decimal] = {}
    for row in rows:
        account_type = row.account_type
        if account_type not in asset_types:
            continue
        category = _resolve_category(row, level)
        parent_category = row.actif_category if level == 2 else None
        if not category:
            continue
        balance = coerce_decimal(row.balance)
        validate_balance_sign(
            account_type,
            balance,
            asset_types,
            (),
            logger,
        )
        converted = convert_balance(
            balance,
            row.commodity_guid,
            normalize_mnemonic(row.mnemonic),
            normalize_namespace(row.namespace),
            currency_guid,
            target_currency,
            prices_map,
            logger,
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


def _resolve_category(
    row: AssetCategoryBalanceRow,
    level: int,
) -> str | None:
    if level == 1:
        return row.actif_category
    if level == 2:
        return row.actif_subcategory
    return row.actif_category


__all__ = [
    "compute_net_worth_summary",
    "compute_asset_category_breakdown",
]
