"""Use case to compute cashflow details for a period."""

from datetime import date
from decimal import Decimal

from src.application.ports.analytics_repository import AnalyticsRepositoryPort
from src.domain.models.finance import (
    CashflowItem,
    CashflowSummary,
    CashflowView,
)
from src.infrastructure.logging.logger import get_app_logger
from src.utils.decimal_utils import coerce_decimal


class GetCashflowUseCase:
    """Compute cashflow summary and details from analytics data."""

    def __init__(
        self,
        gnucash_repository: AnalyticsRepositoryPort,
        logger=None,
        asset_root_name: str = "Actif",
    ) -> None:
        """Initialize the use case.

        Args:
            gnucash_repository: Port providing GnuCash reporting data.
            logger: Optional logger compatible with logging.Logger-like API.
            asset_root_name: Root account name for asset source accounts.
        """
        self._gnucash_repository = gnucash_repository
        self._logger = logger or get_app_logger()
        self._asset_root_name = asset_root_name

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        target_currency: str = "EUR",
    ) -> CashflowView:
        """Return cashflow totals and details for the period.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.
            target_currency: Currency code to filter cashflow rows.

        Returns:
            CashflowView: Summary totals and detailed inflow/outflow items.
        """
        currency_guid = self._gnucash_repository.fetch_currency_guid(
            target_currency
        )
        rows = self._gnucash_repository.fetch_cashflow_rows(
            start_date,
            end_date,
            asset_root_name=self._asset_root_name,
            currency_guid=currency_guid,
        )
        self._logger.info(
            f"Fetched {len(rows)} cashflow rows for {target_currency}"
        )

        incoming_totals: dict[str, Decimal] = {}
        outgoing_totals: dict[str, Decimal] = {}
        incoming_order: list[str] = []
        outgoing_order: list[str] = []
        metadata: dict[str, tuple[str, str | None]] = {}
        for row in rows:
            amount = coerce_decimal(row.amount)
            if amount == 0:
                continue
            if row.account_guid not in metadata:
                metadata[row.account_guid] = (
                    row.account_full_name,
                    row.top_parent_name,
                )
            if amount > 0:
                if row.account_guid not in incoming_totals:
                    incoming_order.append(row.account_guid)
                    incoming_totals[row.account_guid] = amount
                else:
                    incoming_totals[row.account_guid] += amount
            else:
                if row.account_guid not in outgoing_totals:
                    outgoing_order.append(row.account_guid)
                    outgoing_totals[row.account_guid] = abs(amount)
                else:
                    outgoing_totals[row.account_guid] += abs(amount)

        incoming: list[CashflowItem] = []
        outgoing: list[CashflowItem] = []
        total_in = Decimal("0")
        total_out = Decimal("0")
        for account_guid in incoming_order:
            amount = incoming_totals.get(account_guid, Decimal("0"))
            if amount == 0:
                continue
            account_full_name, top_parent_name = metadata[account_guid]
            incoming.append(
                CashflowItem(
                    account_full_name=account_full_name,
                    amount=amount,
                    top_parent_name=top_parent_name,
                )
            )
            total_in += amount
        for account_guid in outgoing_order:
            amount = outgoing_totals.get(account_guid, Decimal("0"))
            if amount == 0:
                continue
            account_full_name, top_parent_name = metadata[account_guid]
            outgoing.append(
                CashflowItem(
                    account_full_name=account_full_name,
                    amount=amount,
                    top_parent_name=top_parent_name,
                )
            )
            total_out += amount

        summary = CashflowSummary(
            total_in=total_in,
            total_out=total_out,
            currency_code=target_currency,
        )
        self._logger.info(
            f"Cashflow totals computed: in={total_in}, out={total_out}, "
            f"currency={target_currency}"
        )
        return CashflowView(
            summary=summary,
            incoming=incoming,
            outgoing=outgoing,
        )


__all__ = ["GetCashflowUseCase", "CashflowView"]
