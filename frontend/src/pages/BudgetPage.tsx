import { useEffect, useMemo, useState } from "react";

import { BlockingState } from "../components/states/BlockingState";
import { EmptyState } from "../components/states/EmptyState";
import { InlineError } from "../components/states/InlineError";
import { KpiSkeleton } from "../components/skeletons/KpiSkeleton";
import { Card } from "../components/ui/Card";
import { DataTable } from "../components/ui/DataTable";
import { KpiGrid } from "../components/ui/KpiGrid";
import { Panel } from "../components/ui/Panel";
import { Select } from "../components/ui/Select";
import {
  useBudgetApplicabilityQuery,
  useBudgetMonthViewQuery,
  useBudgetsQuery,
} from "../lib/api/queries";
import { decimalToNumber, formatCurrency, toIsoDate } from "../lib/format";

function previousMonthStart(monthStart: string): string {
  const [year, month] = monthStart.split("-").map(Number);
  if (!year || !month) {
    return monthStart;
  }
  if (month === 1) {
    return `${year - 1}-12-01`;
  }
  return `${year}-${String(month - 1).padStart(2, "0")}-01`;
}

function reasonLabel(reason: string | null): string {
  if (reason === "out_of_range") {
    return "Selected month is outside this budget period.";
  }
  if (reason === "no_targets") {
    return "No targets are defined for the selected month.";
  }
  if (reason === "data_unavailable") {
    return "Budget data is unavailable for current backend.";
  }
  return "Budget is not applicable for this context.";
}

export function BudgetPage() {
  const today = new Date();
  const [monthStart, setMonthStart] = useState(
    toIsoDate(new Date(today.getFullYear(), today.getMonth(), 1)),
  );
  const budgetsQuery = useBudgetsQuery();
  const [budgetGuid, setBudgetGuid] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!budgetsQuery.data?.budgets.length) {
      return;
    }
    if (budgetGuid && budgetsQuery.data.budgets.some((item) => item.guid === budgetGuid)) {
      return;
    }
    setBudgetGuid(budgetsQuery.data.budgets[0].guid);
  }, [budgetsQuery.data, budgetGuid]);

  const applicabilityQuery = useBudgetApplicabilityQuery(budgetGuid, monthStart);
  const monthViewQuery = useBudgetMonthViewQuery(budgetGuid, monthStart);
  const previousMonthViewQuery = useBudgetMonthViewQuery(
    budgetGuid,
    previousMonthStart(monthStart),
  );

  const contextLine = useMemo(() => {
    const budgetName =
      budgetsQuery.data?.budgets.find((item) => item.guid === budgetGuid)?.name ??
      "No budget";
    const deltaActual =
      decimalToNumber(monthViewQuery.data?.summary.total_actual) -
      decimalToNumber(previousMonthViewQuery.data?.summary.total_actual);
    const hasDelta = previousMonthViewQuery.data?.summary.total_actual !== undefined;
    const deltaText = hasDelta ? `${deltaActual >= 0 ? "+" : ""}${deltaActual.toFixed(2)}` : "n/a";
    return `Month: ${monthStart} | Budget: ${budgetName} | vs last month actual: ${deltaText}`;
  }, [budgetsQuery.data, budgetGuid, monthStart, monthViewQuery.data, previousMonthViewQuery.data]);

  const rows = monthViewQuery.data?.node_results ?? [];

  return (
    <Panel title="Budget" subtitle="KPI-first month summary and expense hierarchy">
      <p className="muted">{contextLine}</p>

      <details className="context-expander">
        <summary>Context</summary>
        <div className="toolbar">
          <input
            className="field focusable"
            type="month"
            value={monthStart.slice(0, 7)}
            onChange={(event) => {
              const value = event.target.value;
              if (!value) {
                return;
              }
              setMonthStart(`${value}-01`);
            }}
          />
          <Select
            value={budgetGuid ?? ""}
            onChange={(event) => setBudgetGuid(event.target.value || undefined)}
            disabled={!budgetsQuery.data?.budgets.length}
          >
            {(budgetsQuery.data?.budgets ?? []).map((item) => (
              <option key={item.guid} value={item.guid}>
                {item.name}
              </option>
            ))}
          </Select>
        </div>
      </details>

      {budgetsQuery.isLoading ? <KpiSkeleton /> : null}
      {budgetsQuery.error ? (
        <InlineError message={(budgetsQuery.error as Error).message} onRetry={() => void budgetsQuery.refetch()} />
      ) : null}

      {!budgetsQuery.isLoading && !budgetsQuery.error && (budgetsQuery.data?.budgets.length ?? 0) === 0 ? (
        <BlockingState
          title="No budgets found"
          body="No GnuCash budgets are available. Add one in GnuCash, then refresh."
        />
      ) : null}

      {budgetGuid && applicabilityQuery.data && !applicabilityQuery.data.applicable ? (
        <BlockingState
          title="Budget cannot be applied"
          body={reasonLabel(applicabilityQuery.data.reason)}
        />
      ) : null}

      {budgetGuid && applicabilityQuery.data?.applicable ? (
        monthViewQuery.isLoading ? (
          <KpiSkeleton />
        ) : monthViewQuery.error ? (
          <InlineError message={(monthViewQuery.error as Error).message} onRetry={() => void monthViewQuery.refetch()} />
        ) : monthViewQuery.data ? (
          <>
            <KpiGrid>
              <Card
                label="Total Budget"
                value={formatCurrency(monthViewQuery.data.summary.total_budget)}
              />
              <Card
                label="Total Actual"
                value={formatCurrency(monthViewQuery.data.summary.total_actual)}
              />
              <Card
                label="Remaining"
                value={formatCurrency(monthViewQuery.data.summary.total_remaining)}
              />
              <Card
                label="Over"
                value={formatCurrency(monthViewQuery.data.summary.total_over)}
                sub={`Status: ${monthViewQuery.data.summary.status_label}`}
              />
            </KpiGrid>

            {rows.length === 0 ? (
              <EmptyState
                title="No budget rows"
                body="No hierarchy rows were returned for this month."
              />
            ) : (
              <DataTable
                rows={rows}
                columns={[
                  { key: "path", title: "Category", render: (row) => row.node_path },
                  { key: "budget", title: "Budget", render: (row) => formatCurrency(row.budget) },
                  { key: "actual", title: "Actual", render: (row) => formatCurrency(row.actual) },
                  {
                    key: "remaining_over",
                    title: "Remaining/Over",
                    render: (row) =>
                      decimalToNumber(row.over) > 0
                        ? `Over ${formatCurrency(row.over)}`
                        : `Remaining ${formatCurrency(row.remaining)}`,
                  },
                  { key: "status", title: "Status", render: (row) => row.status_label },
                ]}
              />
            )}
          </>
        ) : null
      ) : null}
    </Panel>
  );
}
