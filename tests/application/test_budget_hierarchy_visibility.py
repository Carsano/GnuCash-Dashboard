from __future__ import annotations

from decimal import Decimal


def _row(*, guid: str, depth: int) -> object:
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow

    return BudgetHierarchyRow(
        node_guid=guid,
        node_name=guid,
        node_path=guid,
        depth=depth,
        budget=Decimal("0.00"),
        actual=Decimal("0.00"),
        remaining=Decimal("0.00"),
        over=Decimal("0.00"),
        status_label="No budget",
        no_budget=True,
    )


def test_build_children_map_is_deterministic_from_row_order() -> None:
    from src.application.use_cases.budget_hierarchy_visibility import (
        build_children_map,
    )

    rows = (
        _row(guid="root", depth=0),
        _row(guid="home", depth=1),
        _row(guid="food", depth=2),
        _row(guid="rent", depth=2),
        _row(guid="misc", depth=1),
    )

    children = build_children_map(rows)

    assert children == {
        "root": ("home", "misc"),
        "home": ("food", "rent"),
    }


def test_visible_row_guids_respects_expanded_ancestors() -> None:
    from src.application.use_cases.budget_hierarchy_visibility import (
        visible_row_guids,
    )

    rows = (
        _row(guid="root", depth=0),
        _row(guid="home", depth=1),
        _row(guid="food", depth=2),
        _row(guid="rent", depth=2),
        _row(guid="misc", depth=1),
    )

    assert visible_row_guids(rows, expanded_guids=set()) == ("root",)
    assert visible_row_guids(rows, expanded_guids={"root"}) == (
        "root",
        "home",
        "misc",
    )
    assert visible_row_guids(rows, expanded_guids={"root", "home"}) == (
        "root",
        "home",
        "food",
        "rent",
        "misc",
    )
