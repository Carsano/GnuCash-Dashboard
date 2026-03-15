"""API v1 routes for the FastAPI adapter."""

from __future__ import annotations

from datetime import date
import os

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text

from src.adapters.interface.http_api.data_version import DataVersionStore
from src.adapters.interface.http_api.dependencies import (
    get_account_balances_use_case,
    get_accounts_tree_use_case,
    get_accounts_use_case,
    get_asset_category_breakdown_use_case,
    get_backend,
    get_cashflow_asset_selection_use_case,
    get_cashflow_use_case,
    get_data_version_store,
    get_budget_applicability_use_case,
    get_budget_month_view_use_case,
    get_budgets_use_case,
    get_net_worth_use_case,
    get_read_mode,
    get_sync_use_case,
)
from src.adapters.interface.http_api.serialization import to_api_value
from src.infrastructure.container import build_database_adapter

router = APIRouter(prefix="/api/v1")

_EXPECTED_ANALYTICS_VIEWS = (
    "vw_currency_lookup",
    "vw_net_worth_balances",
    "vw_asset_category_balances",
    "vw_latest_prices",
)


def _safe_env_present(name: str) -> bool:
    value = os.getenv(name)
    return bool(value and value.strip())


def _split_asset_guids(asset_guids: str | None) -> list[str] | None:
    if asset_guids is None:
        return None
    parts = [item.strip() for item in asset_guids.split(",")]
    filtered = [item for item in parts if item]
    if not filtered:
        return None
    return filtered


def _build_node_paths(accounts: list) -> dict[str, str]:
    accounts_by_guid = {account.guid: account for account in accounts}
    paths: dict[str, str] = {}
    for account in accounts:
        cursor = account
        seen: set[str] = set()
        parts: list[str] = []
        while cursor.guid not in seen:
            seen.add(cursor.guid)
            parts.append(cursor.name)
            if not cursor.parent_guid:
                break
            parent = accounts_by_guid.get(cursor.parent_guid)
            if parent is None:
                break
            cursor = parent
        paths[account.guid] = ":".join(reversed(parts))
    return paths


@router.get("/health")
def get_health() -> dict[str, bool]:
    return {"ok": True}


@router.get("/meta")
def get_meta(
    data_version_store: DataVersionStore = Depends(get_data_version_store),
    read_mode: str = Depends(get_read_mode),
    backend: str = Depends(get_backend),
) -> dict[str, int | str]:
    return {
        "data_version": data_version_store.get(),
        "read_mode": read_mode,
        "backend": backend,
    }


@router.post("/sync/analytics")
def sync_analytics(
    sync_use_case=Depends(get_sync_use_case),
    data_version_store: DataVersionStore = Depends(get_data_version_store),
) -> dict[str, int]:
    result = sync_use_case.run()
    data_version = data_version_store.bump()
    payload = to_api_value(result)
    payload["data_version"] = data_version
    return payload


@router.get("/accounts")
def get_accounts(
    accounts_use_case=Depends(get_accounts_use_case),
) -> dict[str, list[dict[str, object]]]:
    accounts = accounts_use_case.execute()
    ordered = sorted(accounts, key=lambda item: (item.name.lower(), item.guid))
    return {"accounts": to_api_value(ordered)}


@router.get("/accounts/tree")
def get_accounts_tree(
    accounts_tree_use_case=Depends(get_accounts_tree_use_case),
) -> dict[str, list[dict[str, object]]]:
    accounts = accounts_tree_use_case.execute()
    ordered = sorted(accounts, key=lambda item: (item.name.lower(), item.guid))
    return {"accounts": to_api_value(ordered)}


@router.get("/net-worth")
def get_net_worth(
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str = Query(default="EUR", min_length=1),
    net_worth_use_case=Depends(get_net_worth_use_case),
) -> dict[str, object]:
    result = net_worth_use_case.execute(
        start_date=start_date,
        end_date=end_date,
        target_currency=currency,
    )
    return to_api_value(result)


@router.get("/account-balances")
def get_account_balances(
    end_date: date | None = None,
    currency: str = Query(default="EUR", min_length=1),
    account_balances_use_case=Depends(get_account_balances_use_case),
) -> dict[str, list[dict[str, object]]]:
    balances = account_balances_use_case.execute(
        end_date=end_date,
        target_currency=currency,
    )
    return {"balances": to_api_value(balances)}


@router.get("/asset-category-breakdown")
def get_asset_category_breakdown(
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str = Query(default="EUR", min_length=1),
    level: int = Query(default=1, ge=1, le=2),
    breakdown_use_case=Depends(get_asset_category_breakdown_use_case),
) -> dict[str, object]:
    result = breakdown_use_case.execute(
        start_date=start_date,
        end_date=end_date,
        target_currency=currency,
        level=level,
    )
    return to_api_value(result)


@router.get("/cashflow/asset-selection")
def get_cashflow_asset_selection(
    asset_root_name: str = Query(default="Actif", min_length=1),
    selection_use_case=Depends(get_cashflow_asset_selection_use_case),
) -> dict[str, object]:
    result = selection_use_case.execute(asset_root_name=asset_root_name)
    return to_api_value(result)


@router.get("/cashflow")
def get_cashflow(
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str = Query(default="EUR", min_length=1),
    asset_guids: str | None = None,
    cashflow_use_case=Depends(get_cashflow_use_case),
) -> dict[str, object]:
    result = cashflow_use_case.execute(
        start_date=start_date,
        end_date=end_date,
        target_currency=currency,
        asset_account_guids=_split_asset_guids(asset_guids),
    )
    payload = to_api_value(result)
    payload["summary"]["difference"] = to_api_value(result.summary.difference)
    return payload


@router.get("/budgets")
def get_budgets(
    budgets_use_case=Depends(get_budgets_use_case),
) -> dict[str, list[dict[str, object]]]:
    budgets = budgets_use_case.execute()
    return {"budgets": to_api_value(budgets)}


@router.get("/budget/applicability")
def get_budget_applicability(
    budget_guid: str = Query(min_length=1),
    month_start: date | None = None,
    applicability_use_case=Depends(get_budget_applicability_use_case),
) -> dict[str, object]:
    resolved_month = month_start or date.today().replace(day=1)
    result = applicability_use_case.execute(
        budget_guid=budget_guid,
        month_start=resolved_month,
    )
    return to_api_value(result)


@router.get("/budget/month-view")
def get_budget_month_view(
    budget_guid: str = Query(min_length=1),
    month_start: date | None = None,
    month_view_use_case=Depends(get_budget_month_view_use_case),
    accounts_tree_use_case=Depends(get_accounts_tree_use_case),
) -> dict[str, object]:
    resolved_month = month_start or date.today().replace(day=1)
    accounts = accounts_tree_use_case.execute()
    node_paths = _build_node_paths(accounts)
    result = month_view_use_case.execute(
        budget_guid=budget_guid,
        month_start=resolved_month,
        node_paths=node_paths,
    )
    return to_api_value(result)


@router.get("/diagnostics/env")
def get_diagnostics_env() -> dict[str, dict[str, str | bool]]:
    return {
        "env": {
            "ANALYTICS_DB_URL_present": _safe_env_present("ANALYTICS_DB_URL"),
            "GNUCASH_DB_URL_present": _safe_env_present("GNUCASH_DB_URL"),
            "ANALYTICS_READ_MODE": os.getenv("ANALYTICS_READ_MODE", "tables")
            .strip()
            .lower(),
        }
    }


@router.get("/diagnostics/db")
def get_diagnostics_db(
    request: Request,
) -> dict[str, object]:
    read_mode = os.getenv("ANALYTICS_READ_MODE", "tables").strip().lower()
    try:
        engine = build_database_adapter().get_analytics_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
            rows: list[dict[str, object]] = []
            if read_mode == "views":
                for view_name in _EXPECTED_ANALYTICS_VIEWS:
                    exists = conn.execute(
                        text(
                            """
                            SELECT EXISTS (
                                SELECT 1
                                FROM information_schema.views
                                WHERE lower(table_name) = lower(:view_name)
                            ) AS present
                            """
                        ),
                        {"view_name": view_name},
                    ).scalar()
                    rows.append({"name": view_name, "present": bool(exists)})
        return {"analytics_db_ok": True, "views": rows}
    except Exception as exc:  # noqa: BLE001
        request.app.state.logger.warning(
            "Diagnostics DB check failed: %s",
            exc,
        )
        return {
            "analytics_db_ok": False,
            "views": [],
            "error": {"code": type(exc).__name__, "message": str(exc)},
        }
