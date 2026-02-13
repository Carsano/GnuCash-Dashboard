from dataclasses import is_dataclass
from decimal import Decimal
from typing import get_args

import pytest


def test_budget_month_view_dtos_are_dataclasses() -> None:
    from src.domain.models.budget import (
        BudgetMonthNodeResultDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    assert is_dataclass(BudgetMonthSummaryDTO)
    assert is_dataclass(BudgetMonthNodeResultDTO)
    assert is_dataclass(BudgetMonthViewDTO)


def test_budget_node_sort_key_is_deterministic_case_insensitive() -> None:
    from src.domain.models.budget import (
        BudgetMonthNodeResultDTO,
        budget_node_sort_key,
    )

    a = BudgetMonthNodeResultDTO(
        node_guid="b-guid",
        node_path="Expenses:Food",
        budget=Decimal("1"),
        actual=Decimal("0"),
        remaining=Decimal("1"),
        over=Decimal("0"),
        status_label="On track",
        no_budget=False,
    )
    b = BudgetMonthNodeResultDTO(
        node_guid="a-guid",
        node_path="expenses:food",
        budget=Decimal("1"),
        actual=Decimal("0"),
        remaining=Decimal("1"),
        over=Decimal("0"),
        status_label="On track",
        no_budget=False,
    )

    results = sorted([a, b], key=budget_node_sort_key)
    assert [r.node_guid for r in results] == ["a-guid", "b-guid"]


def test_budget_status_labels_include_epic_vocabulary() -> None:
    from src.domain.models.budget import BudgetStatusLabel

    assert set(get_args(BudgetStatusLabel)) == {
        "No budget",
        "On track",
        "Close",
        "Over",
    }


def test_budget_status_label_from_values_respects_no_budget() -> None:
    from src.domain.models.budget import budget_status_label_from_values

    assert (
        budget_status_label_from_values(
            no_budget=True,
            budget=Decimal("0"),
            actual=Decimal("0"),
        )
        == "No budget"
    )


def test_budget_status_label_from_values_handles_over_close_on_track() -> None:
    from src.domain.models.budget import budget_status_label_from_values

    assert (
        budget_status_label_from_values(
            no_budget=False,
            budget=Decimal("100"),
            actual=Decimal("101"),
        )
        == "Over"
    )

    assert (
        budget_status_label_from_values(
            no_budget=False,
            budget=Decimal("100"),
            actual=Decimal("99"),
            close_threshold=Decimal("2"),
        )
        == "Close"
    )

    assert (
        budget_status_label_from_values(
            no_budget=False,
            budget=Decimal("100"),
            actual=Decimal("50"),
            close_threshold=Decimal("2"),
        )
        == "On track"
    )


def test_budget_month_node_result_invariants() -> None:
    from src.domain.models.budget import BudgetMonthNodeResultDTO

    with pytest.raises(ValueError):
        BudgetMonthNodeResultDTO(
            node_guid="n1",
            node_path="Expenses",
            budget=Decimal("1"),
            actual=Decimal("0"),
            remaining=Decimal("1"),
            over=Decimal("0"),
            status_label="No budget",
            no_budget=True,
        )

    with pytest.raises(ValueError):
        BudgetMonthNodeResultDTO(
            node_guid="n1",
            node_path="Expenses",
            budget=Decimal("0"),
            actual=Decimal("0"),
            remaining=Decimal("0"),
            over=Decimal("0"),
            status_label="No budget",
            no_budget=False,
        )


def test_budget_applicability_dto_invariants() -> None:
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetInapplicableReason,
    )

    assert BudgetApplicabilityDTO(applicable=True, reason=None).reason is None

    with pytest.raises(ValueError):
        BudgetApplicabilityDTO(
            applicable=True,
            reason=BudgetInapplicableReason.OUT_OF_RANGE,
        )

    with pytest.raises(ValueError):
        BudgetApplicabilityDTO(applicable=False, reason=None)
