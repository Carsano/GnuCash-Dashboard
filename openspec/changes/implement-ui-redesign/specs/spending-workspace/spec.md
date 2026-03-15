## ADDED Requirements

### Requirement: Spending SHALL unify budget and cashflow control
The `Spending` route SHALL present budgeting and cashflow as one operational control experience rather than as separate primary experiences.

#### Scenario: Spending starts with budget control
- **WHEN** the user opens `Spending`
- **THEN** the route MUST show a budget-versus-actual hero as the primary summary

#### Scenario: Cashflow appears as companion context
- **WHEN** `Spending` displays monthly control information
- **THEN** cashflow summary MUST be available as supporting context within the same route experience

### Requirement: Spending SHALL provide inline hierarchical diagnosis
The `Spending` route MUST provide a hierarchical category structure with inline expansion so users can diagnose drift without leaving context.

#### Scenario: Category drill-down stays inline
- **WHEN** the user expands a budget category
- **THEN** the application MUST reveal sub-categories inline within the same hierarchy surface

#### Scenario: Drift is communicated in context
- **WHEN** a category is over target or otherwise concerning
- **THEN** the route MUST present the warning within the module or hierarchy context rather than in a separate global alert area
