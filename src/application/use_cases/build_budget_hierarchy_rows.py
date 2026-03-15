"""Build deterministic budget hierarchy rows for expense-tree rendering."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from src.domain.models.accounts import AccountDTO
from src.domain.models.budget import BudgetMonthNodeResultDTO, BudgetStatusLabel


@dataclass(frozen=True, slots=True)
class BudgetHierarchyRow:
    """Single render row for the expense hierarchy."""

    node_guid: str
    node_name: str
    node_path: str
    depth: int
    budget: Decimal
    actual: Decimal
    remaining: Decimal
    over: Decimal
    status_label: BudgetStatusLabel
    no_budget: bool


def _is_expense(account: AccountDTO) -> bool:
    return account.account_type.strip().upper() == "EXPENSE"


def _build_full_path(
    guid: str,
    *,
    accounts_by_guid: dict[str, AccountDTO],
) -> str:
    parts: list[str] = []
    cursor = accounts_by_guid.get(guid)
    seen: set[str] = set()
    while cursor is not None and cursor.guid not in seen:
        seen.add(cursor.guid)
        parts.append(cursor.name)
        if not cursor.parent_guid:
            break
        cursor = accounts_by_guid.get(cursor.parent_guid)
    return ":".join(reversed(parts))


def build_budget_hierarchy_rows(
    accounts: Sequence[AccountDTO],
    node_results: Sequence[BudgetMonthNodeResultDTO],
) -> tuple[BudgetHierarchyRow, ...]:
    """Join accounts tree with budget node results in deterministic tree order."""

    accounts_by_guid = {account.guid: account for account in accounts}
    result_by_guid = {row.node_guid: row for row in node_results}

    expense_guids = {
        account.guid for account in accounts if _is_expense(account)
    }
    if not expense_guids:
        return ()

    included_guids = set(expense_guids)
    for guid in sorted(expense_guids):
        cursor = accounts_by_guid.get(guid)
        seen: set[str] = set()
        while cursor is not None and cursor.guid not in seen:
            seen.add(cursor.guid)
            included_guids.add(cursor.guid)
            if not cursor.parent_guid:
                break
            cursor = accounts_by_guid.get(cursor.parent_guid)

    children_by_parent: dict[str | None, list[str]] = {}
    depth_by_guid: dict[str, int] = {}
    roots: list[str] = []

    for guid in sorted(included_guids):
        account = accounts_by_guid.get(guid)
        if account is None:
            continue
        parent_guid = account.parent_guid
        if parent_guid in included_guids:
            children_by_parent.setdefault(parent_guid, []).append(guid)
        else:
            roots.append(guid)

    sort_key = lambda guid: (
        accounts_by_guid[guid].name.casefold(),
        guid,
    )
    roots.sort(key=sort_key)
    for parent_guid in list(children_by_parent):
        children_by_parent[parent_guid].sort(key=sort_key)

    ordered_guids: list[str] = []
    visited: set[str] = set()

    def walk(guid: str, depth: int) -> None:
        if guid in visited:
            return
        visited.add(guid)
        ordered_guids.append(guid)
        depth_by_guid[guid] = depth
        for child_guid in children_by_parent.get(guid, []):
            walk(child_guid, depth + 1)

    for root_guid in roots:
        walk(root_guid, 0)

    rows: list[BudgetHierarchyRow] = []
    for guid in ordered_guids:
        account = accounts_by_guid[guid]
        result = result_by_guid.get(guid)
        if result is None:
            rows.append(
                BudgetHierarchyRow(
                    node_guid=guid,
                    node_name=account.name,
                    node_path=_build_full_path(guid, accounts_by_guid=accounts_by_guid),
                    depth=depth_by_guid.get(guid, 0),
                    budget=Decimal("0.00"),
                    actual=Decimal("0.00"),
                    remaining=Decimal("0.00"),
                    over=Decimal("0.00"),
                    status_label="No budget",
                    no_budget=True,
                )
            )
            continue
        rows.append(
            BudgetHierarchyRow(
                node_guid=guid,
                node_name=account.name,
                node_path=_build_full_path(guid, accounts_by_guid=accounts_by_guid),
                depth=depth_by_guid.get(guid, 0),
                budget=result.budget,
                actual=result.actual,
                remaining=result.remaining,
                over=result.over,
                status_label=result.status_label,
                no_budget=result.no_budget,
            )
        )
    return tuple(rows)


__all__ = ["BudgetHierarchyRow", "build_budget_hierarchy_rows"]
