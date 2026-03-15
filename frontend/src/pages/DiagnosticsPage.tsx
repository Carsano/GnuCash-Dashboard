import { InlineError } from "../components/states/InlineError";
import { KpiSkeleton } from "../components/skeletons/KpiSkeleton";
import { DataTable } from "../components/ui/DataTable";
import { Panel } from "../components/ui/Panel";
import { useDiagnosticsDbQuery, useDiagnosticsEnvQuery } from "../lib/api/queries";

export function DiagnosticsPage() {
  const envQuery = useDiagnosticsEnvQuery();
  const dbQuery = useDiagnosticsDbQuery();

  const hasError = envQuery.error || dbQuery.error;
  const isLoading = envQuery.isLoading || dbQuery.isLoading;

  return (
    <Panel title="Diagnostics" subtitle="Environment presence, connectivity, and view checks">
      {isLoading ? (
        <KpiSkeleton />
      ) : hasError ? (
        <InlineError
          message={(envQuery.error as Error)?.message ?? (dbQuery.error as Error)?.message}
          onRetry={() => {
            void envQuery.refetch();
            void dbQuery.refetch();
          }}
        />
      ) : (
        <>
          <DataTable
            rows={[
              {
                variable: "ANALYTICS_DB_URL",
                value: String(envQuery.data?.env.ANALYTICS_DB_URL_present ?? false),
              },
              {
                variable: "GNUCASH_DB_URL",
                value: String(envQuery.data?.env.GNUCASH_DB_URL_present ?? false),
              },
              {
                variable: "ANALYTICS_READ_MODE",
                value: envQuery.data?.env.ANALYTICS_READ_MODE ?? "unknown",
              },
              {
                variable: "analytics_db_ok",
                value: String(dbQuery.data?.analytics_db_ok ?? false),
              },
            ]}
            columns={[
              { key: "variable", title: "Variable", render: (row) => row.variable },
              { key: "value", title: "Value", render: (row) => row.value },
            ]}
          />

          <DataTable
            rows={dbQuery.data?.views ?? []}
            emptyLabel="No view checks returned (tables mode or no configured views)."
            columns={[
              { key: "name", title: "View", render: (row) => row.name },
              {
                key: "present",
                title: "Present",
                render: (row) => String(row.present),
              },
            ]}
          />

          {dbQuery.data?.error ? (
            <InlineError message={`${dbQuery.data.error.code}: ${dbQuery.data.error.message}`} />
          ) : null}
        </>
      )}
    </Panel>
  );
}
