from __future__ import annotations

from datetime import date
from decimal import Decimal


def test_get_budget_monthly_actuals_use_case_normalizes_month_and_sorts() -> None:
    from src.application.use_cases.get_budget_monthly_actuals import (
        GetBudgetMonthlyActualsUseCase,
    )
    from src.domain.models.budget import AccountMonthlyActualDTO

    class _Repo:
        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            assert month_start == date(2026, 2, 1)
            return [
                AccountMonthlyActualDTO(
                    account_guid="a-exp-2",
                    amount=Decimal("-7.00"),
                ),
                AccountMonthlyActualDTO(
                    account_guid="a-exp-1",
                    amount=Decimal("12.50"),
                ),
            ]

    use_case = GetBudgetMonthlyActualsUseCase(repository=_Repo())
    result = use_case.execute(month_start=date(2026, 2, 19))
    assert [(row.account_guid, row.amount) for row in result] == [
        ("a-exp-1", Decimal("12.50")),
        ("a-exp-2", Decimal("7.00")),
    ]


def test_get_budget_monthly_actuals_use_case_returns_new_list() -> None:
    from src.application.use_cases.get_budget_monthly_actuals import (
        GetBudgetMonthlyActualsUseCase,
    )
    from src.domain.models.budget import AccountMonthlyActualDTO

    rows = [
        AccountMonthlyActualDTO(
            account_guid="a-exp-1",
            amount=Decimal("1"),
        )
    ]

    class _Repo:
        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            _ = month_start
            return rows

    use_case = GetBudgetMonthlyActualsUseCase(repository=_Repo())
    result = use_case.execute(month_start=date(2026, 1, 1))
    assert result == rows
    assert result is not rows
