"""Shared helpers for currency conversion in application use cases."""

from datetime import date
from decimal import Decimal
from logging import Logger

from sqlalchemy import text


def coerce_decimal(value) -> Decimal:
    """Normalize numeric values to Decimal.

    Args:
        value: Raw numeric value from SQL.

    Returns:
        Decimal: Normalized numeric value.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def fetch_currency_guid(conn, currency: str) -> str:
    """Fetch the GUID for a currency mnemonic.

    Args:
        conn: SQLAlchemy connection to the GnuCash database.
        currency: Currency mnemonic (e.g., EUR).

    Returns:
        str: GUID for the matching currency commodity.
    """
    query = text(
        """
        SELECT guid
        FROM commodities
        WHERE mnemonic = :currency AND namespace = 'CURRENCY'
        LIMIT 1
        """
    )
    result = conn.execute(query, {"currency": currency}).first()
    if not result:
        raise RuntimeError(f"Missing currency in commodities: {currency}")
    return result.guid


def fetch_latest_prices(
    conn,
    currency_guid: str,
    end_date: date | None,
    logger: Logger,
) -> dict[str, Decimal]:
    """Fetch latest FX rates for each commodity.

    Args:
        conn: SQLAlchemy connection to the GnuCash database.
        currency_guid: GUID of the target currency.
        end_date: Optional upper bound for price dates.
        logger: Logger used for warnings.

    Returns:
        dict[str, Decimal]: Latest FX rate per commodity GUID.
    """
    query = text(
        """
        SELECT commodity_guid, value_num, value_denom, date
        FROM prices
        WHERE currency_guid = :currency_guid
        """
    )
    params = {"currency_guid": currency_guid}
    if end_date:
        query = text(query.text + " AND date <= :end_date")
        params["end_date"] = end_date
    query = text(query.text + " ORDER BY commodity_guid, date DESC")
    rows = conn.execute(query, params).all()

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


__all__ = ["coerce_decimal", "fetch_currency_guid", "fetch_latest_prices", "convert_balance"]
