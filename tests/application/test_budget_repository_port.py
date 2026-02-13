from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import get_type_hints


def test_budget_repository_port_imports_and_hints_resolve() -> None:
    from src.application.ports.budget_repository import BudgetRepositoryPort

    hints = get_type_hints(BudgetRepositoryPort.fetch_budgets)
    assert "return" in hints

    hints = get_type_hints(BudgetRepositoryPort.fetch_monthly_budget_targets)
    assert hints["month_start"] is date
    assert "return" in hints

    hints = get_type_hints(BudgetRepositoryPort.fetch_monthly_actuals_by_account)
    assert hints["month_start"] is date
    assert "return" in hints

    hints = get_type_hints(BudgetRepositoryPort.fetch_budget_applicability)
    assert hints["month_start"] is date
    assert "return" in hints


def test_budget_repository_port_can_be_implemented_by_fake() -> None:
    from src.application.ports.budget_repository import BudgetRepositoryPort
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
        BudgetApplicabilityDTO,
        BudgetDTO,
        BudgetInapplicableReason,
    )

    class FakeBudgetRepository(BudgetRepositoryPort):
        def fetch_budgets(self) -> list[BudgetDTO]:
            return [BudgetDTO(guid="b1", name="Budget 1", num_periods=12)]

        def fetch_monthly_budget_targets(
            self,
            *,
            budget_guid: str,
            month_start: date,
        ) -> list[BudgetAccountMonthlyTargetDTO]:
            _ = budget_guid, month_start
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="a1",
                    amount=Decimal("0"),
                )
            ]

        def fetch_monthly_actuals_by_account(
            self,
            *,
            month_start: date,
        ) -> list[AccountMonthlyActualDTO]:
            _ = month_start
            return [
                AccountMonthlyActualDTO(
                    account_guid="a1",
                    amount=Decimal("0"),
                )
            ]

        def fetch_budget_applicability(
            self,
            *,
            budget_guid: str,
            month_start: date,
        ) -> BudgetApplicabilityDTO:
            _ = budget_guid, month_start
            return BudgetApplicabilityDTO(
                applicable=True,
                reason=None,
            )

    repo = FakeBudgetRepository()
    assert repo.fetch_budgets()[0].guid == "b1"
