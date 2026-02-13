"""Use case to compute per-node and summary monthly budget results."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from src.application.ports.budget_repository import BudgetRepositoryPort
from src.domain.models.budget import (
    BudgetMonthNodeResultDTO,
    BudgetMonthSummaryDTO,
    BudgetMonthViewDTO,
    budget_status_label_from_values,
    sort_budget_node_results,
)
from src.utils.decimal_utils import quantize_currency


class GetBudgetMonthViewUseCase:
    """Compute monthly budget view from per-account targets and actuals.

    Rounding policy:
      - Quantize to 2 decimals with ROUND_HALF_UP at the output boundary only.
      - Keep internal arithmetic in full precision before emitting DTO values.
    """

    def __init__(self, repository: BudgetRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        budget_guid: str,
        month_start: date,
        node_paths: Mapping[str, str] | None = None,
    ) -> BudgetMonthViewDTO:
        normalized_month_start = date(month_start.year, month_start.month, 1)
        targets = self._repository.fetch_monthly_budget_targets(
            budget_guid=budget_guid,
            month_start=normalized_month_start,
        )
        actuals = self._repository.fetch_monthly_actuals_by_account(
            month_start=normalized_month_start,
        )

        target_by_guid = {row.account_guid: row.amount for row in targets}
        actual_by_guid = {row.account_guid: row.amount for row in actuals}
        resolved_paths = dict(node_paths or {})
        all_node_guids = sorted(
            set(target_by_guid) | set(actual_by_guid) | set(resolved_paths)
        )

        path_by_guid: dict[str, str] = {}
        for node_guid in all_node_guids:
            path_by_guid[node_guid] = resolved_paths.get(node_guid, node_guid)

        # Build deterministic path->guid mapping for existing nodes first.
        path_to_guid: dict[str, str] = {}
        for node_guid, node_path in sorted(
            path_by_guid.items(),
            key=lambda item: (item[1].casefold(), item[0]),
        ):
            path_to_guid.setdefault(node_path, node_guid)

        budget_by_guid: dict[str, Decimal] = {
            node_guid: target_by_guid.get(node_guid, Decimal("0"))
            for node_guid in all_node_guids
        }
        actual_by_guid_rollup: dict[str, Decimal] = {
            node_guid: actual_by_guid.get(node_guid, Decimal("0"))
            for node_guid in all_node_guids
        }
        has_direct_budget: dict[str, bool] = {
            node_guid: node_guid in target_by_guid for node_guid in all_node_guids
        }
        children_by_guid: dict[str, set[str]] = {}
        child_guids: set[str] = set()

        for node_path in sorted(path_to_guid, key=str.casefold):
            segments = [part for part in node_path.split(":") if part]
            if len(segments) <= 1:
                continue
            for idx in range(1, len(segments)):
                ancestor_path = ":".join(segments[:idx])
                parent_guid = path_to_guid.get(ancestor_path)
                if parent_guid is None:
                    parent_guid = f"__rollup__:{ancestor_path}"
                    path_to_guid[ancestor_path] = parent_guid
                    path_by_guid[parent_guid] = ancestor_path
                    budget_by_guid[parent_guid] = Decimal("0")
                    actual_by_guid_rollup[parent_guid] = Decimal("0")
                    has_direct_budget[parent_guid] = False

                child_path = ":".join(segments[: idx + 1])
                if child_path not in path_to_guid:
                    child_guid = f"__rollup__:{child_path}"
                    path_to_guid[child_path] = child_guid
                    path_by_guid[child_guid] = child_path
                    budget_by_guid[child_guid] = Decimal("0")
                    actual_by_guid_rollup[child_guid] = Decimal("0")
                    has_direct_budget[child_guid] = False
                child_guid = path_to_guid[child_path]
                child_guids.add(child_guid)
                children_by_guid.setdefault(parent_guid, set()).add(child_guid)

        ordered_guids_for_rollup = sorted(
            path_by_guid,
            key=lambda guid: (
                -path_by_guid[guid].count(":"),
                path_by_guid[guid].casefold(),
                guid,
            ),
        )
        no_budget_by_guid: dict[str, bool] = {}

        for node_guid in ordered_guids_for_rollup:
            child_nodes = children_by_guid.get(node_guid, set())
            if child_nodes:
                direct_budget = budget_by_guid[node_guid]
                direct_actual = actual_by_guid_rollup[node_guid]
                budget_by_guid[node_guid] = sum(
                    (budget_by_guid[child_guid] for child_guid in child_nodes),
                    direct_budget,
                )
                actual_by_guid_rollup[node_guid] = sum(
                    (
                        actual_by_guid_rollup[child_guid]
                        for child_guid in child_nodes
                    ),
                    direct_actual,
                )
                no_budget_by_guid[node_guid] = (
                    (not has_direct_budget.get(node_guid, False))
                    and all(
                        no_budget_by_guid[child_guid]
                        for child_guid in child_nodes
                    )
                )
            else:
                no_budget_by_guid[node_guid] = not has_direct_budget.get(
                    node_guid, False
                )

        node_results: list[BudgetMonthNodeResultDTO] = []
        for node_guid in path_by_guid:
            budget_amount = budget_by_guid[node_guid]
            actual_amount = actual_by_guid_rollup[node_guid]
            no_budget = no_budget_by_guid[node_guid]
            remaining = max(budget_amount - actual_amount, Decimal("0"))
            over = max(actual_amount - budget_amount, Decimal("0"))
            node_results.append(
                BudgetMonthNodeResultDTO(
                    node_guid=node_guid,
                    node_path=path_by_guid[node_guid],
                    budget=quantize_currency(budget_amount),
                    actual=quantize_currency(actual_amount),
                    remaining=quantize_currency(remaining),
                    over=quantize_currency(over),
                    status_label=budget_status_label_from_values(
                        no_budget=no_budget,
                        budget=budget_amount,
                        actual=actual_amount,
                    ),
                    no_budget=no_budget,
                )
            )

        ordered_results = sort_budget_node_results(node_results)
        roots = [row for row in ordered_results if row.node_guid not in child_guids]

        total_budget = sum((row.budget for row in roots), Decimal("0"))
        total_actual = sum((row.actual for row in roots), Decimal("0"))
        total_remaining = max(total_budget - total_actual, Decimal("0"))
        total_over = max(total_actual - total_budget, Decimal("0"))
        summary_no_budget = bool(roots) and all(
            row.no_budget for row in roots
        )

        summary = BudgetMonthSummaryDTO(
            total_budget=quantize_currency(total_budget),
            total_actual=quantize_currency(total_actual),
            total_remaining=quantize_currency(total_remaining),
            total_over=quantize_currency(total_over),
            status_label=budget_status_label_from_values(
                no_budget=summary_no_budget,
                budget=total_budget,
                actual=total_actual,
            ),
        )
        return BudgetMonthViewDTO(summary=summary, node_results=ordered_results)


__all__ = ["GetBudgetMonthViewUseCase"]
