import { useMemo, useState } from "react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { KpiGrid } from "../components/ui/KpiGrid";
import { Panel } from "../components/ui/Panel";
import { InlineError } from "../components/states/InlineError";
import { KpiSkeleton } from "../components/skeletons/KpiSkeleton";
import {
  useAccountBalancesQuery,
  useAssetCategoryBreakdownQuery,
  useNetWorthQuery,
  useSyncAnalyticsMutation,
} from "../lib/api/queries";
import { decimalToNumber, formatCurrency, toIsoDate } from "../lib/format";

function CategoryBars({
  title,
  rows,
}: {
  title: string;
  rows: Array<{ category: string; amount: string }>;
}) {
  const total = rows.reduce((sum, row) => sum + decimalToNumber(row.amount), 0);
  return (
    <div className="chart-panel">
      <strong>{title}</strong>
      {rows.length === 0 ? (
        <p className="muted">No category data for this range.</p>
      ) : (
        <div className="bars">
          {rows.map((row) => {
            const value = decimalToNumber(row.amount);
            const pct = total > 0 ? (value / total) * 100 : 0;
            return (
              <div className="bar-row" key={row.category}>
                <div className="bar-label">{row.category}</div>
                <div className="bar-track">
                  <span style={{ width: `${Math.max(3, pct)}%` }} />
                </div>
                <div className="bar-value">{formatCurrency(row.amount)}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function DashboardPage() {
  const today = new Date();
  const defaultStart = new Date(today.getFullYear(), 0, 1);
  const [startDate, setStartDate] = useState(toIsoDate(defaultStart));
  const [endDate, setEndDate] = useState(toIsoDate(today));

  const syncMutation = useSyncAnalyticsMutation();
  const netWorthQuery = useNetWorthQuery(startDate, endDate);
  const breakdownL1Query = useAssetCategoryBreakdownQuery(endDate, 1);
  const breakdownL2Query = useAssetCategoryBreakdownQuery(endDate, 2);
  const balancesQuery = useAccountBalancesQuery(endDate);

  const loading =
    netWorthQuery.isLoading || breakdownL1Query.isLoading || breakdownL2Query.isLoading;

  const hasError = netWorthQuery.error || breakdownL1Query.error || breakdownL2Query.error;

  const topBalances = useMemo(() => {
    const list = balancesQuery.data?.balances ?? [];
    return [...list]
      .sort((a, b) => decimalToNumber(b.balance) - decimalToNumber(a.balance))
      .slice(0, 8);
  }, [balancesQuery.data]);

  return (
    <Panel
      title="Dashboard"
      subtitle="KPI-first parity with live API data"
      actions={
        <div className="toolbar">
          <input
            className="field focusable"
            type="date"
            value={startDate}
            max={endDate}
            onChange={(event) => setStartDate(event.target.value)}
          />
          <input
            className="field focusable"
            type="date"
            value={endDate}
            min={startDate}
            onChange={(event) => setEndDate(event.target.value)}
          />
          <Button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            {syncMutation.isPending ? "Syncing..." : "Sync analytics"}
          </Button>
        </div>
      }
    >
      {loading ? <KpiSkeleton /> : null}

      {hasError ? (
        <InlineError
          message={(hasError as Error).message}
          onRetry={() => {
            void netWorthQuery.refetch();
            void breakdownL1Query.refetch();
            void breakdownL2Query.refetch();
            void balancesQuery.refetch();
          }}
        />
      ) : null}

      {!loading && !hasError && netWorthQuery.data ? (
        <>
          <KpiGrid>
            <Card
              label="Assets"
              value={formatCurrency(netWorthQuery.data.asset_total, netWorthQuery.data.currency_code)}
              sub="Total assets"
            />
            <Card
              label="Liabilities"
              value={formatCurrency(netWorthQuery.data.liability_total, netWorthQuery.data.currency_code)}
              sub="Total liabilities"
            />
            <Card
              label="Net Worth"
              value={formatCurrency(netWorthQuery.data.net_worth, netWorthQuery.data.currency_code)}
              sub="Assets - liabilities"
            />
            <Card
              label="Range"
              value={`${startDate} to ${endDate}`}
              sub="Current query window"
            />
          </KpiGrid>

          <div className="two-col">
            <CategoryBars
              title="Asset breakdown level 1"
              rows={breakdownL1Query.data?.categories ?? []}
            />
            <CategoryBars
              title="Asset breakdown level 2"
              rows={breakdownL2Query.data?.categories ?? []}
            />
          </div>

          <div className="chart-panel">
            <strong>Top account balances</strong>
            <ul className="compact-list">
              {topBalances.map((row) => (
                <li key={row.guid}>
                  <span>{row.name}</span>
                  <span>{formatCurrency(row.balance, row.currency_code)}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      ) : null}

      {syncMutation.error ? (
        <InlineError message={(syncMutation.error as Error).message} />
      ) : null}
    </Panel>
  );
}
