from __future__ import annotations

from datetime import date
from decimal import Decimal


def test_get_budget_month_view_use_case_computes_nodes_and_summary_semantics() -> None:
    from src.application.use_cases.get_budget_month_view import (
        GetBudgetMonthViewUseCase,
    )
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
    )

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            assert budget_guid == "b1"
            assert month_start == date(2026, 2, 1)
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="node-a",
                    amount=Decimal("100"),
                ),
                BudgetAccountMonthlyTargetDTO(
                    account_guid="node-b",
                    amount=Decimal("0"),
                ),
            ]

        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            assert month_start == date(2026, 2, 1)
            return [
                AccountMonthlyActualDTO(
                    account_guid="node-a",
                    amount=Decimal("120"),
                ),
                AccountMonthlyActualDTO(
                    account_guid="node-c",
                    amount=Decimal("15"),
                ),
            ]

    use_case = GetBudgetMonthViewUseCase(repository=_Repo())
    result = use_case.execute(
        budget_guid="b1",
        month_start=date(2026, 2, 20),
    )

    assert [(row.node_guid, row.budget, row.actual, row.remaining, row.over, row.status_label, row.no_budget) for row in result.node_results] == [
        ("node-a", Decimal("100"), Decimal("120"), Decimal("0"), Decimal("20"), "Over", False),
        ("node-b", Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), "On track", False),
        ("node-c", Decimal("0"), Decimal("15"), Decimal("0"), Decimal("15"), "No budget", True),
    ]
    assert result.summary.total_budget == Decimal("100")
    assert result.summary.total_actual == Decimal("135")
    assert result.summary.total_remaining == Decimal("0")
    assert result.summary.total_over == Decimal("35")
    assert result.summary.status_label == "Over"


def test_get_budget_month_view_use_case_is_deterministic_with_casefold_sort() -> None:
    from src.application.use_cases.get_budget_month_view import (
        GetBudgetMonthViewUseCase,
    )
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
    )

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="b-guid",
                    amount=Decimal("10"),
                ),
                BudgetAccountMonthlyTargetDTO(
                    account_guid="a-guid",
                    amount=Decimal("10"),
                ),
            ]

        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            _ = month_start
            return [
                AccountMonthlyActualDTO(
                    account_guid="a-guid",
                    amount=Decimal("4"),
                ),
                AccountMonthlyActualDTO(
                    account_guid="b-guid",
                    amount=Decimal("4"),
                ),
            ]

    use_case = GetBudgetMonthViewUseCase(repository=_Repo())
    result = use_case.execute(
        budget_guid="b1",
        month_start=date(2026, 2, 1),
        node_paths={
            "a-guid": "expenses:food",
            "b-guid": "Expenses:Food",
        },
    )
    leaf_rows = [
        row
        for row in result.node_results
        if row.node_guid in {"a-guid", "b-guid"}
    ]
    assert [row.node_guid for row in leaf_rows] == ["a-guid", "b-guid"]


def test_get_budget_month_view_use_case_applies_2dp_rounding_at_output_boundary() -> None:
    from src.application.use_cases.get_budget_month_view import (
        GetBudgetMonthViewUseCase,
    )
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
    )

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="node-a",
                    amount=Decimal("10.005"),
                )
            ]

        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            _ = month_start
            return [
                AccountMonthlyActualDTO(
                    account_guid="node-a",
                    amount=Decimal("2.335"),
                )
            ]

    use_case = GetBudgetMonthViewUseCase(repository=_Repo())
    result = use_case.execute(budget_guid="b1", month_start=date(2026, 2, 1))
    row = result.node_results[0]

    assert row.budget == Decimal("10.01")
    assert row.actual == Decimal("2.34")
    assert row.remaining == Decimal("7.67")
    assert row.over == Decimal("0.00")
    assert result.summary.total_budget == Decimal("10.01")
    assert result.summary.total_actual == Decimal("2.34")
    assert result.summary.total_remaining == Decimal("7.67")
    assert result.summary.total_over == Decimal("0.00")


def test_get_budget_month_view_use_case_repeated_runs_return_identical_outputs() -> None:
    from src.application.use_cases.get_budget_month_view import (
        GetBudgetMonthViewUseCase,
    )
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
    )

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            return [
                BudgetAccountMonthlyTargetDTO(account_guid="node-b", amount=Decimal("7.777")),
                BudgetAccountMonthlyTargetDTO(account_guid="node-a", amount=Decimal("5.555")),
            ]

        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            _ = month_start
            return [
                AccountMonthlyActualDTO(account_guid="node-a", amount=Decimal("1.111")),
                AccountMonthlyActualDTO(account_guid="node-c", amount=Decimal("3.333")),
            ]

    use_case = GetBudgetMonthViewUseCase(repository=_Repo())
    result_a = use_case.execute(budget_guid="b1", month_start=date(2026, 2, 1))
    result_b = use_case.execute(budget_guid="b1", month_start=date(2026, 2, 1))

    assert result_a == result_b


def test_get_budget_month_view_use_case_reconciles_parent_to_children_totals() -> None:
    from src.application.use_cases.get_budget_month_view import (
        GetBudgetMonthViewUseCase,
    )
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
    )

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="leaf-food",
                    amount=Decimal("40.00"),
                ),
                BudgetAccountMonthlyTargetDTO(
                    account_guid="leaf-rent",
                    amount=Decimal("60.00"),
                ),
                BudgetAccountMonthlyTargetDTO(
                    account_guid="leaf-misc",
                    amount=Decimal("0.00"),
                ),
            ]

        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            _ = month_start
            return [
                AccountMonthlyActualDTO(
                    account_guid="leaf-food",
                    amount=Decimal("50.00"),
                ),
                AccountMonthlyActualDTO(
                    account_guid="leaf-rent",
                    amount=Decimal("55.00"),
                ),
                AccountMonthlyActualDTO(
                    account_guid="leaf-misc",
                    amount=Decimal("2.00"),
                ),
            ]

    use_case = GetBudgetMonthViewUseCase(repository=_Repo())
    result = use_case.execute(
        budget_guid="b1",
        month_start=date(2026, 2, 1),
        node_paths={
            "leaf-food": "Expenses:Home:Food",
            "leaf-rent": "Expenses:Home:Rent",
            "leaf-misc": "Expenses:Misc",
        },
    )

    by_path = {row.node_path: row for row in result.node_results}
    root = by_path["Expenses"]
    home = by_path["Expenses:Home"]
    food = by_path["Expenses:Home:Food"]
    rent = by_path["Expenses:Home:Rent"]
    misc = by_path["Expenses:Misc"]

    assert home.budget == food.budget + rent.budget
    assert home.actual == food.actual + rent.actual
    assert root.budget == home.budget + misc.budget
    assert root.actual == home.actual + misc.actual
    assert home.remaining == Decimal("0.00")
    assert home.over == Decimal("5.00")
    assert root.remaining == Decimal("0.00")
    assert root.over == Decimal("7.00")
    assert misc.status_label == "Over"


def test_get_budget_month_view_use_case_summary_matches_root_within_currency_tolerance() -> None:
    from src.application.use_cases.get_budget_month_view import (
        GetBudgetMonthViewUseCase,
    )
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
    )

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="leaf-a",
                    amount=Decimal("10.005"),
                ),
                BudgetAccountMonthlyTargetDTO(
                    account_guid="leaf-b",
                    amount=Decimal("20.005"),
                ),
            ]

        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            _ = month_start
            return [
                AccountMonthlyActualDTO(
                    account_guid="leaf-a",
                    amount=Decimal("9.995"),
                ),
                AccountMonthlyActualDTO(
                    account_guid="leaf-b",
                    amount=Decimal("20.015"),
                ),
            ]

    use_case = GetBudgetMonthViewUseCase(repository=_Repo())
    result = use_case.execute(
        budget_guid="b1",
        month_start=date(2026, 2, 1),
        node_paths={
            "leaf-a": "Expenses:A",
            "leaf-b": "Expenses:B",
        },
    )
    by_path = {row.node_path: row for row in result.node_results}
    root = by_path["Expenses"]

    tolerance = Decimal("0.01")
    assert abs(result.summary.total_budget - root.budget) <= tolerance
    assert abs(result.summary.total_actual - root.actual) <= tolerance
    assert abs(result.summary.total_remaining - root.remaining) <= tolerance
    assert abs(result.summary.total_over - root.over) <= tolerance


def test_get_budget_month_view_use_case_preserves_direct_parent_values_in_rollups() -> None:
    from src.application.use_cases.get_budget_month_view import (
        GetBudgetMonthViewUseCase,
    )
    from src.domain.models.budget import (
        AccountMonthlyActualDTO,
        BudgetAccountMonthlyTargetDTO,
    )

    class _Repo:
        def fetch_monthly_budget_targets(self, *, budget_guid: str, month_start: date):
            _ = budget_guid, month_start
            return [
                BudgetAccountMonthlyTargetDTO(
                    account_guid="parent-home",
                    amount=Decimal("5.00"),
                ),
                BudgetAccountMonthlyTargetDTO(
                    account_guid="leaf-food",
                    amount=Decimal("40.00"),
                ),
                BudgetAccountMonthlyTargetDTO(
                    account_guid="leaf-rent",
                    amount=Decimal("60.00"),
                ),
            ]

        def fetch_monthly_actuals_by_account(self, *, month_start: date):
            _ = month_start
            return [
                AccountMonthlyActualDTO(
                    account_guid="parent-home",
                    amount=Decimal("6.00"),
                ),
                AccountMonthlyActualDTO(
                    account_guid="leaf-food",
                    amount=Decimal("50.00"),
                ),
                AccountMonthlyActualDTO(
                    account_guid="leaf-rent",
                    amount=Decimal("55.00"),
                ),
            ]

    use_case = GetBudgetMonthViewUseCase(repository=_Repo())
    result = use_case.execute(
        budget_guid="b1",
        month_start=date(2026, 2, 1),
        node_paths={
            "parent-home": "Expenses:Home",
            "leaf-food": "Expenses:Home:Food",
            "leaf-rent": "Expenses:Home:Rent",
        },
    )
    by_path = {row.node_path: row for row in result.node_results}
    home = by_path["Expenses:Home"]
    food = by_path["Expenses:Home:Food"]
    rent = by_path["Expenses:Home:Rent"]
    root = by_path["Expenses"]

    assert home.budget == food.budget + rent.budget + Decimal("5.00")
    assert home.actual == food.actual + rent.actual + Decimal("6.00")
    assert home.over == Decimal("6.00")
    assert root.budget == home.budget
    assert root.actual == home.actual
