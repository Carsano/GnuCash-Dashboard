import { useMemo, useState } from "react";

import { InlineError } from "../components/states/InlineError";
import { EmptyState } from "../components/states/EmptyState";
import { KpiSkeleton } from "../components/skeletons/KpiSkeleton";
import { TableSkeleton } from "../components/skeletons/TableSkeleton";
import { DataTable } from "../components/ui/DataTable";
import { Panel } from "../components/ui/Panel";
import { Select } from "../components/ui/Select";
import { TextInput } from "../components/ui/TextInput";
import { useAccountsQuery } from "../lib/api/queries";

export function AccountsPage() {
  const { data, isLoading, error, refetch } = useAccountsQuery();
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("All");

  const accountTypes = useMemo(() => {
    const values = new Set((data?.accounts ?? []).map((item) => item.account_type));
    return ["All", ...Array.from(values).sort()];
  }, [data]);

  const parentNameByGuid = useMemo(() => {
    return new Map((data?.accounts ?? []).map((item) => [item.guid, item.name]));
  }, [data]);

  const rows = useMemo(() => {
    return (data?.accounts ?? []).filter((item) => {
      if (typeFilter !== "All" && item.account_type !== typeFilter) {
        return false;
      }
      if (query.trim() && !item.name.toLowerCase().includes(query.trim().toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [data, query, typeFilter]);

  return (
    <Panel
      title="Accounts"
      subtitle={`Synced account rows: ${(data?.accounts ?? []).length}`}
      actions={
        <div className="toolbar">
          <TextInput
            aria-label="Search accounts"
            placeholder="Search by name"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Select
            aria-label="Filter account type"
            value={typeFilter}
            onChange={(event) => setTypeFilter(event.target.value)}
          >
            {accountTypes.map((option) => (
              <option key={option}>{option}</option>
            ))}
          </Select>
        </div>
      }
    >
      {isLoading ? (
        <>
          <KpiSkeleton />
          <TableSkeleton />
        </>
      ) : error ? (
        <InlineError message={(error as Error).message} onRetry={() => void refetch()} />
      ) : rows.length === 0 ? (
        <EmptyState
          title="No accounts"
          body="Run analytics sync first, then refresh this page."
        />
      ) : (
        <DataTable
          rows={rows}
          columns={[
            { key: "name", title: "Name", render: (row) => row.name },
            { key: "type", title: "Type", render: (row) => row.account_type },
            {
              key: "parent",
              title: "Parent",
              render: (row) => (row.parent_guid ? parentNameByGuid.get(row.parent_guid) ?? row.parent_guid : "-"),
            },
          ]}
        />
      )}
    </Panel>
  );
}
