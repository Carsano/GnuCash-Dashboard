## Context

The current frontend is a small React 19 + Vite application with clear route boundaries, a centralized query layer, and a minimal shared shell. That makes it a good candidate for an in-place redesign rather than a parallel rebuild. The redesign is driven by the UX specification and brainstorming artifacts, which define a premium financial control surface built around a stable shell, route-backed modes, and reusable finance-specific modules.

The current state has three architectural limitations:

- the shell is parity-oriented and not aligned to the new mental model
- page composition is widget-first rather than hierarchy-first
- current primitives such as `Card`, `KpiGrid`, and `DataTable` are too generic for the target UX

Stakeholders for this design are frontend implementation, UX validation, and release quality. The main constraint is preserving the current app, query layer, and backend contract while replacing the user-facing composition model.

## Goals / Non-Goals

**Goals:**

- Deliver the redesign inside the existing frontend app.
- Establish a stable application shell with command rail, utility bar, and route-backed primary experiences.
- Build reusable financial primitives so `Overview`, `Spending`, and `Wealth` do not diverge architecturally.
- Keep the existing query/data layer as the transport boundary and add presentation-specific view-model shaping on top.
- Support incremental PR-based migration and safe rollback to the last stable UI state during implementation.

**Non-Goals:**

- Rebuilding the frontend in a new framework or second app.
- Redesigning backend contracts as part of this change.
- Expanding business logic scope beyond what the UX requires.
- Solving every secondary route and diagnostics surface before the core product shell is stable.

## Decisions

### Decision: Use in-place migration, not a parallel frontend

Rationale:

- the current app is structurally small and replaceable
- a second frontend would increase merge cost and drift risk
- route, query, and runtime boundaries are already usable

Alternatives considered:

- Parallel frontend rewrite: rejected because it duplicates infrastructure and delays real integration.
- Visual-only restyle of the current app: rejected because the shell and page composition model are fundamentally wrong for the target UX.

### Decision: Introduce explicit `/overview`, `/spending`, and `/wealth` routes

Rationale:

- these map directly to the UX mental model
- route-backed modes reduce ambiguity in navigation and testing
- route-level ownership improves incremental migration

Alternatives considered:

- local tabs inside one dashboard route: rejected because it hides architectural intent and complicates migration from current routes
- keeping `dashboard`, `budget`, and `cashflow` as primary destinations: rejected because it preserves the old parity model

### Decision: Replace shell and tokens before core screens

Rationale:

- the shell defines hierarchy, navigation, and global visual language
- screen work without a stable shell produces expensive rework
- token reset is required to prevent old and new visual systems from colliding

Alternatives considered:

- build Overview first inside the old shell: rejected because it anchors the new design to the wrong frame
- defer token work until after page implementation: rejected because pages would accumulate ad hoc styling

### Decision: Keep the current query/API layer and add view-model shaping

Rationale:

- the query layer already centralizes HTTP and caching concerns
- redesign requirements are mostly presentation and composition driven
- view-model functions create the right boundary between transport DTOs and UX modules

Alternatives considered:

- redesign API access before UI work: rejected because it delays visible progress without solving the current UX problem
- pipe raw DTOs directly into new components: rejected because current DTOs are not aligned to the module hierarchy

### Decision: Build finance-specific component layers alongside generic primitives

Rationale:

- the redesign requires product-defining modules, not just better cards
- overloading `Card`, `KpiGrid`, or `DataTable` would create unclear long-term architecture
- explicit finance modules improve ownership and reuse

Alternatives considered:

- evolve all redesign components inside `components/ui`: rejected because the domain-specific modules would become buried and ambiguous
- keep page-local components in each route: rejected because it guarantees duplication and divergence

### Decision: Consolidate current Budget and Cashflow experiences into Spending

Rationale:

- the UX defines one operational spending-control flow
- users should not have to think in separate legacy route concepts
- existing budget and cashflow logic can still be reused beneath a new composition

Alternatives considered:

- preserve separate Budget and Cashflow as primary redesign routes: rejected because it conflicts with the new product mental model
- remove one of them without consolidation: rejected because both data domains contribute to the Spending experience

### Decision: Introduce shared chart wrappers before final screen implementation

Rationale:

- chart styling is part of the product identity
- page-local chart implementations would drift immediately
- the redesign requires consistent treatment of lines, rings, tooltips, and summary behavior

Alternatives considered:

- continue with lightweight page-specific CSS bars and rails: rejected for final architecture because it does not scale to the target UX

## Risks / Trade-offs

- [Route migration complexity] -> Mitigation: keep legacy redirects during transition and migrate one primary route at a time.
- [Old generic primitives may linger too long] -> Mitigation: treat them as transitional and block new core-screen work from depending on them.
- [Current APIs may not perfectly fit Wealth and Spending view-models] -> Mitigation: use front-end view-model shaping first and only escalate to backend changes if a true data gap remains.
- [Dark theme readability regressions] -> Mitigation: validate contrast and focus behavior during primitive implementation, not at the end.
- [Spending consolidation may blur legacy responsibilities during migration] -> Mitigation: define Spending as the destination architecture early and use old pages only as temporary logic sources.

## Migration Plan

1. Reset global tokens and shared styling foundation.
2. Replace the shell and route scaffolding.
3. Add navigation, layout, and chart wrappers.
4. Add finance-specific primitives.
5. Build `Overview` as the reference implementation.
6. Build `Spending` by consolidating budget and cashflow behaviors.
7. Build `Wealth` as a first-class route-backed screen.
8. Decommission or redirect legacy route concepts.
9. Complete responsive, accessibility, and polish passes.

Rollback strategy:

- Each PR slice must leave the app in a working state.
- Legacy routes remain available until their replacement route is stable.
- Shell replacement and route changes should be isolated enough that they can be reverted without touching the query layer.

## Open Questions

- Does `AccountsPage` remain a distinct supporting route after `Wealth` ships, or does it become secondary detail access under wealth concepts?
- Does `CashflowPage` survive as a support route after Spending stabilizes, or is its remaining detail fully absorbed?
- Will the final chart wrapper use a dedicated visualization library or a project-local rendering abstraction on top of existing primitives?
