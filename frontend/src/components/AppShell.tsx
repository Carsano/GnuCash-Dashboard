import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";

import { Toggle } from "./ui/Toggle";

type Props = {
  density: "comfortable" | "dense";
  onDensityChange: (density: "comfortable" | "dense") => void;
  dataVersion?: number;
  children: ReactNode;
};

export function AppShell({ density, onDensityChange, dataVersion, children }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>GnuCash Dashboard</h1>
          <p>FastAPI + React migration</p>
        </div>
        <nav className="nav">
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/accounts">Accounts</NavLink>
          <NavLink to="/cashflow">Cashflow</NavLink>
          <NavLink to="/diagnostics">Diagnostics</NavLink>
          <NavLink to="/budget">Budget</NavLink>
        </nav>
        <div className="sidebar-footer">
          <Toggle
            checked={density === "dense"}
            onChange={(next) => onDensityChange(next ? "dense" : "comfortable")}
            label="Dense mode"
          />
          <div className="pill">Data version: {dataVersion ?? "..."}</div>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
