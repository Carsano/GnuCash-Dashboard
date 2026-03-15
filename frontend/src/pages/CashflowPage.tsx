import { useEffect, useMemo, useState } from "react";

import { InlineError } from "../components/states/InlineError";
import { EmptyState } from "../components/states/EmptyState";
import { KpiSkeleton } from "../components/skeletons/KpiSkeleton";
import { DataTable } from "../components/ui/DataTable";
import { Panel } from "../components/ui/Panel";
import { Button } from "../components/ui/Button";
import { TextInput } from "../components/ui/TextInput";
import {
  useCashflowAssetSelectionQuery,
  useCashflowQuery,
} from "../lib/api/queries";
import { decimalToNumber, formatCurrency, toIsoDate } from "../lib/format";

function SankeyLite({
  totalIn,
  totalOut,
  difference,
  allowNegative,
}: {
  totalIn: string;
  totalOut: string;
  difference: string;
  allowNegative: boolean;
}) {
  const inValue = Math.max(0, decimalToNumber(totalIn));
  const outValue = Math.max(0, decimalToNumber(totalOut));
  const diffValue = decimalToNumber(difference);
  const base = Math.max(inValue, outValue, 1);
  const inWidth = Math.max(8, (inValue / base) * 100);
  const outWidth = Math.max(8, (outValue / base) * 100);

  return (
    <div className="chart-panel">
      <strong>Cashflow Sankey (lightweight)</strong>
      <div className="sankey-lite">
        <div>
          <label>Incoming</label>
          <div className="sankey-rail">
            <span className="in" style={{ width: `${inWidth}%` }} />
          </div>
          <p>{formatCurrency(totalIn)}</p>
        </div>
        <div>
          <label>Outgoing</label>
          <div className="sankey-rail">
            <span className="out" style={{ width: `${outWidth}%` }} />
          </div>
          <p>{formatCurrency(totalOut)}</p>
        </div>
        {diffValue >= 0 || allowNegative ? (
          <div>
            <label>{diffValue >= 0 ? "Difference" : "Deficit"}</label>
            <div className="sankey-rail">
              <span className={diffValue >= 0 ? "diff" : "deficit"} style={{ width: `${Math.max(8, (Math.abs(diffValue) / base) * 100)}%` }} />
            </div>
            <p>{formatCurrency(difference)}</p>
          </div>
        ) : (
          <p className="muted">Difference is negative; enable deficit toggle to show the node.</p>
        )}
      </div>
    </div>
  );
}

export function CashflowPage() {
  const today = new Date();
  const defaultStart = new Date(today.getFullYear(), today.getMonth(), 1);
  const [startDate, setStartDate] = useState(toIsoDate(defaultStart));
  const [endDate, setEndDate] = useState(toIsoDate(today));
  const [assetRootName, setAssetRootName] = useState("Actif");
  const [availableFilter, setAvailableFilter] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("");
  const [selectedGuids, setSelectedGuids] = useState<string[]>([]);
  const [hasInitializedSelection, setHasInitializedSelection] = useState(false);
  const [showSankey, setShowSankey] = useState(false);
  const [allowNegativeDeficit, setAllowNegativeDeficit] = useState(false);

  const selectionQuery = useCashflowAssetSelectionQuery(assetRootName);

  useEffect(() => {
    setHasInitializedSelection(false);
    setSelectedGuids([]);
  }, [assetRootName]);

  useEffect(() => {
    if (!selectionQuery.data || hasInitializedSelection) {
      return;
    }
    setSelectedGuids(selectionQuery.data.default_selected_guids);
    setHasInitializedSelection(true);
  }, [selectionQuery.data, hasInitializedSelection]);

  const cashflowQuery = useCashflowQuery(startDate, endDate, selectedGuids);

  const availableOptions = useMemo(() => {
    const selected = new Set(selectedGuids);
    return (selectionQuery.data?.options ?? []).filter((item) => {
      if (selected.has(item.guid)) {
        return false;
      }
      return item.display_name.toLowerCase().includes(availableFilter.toLowerCase());
    });
  }, [selectionQuery.data, selectedGuids, availableFilter]);

  const selectedOptions = useMemo(() => {
    const byGuid = new Map((selectionQuery.data?.options ?? []).map((item) => [item.guid, item]));
    return selectedGuids
      .map((guid) => byGuid.get(guid))
      .filter((item): item is NonNullable<typeof item> => Boolean(item))
      .filter((item) => item.display_name.toLowerCase().includes(selectedFilter.toLowerCase()));
  }, [selectionQuery.data, selectedGuids, selectedFilter]);

  const summary = cashflowQuery.data?.summary;

  return (
    <Panel title="Cashflow" subtitle="Asset selection, summary KPIs, details, and lazy Sankey">
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
        <TextInput
          value={assetRootName}
          onChange={(event) => setAssetRootName(event.target.value || "Actif")}
          placeholder="Asset root name"
        />
      </div>

      {selectionQuery.isLoading ? <KpiSkeleton /> : null}
      {selectionQuery.error ? (
        <InlineError message={(selectionQuery.error as Error).message} onRetry={() => void selectionQuery.refetch()} />
      ) : null}

      {selectionQuery.data ? (
        <div className="two-col">
          <div className="chart-panel">
            <strong>Available assets ({availableOptions.length})</strong>
            <TextInput
              value={availableFilter}
              onChange={(event) => setAvailableFilter(event.target.value)}
              placeholder="Filter available"
            />
            <ul className="pick-list">
              {availableOptions.map((item) => (
                <li key={item.guid}>
                  <span>{item.display_name}</span>
                  <Button
                    variant="ghost"
                    onClick={() => setSelectedGuids((current) => [...current, item.guid])}
                  >
                    Add
                  </Button>
                </li>
              ))}
            </ul>
            <Button
              variant="ghost"
              onClick={() =>
                setSelectedGuids(selectionQuery.data.options.map((item) => item.guid))
              }
            >
              Select all
            </Button>
          </div>

          <div className="chart-panel">
            <strong>Selected assets ({selectedOptions.length})</strong>
            <TextInput
              value={selectedFilter}
              onChange={(event) => setSelectedFilter(event.target.value)}
              placeholder="Filter selected"
            />
            <ul className="pick-list">
              {selectedOptions.map((item) => (
                <li key={item.guid}>
                  <span>{item.display_name}</span>
                  <Button
                    variant="ghost"
                    onClick={() =>
                      setSelectedGuids((current) =>
                        current.filter((guid) => guid !== item.guid),
                      )
                    }
                  >
                    Remove
                  </Button>
                </li>
              ))}
            </ul>
            <Button variant="ghost" onClick={() => setSelectedGuids([])}>
              Clear selection
            </Button>
          </div>
        </div>
      ) : null}

      {selectedGuids.length === 0 ? (
        <EmptyState
          title="No asset selected"
          body="Select at least one asset account to compute cashflow."
        />
      ) : cashflowQuery.isLoading ? (
        <KpiSkeleton />
      ) : cashflowQuery.error ? (
        <InlineError message={(cashflowQuery.error as Error).message} onRetry={() => void cashflowQuery.refetch()} />
      ) : summary ? (
        <>
          <div className="kpi-grid">
            <div className="card"><div className="card-label">Incoming</div><div className="card-value">{formatCurrency(summary.total_in)}</div></div>
            <div className="card"><div className="card-label">Outgoing</div><div className="card-value">{formatCurrency(summary.total_out)}</div></div>
            <div className="card"><div className="card-label">Difference</div><div className="card-value">{formatCurrency(summary.difference)}</div></div>
          </div>

          <div className="toolbar">
            <label className="toggle"><input className="focusable" type="checkbox" checked={showSankey} onChange={(event) => setShowSankey(event.target.checked)} /><span>Show Sankey</span></label>
            <label className="toggle"><input className="focusable" type="checkbox" checked={allowNegativeDeficit} onChange={(event) => setAllowNegativeDeficit(event.target.checked)} /><span>Allow negative deficit node</span></label>
          </div>

          {showSankey ? (
            <SankeyLite
              totalIn={summary.total_in}
              totalOut={summary.total_out}
              difference={summary.difference}
              allowNegative={allowNegativeDeficit}
            />
          ) : null}

          <div className="two-col">
            <DataTable
              rows={cashflowQuery.data?.incoming ?? []}
              emptyLabel="No incoming rows"
              columns={[
                { key: "account", title: "Account", render: (row) => row.account_full_name },
                { key: "amount", title: "Amount", render: (row) => formatCurrency(row.amount) },
              ]}
            />
            <DataTable
              rows={cashflowQuery.data?.outgoing ?? []}
              emptyLabel="No outgoing rows"
              columns={[
                { key: "account", title: "Account", render: (row) => row.account_full_name },
                { key: "amount", title: "Amount", render: (row) => formatCurrency(row.amount) },
              ]}
            />
          </div>
        </>
      ) : null}
    </Panel>
  );
}
