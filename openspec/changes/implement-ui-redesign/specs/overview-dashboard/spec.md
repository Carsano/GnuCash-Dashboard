## ADDED Requirements

### Requirement: Overview SHALL present a command-center hierarchy
The `Overview` route SHALL present current financial state using a command-center hierarchy with a dominant net worth hero, a secondary support row, and a lower operational deck.

#### Scenario: Net worth is the dominant signal
- **WHEN** `Overview` loads successfully
- **THEN** current net worth MUST be visually dominant over all other financial summaries

#### Scenario: Support row remains secondary
- **WHEN** asset growth and cash position are displayed
- **THEN** they MUST be presented as secondary support metrics beneath the hero rather than as equal-weight KPI cards

### Requirement: Overview SHALL support contextual drill-in
The `Overview` experience MUST allow users to move into deeper analysis through contextually related modules without losing orientation.

#### Scenario: Overview links into Spending and Wealth
- **WHEN** a user selects a budget/cashflow-related module or a wealth-related module
- **THEN** the application MUST take the user into the corresponding primary experience with preserved context where available

#### Scenario: Overview avoids parity widget clutter
- **WHEN** Overview renders operational information
- **THEN** it MUST use the tiered module composition defined by the redesign rather than an equal-weight widget grid
