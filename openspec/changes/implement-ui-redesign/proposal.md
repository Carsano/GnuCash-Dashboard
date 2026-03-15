## Why

The current frontend delivers API parity, but it does not implement the redesigned product experience defined in the UX specification and brainstorming artifacts. The application needs a structural redesign now so the interface can move from generic financial widgets to a premium, mode-based product shell with clear hierarchy, reusable financial modules, and implementation discipline.

## What Changes

- Replace the current visual token system and global shell with a redesigned application frame aligned to the UX specification.
- Introduce first-class route-backed experiences for `Overview`, `Spending`, and `Wealth`.
- Build shared financial UI primitives for hero metrics, support metrics, allocation visualization, budget/cashflow composition, and hierarchical financial trees.
- Consolidate current budget and cashflow experiences into a unified `Spending` experience.
- Add a new `Wealth` experience for allocation, asset hierarchy, and liabilities.
- Preserve the current frontend app, routing runtime, and API/query layer while migrating screen composition in place.
- Decommission parity-oriented dashboard patterns such as equal-weight KPI grids and ad hoc page-local charting in core flows.

## Capabilities

### New Capabilities

- `design-system-foundation`: Defines the redesign token system, visual roles, layout rules, and reusable shell styling baseline.
- `application-shell-navigation`: Defines the stable shell, route model, command rail, top utility bar, and mode switching behavior.
- `overview-dashboard`: Defines the command-center overview experience with hero hierarchy, support metrics, and operational deck composition.
- `spending-workspace`: Defines the unified spending-control experience combining budget and cashflow into one route-backed workflow.
- `wealth-workspace`: Defines the strategic wealth experience for allocation, asset hierarchy, and liabilities in one stable view.

### Modified Capabilities

- None.

## Impact

- Affected code: `frontend/src/app/*`, `frontend/src/styles/*`, `frontend/src/components/*`, `frontend/src/pages/*`
- Affected systems: React shell, route structure, shared component architecture, core financial screen composition
- Dependencies: existing React Router, TanStack Query, and current HTTP API remain in use
- Implementation impact: requires route migration, component replacement, and new finance-specific UI modules, but does not require a second frontend app or an immediate backend redesign
