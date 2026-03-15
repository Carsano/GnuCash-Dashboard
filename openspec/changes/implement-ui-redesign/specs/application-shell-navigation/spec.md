## ADDED Requirements

### Requirement: The frontend SHALL provide a stable redesigned application shell
The application SHALL provide a shared shell with a left command rail, a top utility bar, a mode switch, and a route content slot for redesigned primary experiences.

#### Scenario: Shared shell frames redesigned routes
- **WHEN** the user navigates to `Overview`, `Spending`, or `Wealth`
- **THEN** the same shell structure MUST frame the route while allowing route-specific content to change

#### Scenario: Shell remains stable during navigation
- **WHEN** the user switches between primary redesigned routes
- **THEN** the navigation frame MUST remain visually stable and MUST NOT reflow into unrelated layouts

### Requirement: Primary redesign experiences SHALL be route-backed
The redesigned application MUST expose first-class route-backed experiences for `Overview`, `Spending`, and `Wealth`.

#### Scenario: Root and legacy dashboard routes resolve to Overview
- **WHEN** the user opens `/` or `/dashboard`
- **THEN** the application MUST take the user to the redesigned `Overview` experience

#### Scenario: Route identity is explicit
- **WHEN** the user navigates among primary redesign experiences
- **THEN** the application MUST expose explicit route transitions rather than only local tab or widget state changes
