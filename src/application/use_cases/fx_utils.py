"""Shared helpers for currency conversion in application use cases."""

from decimal import Decimal
from logging import Logger

from src.application.ports.gnucash_repository import PriceRow
from src.utils.decimal_utils import coerce_decimal


def build_price_map(
    rows: list[PriceRow],
    logger: Logger,
) -> dict[str, Decimal]:
    """Build the latest FX rate mapping from price rows.

    Args:
        rows: Price rows sorted by commodity/date (newest first).
        logger: Logger used for warnings.

    Returns:
        dict[str, Decimal]: Latest FX rate per commodity GUID.
    """
    rates: dict[str, Decimal] = {}
    for row in rows:
        if row.commodity_guid in rates:
            continue
        denom = coerce_decimal(row.value_denom)
        if denom == 0:
            logger.warning(
                "Skipping FX rate with zero denominator "
                f"for {row.commodity_guid}"
            )
            continue
        rates[row.commodity_guid] = coerce_decimal(row.value_num) / denom
    return rates


def convert_balance(
    balance: Decimal,
    commodity_guid: str,
    mnemonic: str,
    namespace: str,
    target_guid: str,
    target_currency: str,
    prices: dict[str, Decimal],
    logger: Logger,
) -> Decimal | None:
    """Convert a balance into the target currency.

    Args:
        balance: Balance in the source currency.
        commodity_guid: GUID for the account commodity.
        mnemonic: Commodity mnemonic (e.g., EUR).
        namespace: Commodity namespace.
        target_guid: GUID of the target currency.
        target_currency: Target currency mnemonic.
        prices: Mapping of commodity GUID to FX rate.
        logger: Logger used for warnings.

    Returns:
        Decimal | None: Converted balance or None when conversion is not possible.
    """
    if not commodity_guid or not mnemonic:
        logger.warning("Skipping account with missing commodity info")
        return None
    if namespace.upper() == "TEMPLATE" or mnemonic.lower() == "template":
        return None
    if namespace == "CURRENCY" and (
        commodity_guid == target_guid or mnemonic == target_currency
    ):
        return balance
    rate = prices.get(commodity_guid)
    if rate is None:
        logger.warning(
            f"Missing FX rate for {mnemonic} to {target_currency}"
        )
        return None
    return balance * rate


__all__ = ["coerce_decimal", "build_price_map", "convert_balance"]
