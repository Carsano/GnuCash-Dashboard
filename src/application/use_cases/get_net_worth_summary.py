"""Use case to compute net worth from the GnuCash database."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from src.application.ports.gnucash_repository import GnuCashRepositoryPort
from src.application.use_cases.constants import (
    DEFAULT_ASSET_TYPES,
    DEFAULT_LIABILITY_TYPES,
)
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
class NetWorthSummary:
    """Summary of net worth figures.

    Attributes:
        asset_total: Sum of asset balances.
        liability_total: Sum of liability balances.
        net_worth: Assets minus liabilities.
    """

    asset_total: Decimal
    liability_total: Decimal
    net_worth: Decimal
    currency_code: str


class GetNetWorthSummaryUseCase:
    """Compute net worth from the GnuCash database."""

    def __init__(
        self,
        gnucash_repository: GnuCashRepositoryPort,
        logger=None,
        asset_types: Iterable[str] | None = None,
        liability_types: Iterable[str] | None = None,
    ) -> None:
        """Initialize the use case.

        Args:
            gnucash_repository: Port providing GnuCash reporting data.
            logger: Optional logger compatible with logging.Logger-like API.
            asset_types: Optional iterable of account types treated as assets.
            liability_types: Optional iterable treated as liabilities.
        """
        self._gnucash_repository = gnucash_repository
        self._logger = logger or get_app_logger()
        self._asset_types = tuple(asset_types or DEFAULT_ASSET_TYPES)
        self._liability_types = tuple(
            liability_types or DEFAULT_LIABILITY_TYPES
        )

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        target_currency: str = "EUR",
    ) -> NetWorthSummary:
        """Return the net worth summary.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.

        Returns:
            NetWorthSummary: Computed asset, liability, and net worth totals.
        """
        currency_guid = self._gnucash_repository.fetch_currency_guid(
            target_currency
        )
        balances = self._gnucash_repository.fetch_net_worth_balances(
            start_date,
            end_date,
        )
        price_rows = self._gnucash_repository.fetch_latest_prices(
            currency_guid,
            end_date,
        )
        self._logger.info(
            f"Fetched {len(balances)} balances and "
            f"{len(price_rows)} prices for net worth"
        )
        prices = build_price_map(price_rows, self._logger)

        asset_total = Decimal("0")
        liability_total = Decimal("0")

        for row in balances:
            account_type = row.account_type
            if (
                account_type not in self._asset_types
                and account_type not in self._liability_types
            ):
                continue
            balance = coerce_decimal(row.balance)
            validate_balance_sign(
                account_type,
                balance,
                self._asset_types,
                self._liability_types,
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
            if account_type in self._asset_types:
                asset_total += converted
            else:
                liability_total += abs(converted)

        net_worth = asset_total - liability_total

        self._logger.info(
            f"Net worth computed: assets={asset_total}, "
            f"liabilities={liability_total}, currency={target_currency}"
        )

        return NetWorthSummary(
            asset_total=asset_total,
            liability_total=liability_total,
            net_worth=net_worth,
            currency_code=target_currency,
        )

__all__ = ["GetNetWorthSummaryUseCase", "NetWorthSummary"]
