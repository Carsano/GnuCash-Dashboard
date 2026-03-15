## ADDED Requirements

### Requirement: The redesign SHALL provide a unified visual token system
The frontend SHALL expose a shared token system for color, typography, spacing, radii, borders, motion, and interaction states so all redesigned routes use one visual foundation.

#### Scenario: Token system replaces legacy visual roles
- **WHEN** the redesign shell or a redesigned route renders
- **THEN** it MUST use semantic redesign tokens rather than legacy route-local color and spacing assumptions

#### Scenario: Token system supports route consistency
- **WHEN** `Overview`, `Spending`, and `Wealth` are rendered
- **THEN** the visual hierarchy, accent usage, spacing rhythm, and focus treatment MUST remain consistent across routes

### Requirement: The redesign SHALL support premium dark-surface accessibility
The token system MUST support the warm-charcoal dark visual direction while maintaining WCAG AA-compliant contrast and non-color-only state signaling.

#### Scenario: Text contrast remains compliant
- **WHEN** text, labels, helper copy, and values are shown on redesign surfaces
- **THEN** their contrast MUST meet the configured accessibility baseline for the route context

#### Scenario: State is not conveyed by color alone
- **WHEN** success, warning, error, or focus states are presented
- **THEN** the UI MUST include a secondary cue such as iconography, copy, border treatment, or focus style
