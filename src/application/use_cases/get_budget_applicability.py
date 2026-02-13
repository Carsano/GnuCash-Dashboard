"""Use case to determine if a selected budget applies to a given month."""

from __future__ import annotations

from datetime import date

from src.application.ports.budget_repository import (
    BudgetsUnsupportedBackendError,
    BudgetRepositoryPort,
)
from src.domain.models.budget import (
    BudgetApplicabilityDTO,
    BudgetInapplicableReason,
)


class GetBudgetApplicabilityUseCase:
    """Check whether the selected budget can be applied for the given month."""

    def __init__(self, repository: BudgetRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        budget_guid: str,
        month_start: date,
    ) -> BudgetApplicabilityDTO:
        normalized_month_start = date(month_start.year, month_start.month, 1)
        try:
            return self._repository.fetch_budget_applicability(
                budget_guid=budget_guid,
                month_start=normalized_month_start,
            )
        except BudgetsUnsupportedBackendError:
            return BudgetApplicabilityDTO(
                applicable=False,
                reason=BudgetInapplicableReason.DATA_UNAVAILABLE,
            )
        except Exception:
            return BudgetApplicabilityDTO(
                applicable=False,
                reason=BudgetInapplicableReason.DATA_UNAVAILABLE,
            )


__all__ = ["GetBudgetApplicabilityUseCase"]
