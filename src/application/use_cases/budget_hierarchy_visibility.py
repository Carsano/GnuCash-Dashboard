"""Deterministic expand/collapse visibility helpers for budget hierarchy rows."""

from __future__ import annotations

from collections.abc import Sequence

from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow


def build_children_map(
    rows: Sequence[BudgetHierarchyRow],
) -> dict[str, tuple[str, ...]]:
    """Return deterministic parent -> children GUID mapping from ordered rows."""

    children: dict[str, list[str]] = {}
    stack: list[BudgetHierarchyRow] = []

    for row in rows:
        while stack and stack[-1].depth >= row.depth:
            stack.pop()
        if stack:
            parent_guid = stack[-1].node_guid
            children.setdefault(parent_guid, []).append(row.node_guid)
        stack.append(row)

    return {
        parent_guid: tuple(child_guids)
        for parent_guid, child_guids in children.items()
    }


def visible_row_guids(
    rows: Sequence[BudgetHierarchyRow],
    expanded_guids: set[str],
) -> tuple[str, ...]:
    """Return visible row GUIDs based on the expanded-node state."""

    visible: list[str] = []
    ancestor_stack: list[tuple[int, str]] = []

    for row in rows:
        while ancestor_stack and ancestor_stack[-1][0] >= row.depth:
            ancestor_stack.pop()
        if all(parent_guid in expanded_guids for _, parent_guid in ancestor_stack):
            visible.append(row.node_guid)
        ancestor_stack.append((row.depth, row.node_guid))

    return tuple(visible)


__all__ = ["build_children_map", "visible_row_guids"]
