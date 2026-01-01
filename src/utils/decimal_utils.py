"""Helpers for Decimal normalization."""

from decimal import Decimal


def coerce_decimal(value) -> Decimal:
    """Normalize numeric values to Decimal.

    Args:
        value: Raw numeric value from SQL or adapters.

    Returns:
        Decimal: Normalized numeric value.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


__all__ = ["coerce_decimal"]
