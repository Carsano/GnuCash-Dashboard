from __future__ import annotations

from datetime import date
from decimal import Decimal


def test_get_budget_monthly_targets_use_case_normalizes_month_and_sorts() -> None:
    from src.application.use_cases.get_budget_monthly_targets import (
        GetBudgetMonthlyTargetsUseCase,
    )
    from src.domain.models.budget import BudgetAccountMonthlyTargetDTO

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            assert budget_guid == "b1"
            assert month_start == date(2026, 2, 1)
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="a-exp-2",
                    amount=Decimal("0"),
                ),
                BudgetAccountMonthlyTargetDTO(
                    account_guid="a-exp-1",
                    amount=Decimal("12.50"),
                ),
            ]

    use_case = GetBudgetMonthlyTargetsUseCase(repository=_Repo())
    result = use_case.execute(
        budget_guid="b1",
        month_start=date(2026, 2, 19),
    )
    assert [(row.account_guid, row.amount) for row in result] == [
        ("a-exp-1", Decimal("12.50")),
        ("a-exp-2", Decimal("0")),
    ]


def test_get_budget_monthly_targets_use_case_preserves_zero_and_missing_semantics() -> None:
    from src.application.use_cases.get_budget_monthly_targets import (
        GetBudgetMonthlyTargetsUseCase,
    )
    from src.domain.models.budget import BudgetAccountMonthlyTargetDTO

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="expense-with-zero",
                    amount=Decimal("0"),
                )
            ]

    use_case = GetBudgetMonthlyTargetsUseCase(repository=_Repo())
    result = use_case.execute(
        budget_guid="b1",
        month_start=date(2026, 1, 1),
    )
    by_guid = {row.account_guid: row.amount for row in result}
    assert by_guid["expense-with-zero"] == Decimal("0")
    assert "expense-without-row" not in by_guid
