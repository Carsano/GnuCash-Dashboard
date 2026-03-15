"""Helpers for Decimal normalization."""

from decimal import Decimal, ROUND_HALF_UP


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


def quantize_currency(value: Decimal, *, places: int = 2) -> Decimal:
    """Quantize a Decimal to currency precision using half-up rounding."""

    exponent = Decimal("1").scaleb(-places)
    return value.quantize(exponent, rounding=ROUND_HALF_UP)


__all__ = ["coerce_decimal", "quantize_currency"]
