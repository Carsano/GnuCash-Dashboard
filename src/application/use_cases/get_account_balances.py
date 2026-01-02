"""Use case to compute account balances for tree display."""

from datetime import date

from src.application.ports.analytics_repository import AnalyticsRepositoryPort
from src.domain.models.accounts import AccountBalanceDTO
from src.domain.services.fx import build_price_map, convert_balance
from src.infrastructure.logging.logger import get_app_logger


class GetAccountBalancesUseCase:
    """Compute account balances in a target currency."""

    def __init__(
        self,
        gnucash_repository: AnalyticsRepositoryPort,
        logger=None,
    ) -> None:
        """Initialize the use case.

        Args:
            gnucash_repository: Port providing GnuCash reporting data.
            logger: Optional logger compatible with logging.Logger-like API.
        """
        self._gnucash_repository = gnucash_repository
        self._logger = logger or get_app_logger()

    def execute(
        self,
        end_date: date | None = None,
        target_currency: str = "EUR",
    ) -> list[AccountBalanceDTO]:
        """Return account balances converted to the target currency.

        Args:
            end_date: Optional upper bound for transaction post dates.
            target_currency: Currency mnemonic for conversions.

        Returns:
            list[AccountBalanceDTO]: Account balances for UI rendering.
        """
        currency_guid = self._gnucash_repository.fetch_currency_guid(
            target_currency
        )
        rows = self._gnucash_repository.fetch_account_balances(end_date)
        price_rows = self._gnucash_repository.fetch_latest_prices(
            currency_guid,
            end_date,
        )
        prices = build_price_map(price_rows, logger=self._logger)
        balances = []
        for row in rows:
            converted = convert_balance(
                row.balance,
                row.commodity_guid or "",
                row.mnemonic or "",
                row.namespace or "",
                currency_guid,
                target_currency,
                prices,
                logger=self._logger,
            )
            if converted is None:
                continue
            if row.account_type in ("INCOME", "LIABILITY"):
                converted = -converted
            balances.append(
                AccountBalanceDTO(
                    guid=row.guid,
                    name=row.name,
                    account_type=row.account_type,
                    parent_guid=row.parent_guid,
                    balance=converted,
                    currency_code=target_currency,
                )
            )
        balances = sorted(
            balances,
            key=lambda item: (item.name.lower(), item.guid),
        )
        self._logger.info(
            f"Fetched {len(balances)} account balances for {target_currency}"
        )
        return balances


__all__ = ["GetAccountBalancesUseCase", "AccountBalanceDTO"]
