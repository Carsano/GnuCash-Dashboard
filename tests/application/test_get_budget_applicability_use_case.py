from __future__ import annotations

from datetime import date

from src.application.ports.budget_repository import BudgetsUnsupportedBackendError
from src.domain.models.budget import (
    BudgetApplicabilityDTO,
    BudgetInapplicableReason,
)


def test_get_budget_applicability_use_case_returns_repository_result() -> None:
    from src.application.use_cases.get_budget_applicability import (
        GetBudgetApplicabilityUseCase,
    )

    class _Repo:
        def fetch_budget_applicability(self, *, budget_guid: str, month_start: date):
            assert budget_guid == "b1"
            assert month_start == date(2026, 2, 1)
            return BudgetApplicabilityDTO(
                applicable=False,
                reason=BudgetInapplicableReason.OUT_OF_RANGE,
            )

    use_case = GetBudgetApplicabilityUseCase(repository=_Repo())
    result = use_case.execute(budget_guid="b1", month_start=date(2026, 2, 1))
    assert result == BudgetApplicabilityDTO(
        applicable=False,
        reason=BudgetInapplicableReason.OUT_OF_RANGE,
    )


def test_get_budget_applicability_use_case_maps_backend_errors_to_data_unavailable() -> None:
    from src.application.use_cases.get_budget_applicability import (
        GetBudgetApplicabilityUseCase,
    )

    class _Repo:
        def fetch_budget_applicability(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            raise BudgetsUnsupportedBackendError(backend="analytics")

    use_case = GetBudgetApplicabilityUseCase(repository=_Repo())
    result = use_case.execute(budget_guid="b1", month_start=date(2026, 2, 1))
    assert result == BudgetApplicabilityDTO(
        applicable=False,
        reason=BudgetInapplicableReason.DATA_UNAVAILABLE,
    )


def test_get_budget_applicability_use_case_maps_unknown_errors_to_data_unavailable() -> None:
    from src.application.use_cases.get_budget_applicability import (
        GetBudgetApplicabilityUseCase,
    )

    class _Repo:
        def fetch_budget_applicability(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            raise RuntimeError("boom")

    use_case = GetBudgetApplicabilityUseCase(repository=_Repo())
    result = use_case.execute(budget_guid="b1", month_start=date(2026, 2, 1))
    assert result == BudgetApplicabilityDTO(
        applicable=False,
        reason=BudgetInapplicableReason.DATA_UNAVAILABLE,
    )

