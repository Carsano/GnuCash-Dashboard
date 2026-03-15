# Component Inventory

## React UI Pages

- `DashboardPage` → `frontend/src/pages/DashboardPage.tsx`
- `AccountsPage` → `frontend/src/pages/AccountsPage.tsx`
- `CashflowPage` → `frontend/src/pages/CashflowPage.tsx`
- `BudgetPage` → `frontend/src/pages/BudgetPage.tsx`
- `DiagnosticsPage` → `frontend/src/pages/DiagnosticsPage.tsx`

## API Adapter Components

- FastAPI app factory: `src/adapters/interface/http_api/app.py`
- FastAPI routes: `src/adapters/interface/http_api/router.py`
- Dependency providers: `src/adapters/interface/http_api/dependencies.py`
- Serialization helpers: `src/adapters/interface/http_api/serialization.py`

## CLI Components

- Sync jobs and ops tools under `src/adapters/`.
