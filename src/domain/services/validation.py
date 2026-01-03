"""Domain validation helpers."""

from collections.abc import Iterable
from decimal import Decimal
from logging import Logger


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


__all__ = ["validate_balance_sign"]
