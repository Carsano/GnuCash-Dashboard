"""FastAPI adapter endpoint tests."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from fastapi.testclient import TestClient

from src.adapters.interface.http_api.app import create_app
from src.adapters.interface.http_api.dependencies import (
    get_account_balances_use_case,
    get_accounts_tree_use_case,
    get_accounts_use_case,
    get_asset_category_breakdown_use_case,
    get_budget_applicability_use_case,
    get_budget_month_view_use_case,
    get_budgets_use_case,
    get_backend,
    get_cashflow_asset_selection_use_case,
    get_cashflow_use_case,
    get_net_worth_use_case,
    get_read_mode,
    get_sync_use_case,
)
from src.domain.models.accounts import AccountBalanceDTO, AccountDTO
from src.domain.models.finance import (
    AssetCategoryAmount,
    AssetCategoryBreakdown,
    CashflowItem,
    CashflowSummary,
    CashflowView,
    NetWorthSummary,
)
from src.domain.models.budget import (
    BudgetApplicabilityDTO,
    BudgetDTO,
    BudgetInapplicableReason,
    BudgetMonthNodeResultDTO,
    BudgetMonthSummaryDTO,
    BudgetMonthViewDTO,
)


@dataclass(frozen=True)
class _SyncResult:
    accounts_count: int
    commodities_count: int
    splits_count: int
    transactions_count: int
    prices_count: int


class _AccountsUseCase:
    def execute(self) -> list[AccountDTO]:
        return [
            AccountDTO(
                guid="b-guid",
                name="zeta",
                account_type="ASSET",
                commodity_guid="eur",
                parent_guid=None,
                is_placeholder=True,
            ),
            AccountDTO(
                guid="a-guid",
                name="Alpha",
                account_type="ASSET",
                commodity_guid="eur",
                parent_guid=None,
                is_placeholder=False,
            ),
        ]


class _AccountsTreeUseCase:
    def execute(self) -> list[AccountDTO]:
        return [
            AccountDTO(
                guid="child",
                name="Child",
                account_type="ASSET",
                commodity_guid="eur",
                parent_guid="root",
                is_placeholder=False,
            ),
            AccountDTO(
                guid="root",
                name="Root",
                account_type="ASSET",
                commodity_guid="eur",
                parent_guid=None,
                is_placeholder=True,
            ),
        ]


class _NetWorthUseCase:
    def execute(self, *, start_date=None, end_date=None, target_currency="EUR"):
        _ = (start_date, end_date, target_currency)
        return NetWorthSummary(
            asset_total=Decimal("100.00"),
            liability_total=Decimal("40.00"),
            net_worth=Decimal("60.00"),
            currency_code="EUR",
        )


class _AccountBalancesUseCase:
    def execute(self, *, end_date=None, target_currency="EUR"):
        _ = (end_date, target_currency)
        return [
            AccountBalanceDTO(
                guid="acc-1",
                name="Checking",
                account_type="ASSET",
                parent_guid=None,
                balance=Decimal("12.34"),
                currency_code="EUR",
            ),
            AccountBalanceDTO(
                guid="acc-2",
                name="Loan",
                account_type="LIABILITY",
                parent_guid=None,
                balance=None,
                currency_code="EUR",
            ),
        ]


class _AssetCategoryBreakdownUseCase:
    def execute(
        self,
        *,
        start_date=None,
        end_date=None,
        target_currency="EUR",
        level=1,
    ):
        _ = (start_date, end_date, target_currency, level)
        return AssetCategoryBreakdown(
            currency_code="EUR",
            categories=[
                AssetCategoryAmount(
                    category="Liquidites",
                    amount=Decimal("12.34"),
                    parent_category=None,
                )
            ],
        )


class _CashflowAssetSelectionUseCase:
    def execute(self, *, asset_root_name: str = "Actif"):
        from src.application.use_cases.get_cashflow_asset_selection import (
            CashflowAssetAccountOption,
            CashflowAssetSelection,
        )

        return CashflowAssetSelection(
            asset_root_name=asset_root_name,
            options=(
                CashflowAssetAccountOption(
                    guid="a-1",
                    display_name=f"{asset_root_name}:Banque",
                ),
            ),
            default_selected_guids=("a-1",),
        )


class _CashflowUseCase:
    def execute(
        self,
        *,
        start_date=None,
        end_date=None,
        target_currency="EUR",
        asset_account_guids=None,
    ):
        _ = (start_date, end_date, target_currency, asset_account_guids)
        return CashflowView(
            summary=CashflowSummary(
                total_in=Decimal("20.00"),
                total_out=Decimal("5.50"),
                currency_code="EUR",
            ),
            incoming=[
                CashflowItem(
                    account_full_name="Revenus:Salaire",
                    amount=Decimal("20.00"),
                    top_parent_name="Revenus",
                )
            ],
            outgoing=[
                CashflowItem(
                    account_full_name="Depenses:Courses",
                    amount=Decimal("5.50"),
                    top_parent_name="Depenses",
                )
            ],
        )


class _BudgetsUseCase:
    def execute(self) -> list[BudgetDTO]:
        return [
            BudgetDTO(guid="b2", name="Household", num_periods=12),
            BudgetDTO(guid="b1", name="Essentials", num_periods=12),
        ]


class _BudgetApplicabilityUseCase:
    def execute(self, *, budget_guid: str, month_start=None):
        _ = (budget_guid, month_start)
        return BudgetApplicabilityDTO(applicable=True, reason=None)


class _BudgetMonthViewUseCase:
    def execute(self, *, budget_guid: str, month_start=None, node_paths=None):
        _ = (budget_guid, month_start, node_paths)
        return BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=Decimal("1000.00"),
                total_actual=Decimal("700.50"),
                total_remaining=Decimal("299.50"),
                total_over=Decimal("0.00"),
                status_label="On track",
            ),
            node_results=[
                BudgetMonthNodeResultDTO(
                    node_guid="n1",
                    node_path="Expenses:Food",
                    budget=Decimal("500.00"),
                    actual=Decimal("520.00"),
                    remaining=Decimal("0.00"),
                    over=Decimal("20.00"),
                    status_label="Over",
                    no_budget=False,
                ),
                BudgetMonthNodeResultDTO(
                    node_guid="n2",
                    node_path="Expenses:Rent",
                    budget=Decimal("500.00"),
                    actual=Decimal("180.50"),
                    remaining=Decimal("319.50"),
                    over=Decimal("0.00"),
                    status_label="On track",
                    no_budget=False,
                ),
            ],
        )


class _SyncUseCase:
    def run(self):
        return _SyncResult(
            accounts_count=1,
            commodities_count=2,
            splits_count=3,
            transactions_count=4,
            prices_count=5,
        )


def _build_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_read_mode] = lambda: "tables"
    app.dependency_overrides[get_backend] = lambda: "sqlalchemy"
    app.dependency_overrides[get_accounts_use_case] = _AccountsUseCase
    app.dependency_overrides[get_accounts_tree_use_case] = _AccountsTreeUseCase
    app.dependency_overrides[get_net_worth_use_case] = _NetWorthUseCase
    app.dependency_overrides[get_account_balances_use_case] = (
        _AccountBalancesUseCase
    )
    app.dependency_overrides[get_asset_category_breakdown_use_case] = (
        _AssetCategoryBreakdownUseCase
    )
    app.dependency_overrides[get_cashflow_asset_selection_use_case] = (
        _CashflowAssetSelectionUseCase
    )
    app.dependency_overrides[get_cashflow_use_case] = _CashflowUseCase
    app.dependency_overrides[get_budgets_use_case] = _BudgetsUseCase
    app.dependency_overrides[get_budget_applicability_use_case] = (
        _BudgetApplicabilityUseCase
    )
    app.dependency_overrides[get_budget_month_view_use_case] = (
        _BudgetMonthViewUseCase
    )
    app.dependency_overrides[get_sync_use_case] = _SyncUseCase
    return TestClient(app)


def test_health_and_meta_include_data_version_header() -> None:
    client = _build_client()

    health_response = client.get("/api/v1/health")
    meta_response = client.get("/api/v1/meta")

    assert health_response.status_code == 200
    assert health_response.json() == {"ok": True}
    assert health_response.headers["X-Data-Version"] == "1"
    assert meta_response.json() == {
        "data_version": 1,
        "read_mode": "tables",
        "backend": "sqlalchemy",
    }


def test_sync_increments_data_version() -> None:
    client = _build_client()

    response = client.post("/api/v1/sync/analytics")

    assert response.status_code == 200
    assert response.json()["data_version"] == 2
    assert response.headers["X-Data-Version"] == "2"


def test_accounts_endpoint_returns_deterministic_order() -> None:
    client = _build_client()

    response = client.get("/api/v1/accounts")

    assert response.status_code == 200
    payload = response.json()
    assert [row["name"] for row in payload["accounts"]] == ["Alpha", "zeta"]
    assert payload["accounts"][0]["is_placeholder"] is False
    assert payload["accounts"][1]["is_placeholder"] is True


def test_net_worth_and_cashflow_serialize_decimal_as_strings() -> None:
    client = _build_client()

    net_worth = client.get("/api/v1/net-worth")
    cashflow = client.get("/api/v1/cashflow")

    assert net_worth.status_code == 200
    assert net_worth.json()["asset_total"] == "100.00"
    assert cashflow.status_code == 200
    assert cashflow.json()["summary"]["total_in"] == "20.00"
    assert cashflow.json()["summary"]["difference"] == "14.50"
    assert cashflow.json()["incoming"][0]["amount"] == "20.00"


def test_invalid_level_returns_uniform_400_error() -> None:
    client = _build_client()

    response = client.get("/api/v1/asset-category-breakdown?level=3")

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "invalid_request"
    assert isinstance(payload["error"]["details"], dict)


def test_invalid_date_returns_uniform_400_error() -> None:
    client = _build_client()

    response = client.get("/api/v1/net-worth?start_date=2026-02-99")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_request"


def test_diagnostics_env_shapes_presence_booleans(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setenv("ANALYTICS_DB_URL", "postgresql://example")
    monkeypatch.delenv("GNUCASH_DB_URL", raising=False)
    monkeypatch.setenv("ANALYTICS_READ_MODE", "views")

    response = client.get("/api/v1/diagnostics/env")

    assert response.status_code == 200
    payload = response.json()["env"]
    assert payload["ANALYTICS_DB_URL_present"] is True
    assert payload["GNUCASH_DB_URL_present"] is False
    assert payload["ANALYTICS_READ_MODE"] == "views"


def test_budget_endpoints_serialize_decimal_and_shapes() -> None:
    client = _build_client()

    budgets = client.get("/api/v1/budgets")
    applicability = client.get(
        "/api/v1/budget/applicability?budget_guid=b1&month_start=2026-02-01"
    )
    month_view = client.get(
        "/api/v1/budget/month-view?budget_guid=b1&month_start=2026-02-01"
    )

    assert budgets.status_code == 200
    assert [item["name"] for item in budgets.json()["budgets"]] == [
        "Household",
        "Essentials",
    ]

    assert applicability.status_code == 200
    assert applicability.json() == {"applicable": True, "reason": None}

    assert month_view.status_code == 200
    payload = month_view.json()
    assert payload["summary"]["total_budget"] == "1000.00"
    assert payload["summary"]["total_actual"] == "700.50"
    assert payload["node_results"][0]["over"] == "20.00"


def test_budget_applicability_reason_shape() -> None:
    class _InapplicableUseCase:
        def execute(self, *, budget_guid: str, month_start=None):
            _ = (budget_guid, month_start)
            return BudgetApplicabilityDTO(
                applicable=False,
                reason=BudgetInapplicableReason.NO_TARGETS,
            )

    app = create_app()
    app.dependency_overrides[get_read_mode] = lambda: "tables"
    app.dependency_overrides[get_backend] = lambda: "sqlalchemy"
    app.dependency_overrides[get_budget_applicability_use_case] = (
        _InapplicableUseCase
    )
    client = TestClient(app)

    response = client.get(
        "/api/v1/budget/applicability?budget_guid=b1&month_start=2026-02-01"
    )
    assert response.status_code == 200
    assert response.json() == {
        "applicable": False,
        "reason": "no_targets",
    }
