"""Domain models for budget (single-month view)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal

BudgetStatusLabel = Literal["No budget", "On track", "Close", "Over"]

class BudgetInapplicableReason(str, Enum):
    """Structured reason codes for "budget cannot be applied" states."""

    OUT_OF_RANGE = "out_of_range"
    NO_TARGETS = "no_targets"
    DATA_UNAVAILABLE = "data_unavailable"


@dataclass(frozen=True)
class BudgetDTO:
    """Serializable representation of a GnuCash budget."""

    guid: str
    name: str
    num_periods: int


@dataclass(frozen=True)
class BudgetAccountMonthlyTargetDTO:
    """Budget target for a single account in a specific month."""

    account_guid: str
    amount: Decimal


@dataclass(frozen=True)
class AccountMonthlyActualDTO:
    """Actual spending total for a single account in a specific month."""

    account_guid: str
    amount: Decimal


@dataclass(frozen=True)
class BudgetMonthSummaryDTO:
    """Overall summary totals for a single-month budget view."""

    total_budget: Decimal
    total_actual: Decimal
    total_remaining: Decimal
    total_over: Decimal
    status_label: BudgetStatusLabel


@dataclass(frozen=True)
class BudgetMonthNodeResultDTO:
    """Per-node result row for a single-month budget view."""

    node_guid: str
    node_path: str
    budget: Decimal
    actual: Decimal
    remaining: Decimal
    over: Decimal
    status_label: BudgetStatusLabel
    no_budget: bool

    def __post_init__(self) -> None:
        if self.no_budget:
            if self.budget != Decimal("0"):
                raise ValueError(
                    "no_budget=True requires budget=0 to avoid ambiguity."
                )
            if self.status_label != "No budget":
                raise ValueError(
                    "no_budget=True requires status_label='No budget'."
                )
        elif self.status_label == "No budget":
            raise ValueError(
                "status_label='No budget' requires no_budget=True."
            )


@dataclass(frozen=True)
class BudgetMonthViewDTO:
    """Budget month view DTO: summary + ordered per-node results.

    Contract: `node_results` MUST be sorted deterministically using
    `budget_node_sort_key`.
    """

    summary: BudgetMonthSummaryDTO
    node_results: list[BudgetMonthNodeResultDTO]


@dataclass(frozen=True)
class BudgetApplicabilityDTO:
    """Applicability result for a budget in a given single-month context."""

    applicable: bool
    reason: BudgetInapplicableReason | None

    def __post_init__(self) -> None:
        if self.applicable and self.reason is not None:
            raise ValueError("applicable=True requires reason=None.")
        if not self.applicable and self.reason is None:
            raise ValueError("applicable=False requires a reason.")


def budget_node_sort_key(node: BudgetMonthNodeResultDTO) -> tuple[str, str]:
    """Deterministic, case-insensitive sort key for node results."""

    return (node.node_path.casefold(), node.node_guid)


def sort_budget_node_results(
    node_results: list[BudgetMonthNodeResultDTO],
) -> list[BudgetMonthNodeResultDTO]:
    """Return deterministically ordered node results."""

    return sorted(node_results, key=budget_node_sort_key)


def budget_status_label_from_values(
    *,
    no_budget: bool,
    budget: Decimal,
    actual: Decimal,
    close_threshold: Decimal | None = None,
) -> BudgetStatusLabel:
    """Return a status label from explicit semantics and numeric values.

    Notes:
      - `no_budget=True` is authoritative (distinct from `budget=0`).
      - "Close" is optional and only applied when `close_threshold` is provided.
    """

    if no_budget:
        return "No budget"
    if actual > budget:
        return "Over"
    remaining = budget - actual
    if (
        close_threshold is not None
        and remaining > 0
        and remaining <= close_threshold
    ):
        return "Close"
    return "On track"


__all__ = [
    "BudgetApplicabilityDTO",
    "AccountMonthlyActualDTO",
    "BudgetAccountMonthlyTargetDTO",
    "BudgetDTO",
    "BudgetInapplicableReason",
    "BudgetMonthNodeResultDTO",
    "BudgetMonthSummaryDTO",
    "BudgetMonthViewDTO",
    "BudgetStatusLabel",
    "budget_node_sort_key",
    "budget_status_label_from_values",
    "sort_budget_node_results",
]
