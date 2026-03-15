from __future__ import annotations

from datetime import date
from decimal import Decimal


def test_get_budgets_use_case_sorts_deterministically() -> None:
    from src.application.use_cases.get_budgets import GetBudgetsUseCase
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
        BudgetDTO,
    )

    class _FakeBudgetRepository:
        def fetch_budgets(self) -> list[BudgetDTO]:
            return [
                BudgetDTO(guid="b", name="Zoo", num_periods=12),
                BudgetDTO(guid="a", name="alpha", num_periods=12),
                BudgetDTO(guid="c", name="Alpha", num_periods=12),
            ]

        def fetch_monthly_budget_targets(
            self,
            *,
            budget_guid: str,
            month_start: date,
        ) -> list[BudgetAccountMonthlyTargetDTO]:
            _ = budget_guid, month_start
            return []

        def fetch_monthly_actuals_by_account(
            self,
            *,
            month_start: date,
        ) -> list[AccountMonthlyActualDTO]:
            _ = month_start
            return []

    use_case = GetBudgetsUseCase(repository=_FakeBudgetRepository())
    result = use_case.execute()
    assert [(b.name, b.guid) for b in result] == [
        ("alpha", "a"),
        ("Alpha", "c"),
        ("Zoo", "b"),
    ]


def test_get_budgets_use_case_returns_new_list() -> None:
    from src.application.use_cases.get_budgets import GetBudgetsUseCase
    from src.domain.models.budget import BudgetDTO

    budgets = [BudgetDTO(guid="a", name="A", num_periods=1)]

    class _FakeBudgetRepository:
        def fetch_budgets(self) -> list[BudgetDTO]:
            return budgets

    use_case = GetBudgetsUseCase(repository=_FakeBudgetRepository())
    result = use_case.execute()

    assert result == budgets
    assert result is not budgets

