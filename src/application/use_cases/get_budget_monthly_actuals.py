"""Use case to load monthly budget actuals by account."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.application.ports.budget_repository import BudgetRepositoryPort
from src.domain.models.budget import AccountMonthlyActualDTO


class GetBudgetMonthlyActualsUseCase:
    """Fetch per-account monthly actuals with normalized deterministic output."""

    def __init__(self, repository: BudgetRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        month_start: date,
    ) -> list[AccountMonthlyActualDTO]:
        normalized_month_start = date(month_start.year, month_start.month, 1)
        rows = list(
            self._repository.fetch_monthly_actuals_by_account(
                month_start=normalized_month_start,
            )
        )
        normalized_rows = [
            AccountMonthlyActualDTO(
                account_guid=row.account_guid,
                amount=abs(Decimal(row.amount)),
            )
            for row in rows
        ]
        return sorted(normalized_rows, key=lambda row: row.account_guid)


__all__ = ["GetBudgetMonthlyActualsUseCase"]
