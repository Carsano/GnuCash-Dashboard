"""Port for reading budget (GnuCash Budgets + monthly targets + monthly actuals).

Notes:
  - This port returns per-account inputs (account GUID keyed). Higher-level node
    totals are derived in the application layer by aggregating account values
    across the expense tree.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from src.domain.models.budget import (
    AccountMonthlyActualDTO,
    BudgetApplicabilityDTO,
    BudgetAccountMonthlyTargetDTO,
    BudgetDTO,
)


class BudgetsUnsupportedBackendError(RuntimeError):
    """Raised when budgets are requested from an unsupported backend."""

    def __init__(self, *, backend: str) -> None:
        super().__init__(
            "Budgets are not available for the configured backend "
            f"(GNUCASH_BACKEND={backend}). "
            "Use GNUCASH_BACKEND=sqlalchemy for budgets."
        )
        self.backend = backend


class BudgetRepositoryPort(Protocol):
    """Port exposing read access for budget-related queries."""

    def fetch_budgets(self) -> list[BudgetDTO]:
        """Return the available budgets.

        Contract: results MUST be deterministic across runs. Implementations
        should sort by `(name.casefold(), guid)` at the application boundary if
        the backend does not guarantee ordering.
        """

    def fetch_monthly_budget_targets(
        self,
        *,
        budget_guid: str,
        month_start: date,
    ) -> list[BudgetAccountMonthlyTargetDTO]:
        """Return per-account budget targets for the given budget and month.

        Contract:
          - `month_start` MUST be the first day of the month being queried.
          - Totals must cover the entire calendar month starting at `month_start`.
          - Results MUST be deterministic (e.g., sort by `account_guid`).
        """

    def fetch_monthly_actuals_by_account(
        self,
        *,
        month_start: date,
    ) -> list[AccountMonthlyActualDTO]:
        """Return per-account actual spending totals for the given month.

        `account_guid` is a GnuCash account GUID. Node-level totals are computed
        by summing the accounts in a node's subtree.

        Contract:
          - `month_start` MUST be the first day of the month being queried.
          - Totals must cover the entire calendar month starting at `month_start`.
          - Results MUST be deterministic (e.g., sort by `account_guid`).
        """

    def fetch_budget_applicability(
        self,
        *,
        budget_guid: str,
        month_start: date,
    ) -> BudgetApplicabilityDTO:
        """Return applicability for the given budget in the given month.

        Contract:
          - `month_start` MUST be the first day of the month being queried.
          - Implementations SHOULD return structured reasons for inapplicable
            states (e.g., out-of-range or no targets) rather than raising.
          - Results MUST be deterministic.
        """


__all__ = ["BudgetsUnsupportedBackendError", "BudgetRepositoryPort"]
