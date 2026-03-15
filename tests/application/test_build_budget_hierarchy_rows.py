from __future__ import annotations

from decimal import Decimal


def test_build_budget_hierarchy_rows_orders_tree_and_maps_values() -> None:
    from src.application.use_cases.build_budget_hierarchy_rows import (
        build_budget_hierarchy_rows,
    )
    from src.domain.models.accounts import AccountDTO
    from src.domain.models.budget import BudgetMonthNodeResultDTO

    accounts = [
        AccountDTO(
            guid="root-exp",
            name="Expenses",
            account_type="EXPENSE",
            commodity_guid=None,
            parent_guid=None,
        ),
        AccountDTO(
            guid="home",
            name="Home",
            account_type="EXPENSE",
            commodity_guid=None,
            parent_guid="root-exp",
        ),
        AccountDTO(
            guid="food",
            name="Food",
            account_type="EXPENSE",
            commodity_guid=None,
            parent_guid="home",
        ),
        AccountDTO(
            guid="rent",
            name="Rent",
            account_type="EXPENSE",
            commodity_guid=None,
            parent_guid="home",
        ),
        AccountDTO(
            guid="misc",
            name="Misc",
            account_type="EXPENSE",
            commodity_guid=None,
            parent_guid="root-exp",
        ),
        AccountDTO(
            guid="asset-root",
            name="Assets",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid=None,
        ),
    ]
    node_results = [
        BudgetMonthNodeResultDTO(
            node_guid="food",
            node_path="Expenses:Home:Food",
            budget=Decimal("40.00"),
            actual=Decimal("50.00"),
            remaining=Decimal("0.00"),
            over=Decimal("10.00"),
            status_label="Over",
            no_budget=False,
        ),
        BudgetMonthNodeResultDTO(
            node_guid="rent",
            node_path="Expenses:Home:Rent",
            budget=Decimal("60.00"),
            actual=Decimal("55.00"),
            remaining=Decimal("5.00"),
            over=Decimal("0.00"),
            status_label="On track",
            no_budget=False,
        ),
        BudgetMonthNodeResultDTO(
            node_guid="home",
            node_path="Expenses:Home",
            budget=Decimal("100.00"),
            actual=Decimal("105.00"),
            remaining=Decimal("0.00"),
            over=Decimal("5.00"),
            status_label="Over",
            no_budget=False,
        ),
    ]

    rows = build_budget_hierarchy_rows(accounts, node_results)

    assert [row.node_guid for row in rows] == [
        "root-exp",
        "home",
        "food",
        "rent",
        "misc",
    ]
    by_guid = {row.node_guid: row for row in rows}
    assert by_guid["home"].depth == 1
    assert by_guid["food"].depth == 2
    assert by_guid["food"].budget == Decimal("40.00")
    assert by_guid["rent"].status_label == "On track"
    assert by_guid["misc"].status_label == "No budget"
    assert by_guid["misc"].no_budget is True
    assert by_guid["misc"].budget == Decimal("0.00")
    assert by_guid["root-exp"].node_path == "Expenses"


def test_build_budget_hierarchy_rows_includes_non_expense_ancestors_for_structure() -> None:
    from src.application.use_cases.build_budget_hierarchy_rows import (
        build_budget_hierarchy_rows,
    )
    from src.domain.models.accounts import AccountDTO
    from src.domain.models.budget import BudgetMonthNodeResultDTO

    accounts = [
        AccountDTO(
            guid="root",
            name="Root",
            account_type="ROOT",
            commodity_guid=None,
            parent_guid=None,
        ),
        AccountDTO(
            guid="exp",
            name="Expenses",
            account_type="EXPENSE",
            commodity_guid=None,
            parent_guid="root",
        ),
        AccountDTO(
            guid="food",
            name="Food",
            account_type="EXPENSE",
            commodity_guid=None,
            parent_guid="exp",
        ),
    ]
    node_results = [
        BudgetMonthNodeResultDTO(
            node_guid="food",
            node_path="Root:Expenses:Food",
            budget=Decimal("10.00"),
            actual=Decimal("8.00"),
            remaining=Decimal("2.00"),
            over=Decimal("0.00"),
            status_label="On track",
            no_budget=False,
        )
    ]

    rows = build_budget_hierarchy_rows(accounts, node_results)

    assert [row.node_guid for row in rows] == ["root", "exp", "food"]
    assert rows[0].depth == 0
    assert rows[1].depth == 1
    assert rows[2].depth == 2
