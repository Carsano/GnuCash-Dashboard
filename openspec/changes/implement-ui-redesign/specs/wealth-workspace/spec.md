## ADDED Requirements

### Requirement: Wealth SHALL provide a stable allocation-centered experience
The `Wealth` route SHALL present asset structure, allocation, and liabilities in one stable strategic view anchored by a persistent allocation visualization.

#### Scenario: Allocation remains the visual anchor
- **WHEN** the user opens or interacts with `Wealth`
- **THEN** the allocation visualization MUST remain a stable reference point for the route

#### Scenario: Wealth includes liabilities in the same experience
- **WHEN** the route displays asset structure
- **THEN** liabilities MUST be available within the same overall Wealth experience using the same hierarchy grammar

### Requirement: Wealth SHALL support inline structural exploration
The `Wealth` route MUST allow users to inspect asset classes, accounts, and liability structure through inline expansion without losing the macro composition view.

#### Scenario: Asset classes expand inline
- **WHEN** the user expands an asset category
- **THEN** the application MUST reveal the underlying structure inline within the current view

#### Scenario: Macro context is preserved during drill-down
- **WHEN** the user explores deeper account structure in `Wealth`
- **THEN** the user MUST remain anchored to the allocation and overall balance-sheet context
