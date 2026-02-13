"""Use case to load monthly budget targets for a selected budget/month."""

from __future__ import annotations

from datetime import date

from src.application.ports.budget_repository import BudgetRepositoryPort
from src.domain.models.budget import BudgetAccountMonthlyTargetDTO


class GetBudgetMonthlyTargetsUseCase:
    """Fetch per-account monthly targets with deterministic ordering."""

    def __init__(self, repository: BudgetRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        budget_guid: str,
        month_start: date,
    ) -> list[BudgetAccountMonthlyTargetDTO]:
        normalized_month_start = date(month_start.year, month_start.month, 1)
        targets = list(
            self._repository.fetch_monthly_budget_targets(
                budget_guid=budget_guid,
                month_start=normalized_month_start,
            )
        )
        return sorted(targets, key=lambda row: row.account_guid)


__all__ = ["GetBudgetMonthlyTargetsUseCase"]
