# Component Inventory

## Streamlit UI Pages

- `Dashboard` → `src/adapters/interface/streamlit/page_renderers/dashboard.py`
- `Accounts` → `src/adapters/interface/streamlit/page_renderers/accounts.py`
- `Cashflow` → `src/adapters/interface/streamlit/page_renderers/cashflow.py`
- `Budget` → `src/adapters/interface/streamlit/page_renderers/budget.py`
- `Diagnostics` → `src/adapters/interface/streamlit/page_renderers/diagnostics.py`

## Shared UI Components / Helpers

- Streamlit session + caching helpers: `src/adapters/interface/streamlit/shared.py`
- Cashflow Sankey model + Plotly figure builder: `src/adapters/interface/streamlit/sankey_cashflow.py`

## CLI Components

- Sync jobs and ops tools under `src/adapters/` (see `docs/api-contracts-main.md`).

