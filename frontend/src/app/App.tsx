import "./app.css";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";

import { AppShell } from "../components/AppShell";
import { DashboardPage } from "../pages/DashboardPage";
import { AccountsPage } from "../pages/AccountsPage";
import { CashflowPage } from "../pages/CashflowPage";
import { DiagnosticsPage } from "../pages/DiagnosticsPage";
import { BudgetPage } from "../pages/BudgetPage";
import { InlineError } from "../components/states/InlineError";
import { useDataVersion, useMetaQuery } from "../lib/api/queries";

export function App() {
  const [density, setDensity] = useState<"comfortable" | "dense">("comfortable");
  const location = useLocation();
  const dataVersion = useDataVersion();
  const metaQuery = useMetaQuery();

  useEffect(() => {
    document.documentElement.dataset.density = density;
  }, [density]);

  return (
    <AppShell density={density} onDensityChange={setDensity} dataVersion={dataVersion}>
      <div className="topbar">
        <h2>{location.pathname === "/" ? "/dashboard" : location.pathname}</h2>
        <p>
          Backend mode: {metaQuery.data?.backend ?? "..."} | Read mode: {metaQuery.data?.read_mode ?? "..."}
        </p>
      </div>

      {metaQuery.error ? (
        <InlineError
          message={(metaQuery.error as Error).message}
          onRetry={() => void metaQuery.refetch()}
        />
      ) : null}

      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/accounts" element={<AccountsPage />} />
        <Route path="/cashflow" element={<CashflowPage />} />
        <Route path="/diagnostics" element={<DiagnosticsPage />} />
        <Route path="/budget" element={<BudgetPage />} />
      </Routes>
    </AppShell>
  );
}
