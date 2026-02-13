"""Use case to read available budgets for presentation layers."""

from __future__ import annotations

from src.application.ports.budget_repository import BudgetRepositoryPort
from src.domain.models.budget import BudgetDTO


class GetBudgetsUseCase:
    """Fetch budgets from the configured backend."""

    def __init__(self, repository: BudgetRepositoryPort) -> None:
        self._repository = repository

    def execute(self) -> list[BudgetDTO]:
        budgets = list(self._repository.fetch_budgets())
        return sorted(
            budgets,
            key=lambda budget: (budget.name.casefold(), budget.guid),
        )


__all__ = ["GetBudgetsUseCase", "BudgetDTO"]

