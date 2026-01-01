"""PieCash-backed repository placeholder for GnuCash reporting data."""

from datetime import date
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import piecash  # noqa: F401
except ImportError:  # pragma: no cover - optional dependency
    piecash = None

from src.application.ports.gnucash_repository import (
    AssetCategoryBalanceRow,
    GnuCashRepositoryPort,
    NetWorthBalanceRow,
    PriceRow,
)
from src.infrastructure.logging.logger import get_app_logger


class PieCashGnuCashRepository(GnuCashRepositoryPort):
    """Repository placeholder for PieCash-based GnuCash access."""

    def __init__(self, book_path: Path, logger=None) -> None:
        """Initialize the repository.

        Args:
            book_path: Path to the GnuCash book supported by piecash.
            logger: Optional logger compatible with logging.Logger-like API.
        """
        if piecash is None:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "piecash is not installed; install it to use the piecash backend"
            )
        self._book_path = book_path
        self._logger = logger or get_app_logger()

    def fetch_currency_guid(self, currency: str) -> str:
        """Return the GUID for a currency mnemonic.

        Args:
            currency: Currency mnemonic (e.g., EUR).

        Returns:
            str: GUID for the currency.
        """
        raise NotImplementedError(
            "PieCashGnuCashRepository is a placeholder; "
            "implement fetch_currency_guid before enabling the backend."
        )

    def fetch_net_worth_balances(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> list[NetWorthBalanceRow]:
        """Return balances needed for net worth aggregation.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.

        Returns:
            list[NetWorthBalanceRow]: Balances for net worth aggregation.
        """
        raise NotImplementedError(
            "PieCashGnuCashRepository is a placeholder; "
            "implement fetch_net_worth_balances before enabling the backend."
        )

    def fetch_asset_category_balances(
        self,
        start_date: date | None,
        end_date: date | None,
        actif_root_name: str,
    ) -> list[AssetCategoryBalanceRow]:
        """Return balances grouped by asset category.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.
            actif_root_name: Root account name for asset categories.

        Returns:
            list[AssetCategoryBalanceRow]: Balances grouped by asset categories.
        """
        raise NotImplementedError(
            "PieCashGnuCashRepository is a placeholder; "
            "implement fetch_asset_category_balances before enabling the backend."
        )

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date: date | None,
    ) -> list[PriceRow]:
        """Return the latest price rows per commodity.

        Args:
            currency_guid: GUID for the target currency.
            end_date: Optional upper bound for price dates.

        Returns:
            list[PriceRow]: Latest price rows per commodity.
        """
        raise NotImplementedError(
            "PieCashGnuCashRepository is a placeholder; "
            "implement fetch_latest_prices before enabling the backend."
        )


__all__ = ["PieCashGnuCashRepository"]
