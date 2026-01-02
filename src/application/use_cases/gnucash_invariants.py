"""Invariant checks for GnuCash repository data."""

from collections.abc import Iterable
from decimal import Decimal
from logging import Logger


def normalize_namespace(namespace: str | None) -> str | None:
    """Normalize commodity namespace values.

    Args:
        namespace: Raw namespace value from a repository.

    Returns:
        str | None: Normalized namespace value.
    """
    if not namespace:
        return None
    cleaned = namespace.strip()
    return cleaned.upper() if cleaned else None


def normalize_mnemonic(mnemonic: str | None) -> str | None:
    """Normalize commodity mnemonic values.

    Args:
        mnemonic: Raw mnemonic value from a repository.

    Returns:
        str | None: Normalized mnemonic value.
    """
    if not mnemonic:
        return None
    cleaned = mnemonic.strip()
    return cleaned.upper() if cleaned else None


def validate_balance_sign(
    account_type: str,
    balance: Decimal,
    asset_types: Iterable[str],
    liability_types: Iterable[str],
    logger: Logger,
) -> None:
    """Warn when balances violate expected sign conventions.

    Args:
        account_type: Account type from the repository row.
        balance: Raw balance amount.
        asset_types: Account types treated as assets.
        liability_types: Account types treated as liabilities.
        logger: Logger used for warnings.
    """
    if account_type in asset_types and balance < 0:
        logger.warning(
            f"Asset balance is negative for account_type={account_type}: {balance}"
        )
    if account_type in liability_types and balance > 0:
        logger.warning(
            f"Liability balance is positive for account_type={account_type}: {balance}"
        )


__all__ = [
    "normalize_namespace",
    "normalize_mnemonic",
    "validate_balance_sign",
]
