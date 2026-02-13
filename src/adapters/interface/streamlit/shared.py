"""Shared Streamlit helpers for the GnuCash dashboard.

This module contains cross-page utilities:
- cached data loaders (wrapping application use cases);
- formatting helpers;
- date range selection widgets;
- cache/session invalidation after analytics sync.
"""

from __future__ import annotations

from collections.abc import Sequence
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
import os

import streamlit as st

from src.application.use_cases.get_account_balances import (
    AccountBalanceDTO,
    GetAccountBalancesUseCase,
)
from src.application.use_cases.get_accounts import AccountDTO, GetAccountsUseCase
from src.application.use_cases.get_accounts_tree import GetAccountsTreeUseCase
from src.application.use_cases.get_asset_category_breakdown import (
    AssetCategoryBreakdown,
    GetAssetCategoryBreakdownUseCase,
)
from src.application.use_cases.get_cashflow import CashflowView, GetCashflowUseCase
from src.application.use_cases.get_cashflow_asset_selection import (
    CashflowAssetSelection,
    GetCashflowAssetSelectionUseCase,
)
from src.application.use_cases.get_budget_applicability import (
    GetBudgetApplicabilityUseCase,
)
from src.application.use_cases.get_budget_month_view import (
    GetBudgetMonthViewUseCase,
)
from src.application.use_cases.get_budgets import GetBudgetsUseCase
from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
    NetWorthSummary,
)
from src.application.use_cases.sync_gnucash_analytics import (
    SyncGnuCashAnalyticsResult,
    SyncGnuCashAnalyticsUseCase,
)
from src.domain.models.budget import BudgetDTO
from src.domain.models.budget import BudgetApplicabilityDTO
from src.domain.models.budget import BudgetMonthViewDTO
from src.infrastructure.container import (
    build_accounts_repository,
    build_accounts_tree_repository,
    build_analytics_repository,
    build_budget_repository,
    build_database_adapter,
)


def invalidate_streamlit_caches() -> None:
    """Invalidate Streamlit caches and known UI session keys.

    This is used after syncing analytics so the dashboard refreshes with
    the new dataset.
    """
    st.session_state.pop("cashflow_sankey_signature", None)
    st.session_state.pop("cashflow_sankey_model", None)
    st.session_state.pop("cashflow_sankey_fig", None)
    if hasattr(st.cache_data, "clear"):
        st.cache_data.clear()


def sync_gnucash_analytics() -> SyncGnuCashAnalyticsResult:
    """Synchronize GnuCash tables into the analytics database.

    Returns:
        SyncGnuCashAnalyticsResult: Row counts per synced table.
    """
    db_port = build_database_adapter()
    use_case = SyncGnuCashAnalyticsUseCase(db_port=db_port)
    return use_case.run()


def _fetch_accounts() -> Sequence[AccountDTO]:
    """Fetch accounts using the analytics database."""
    repository = build_accounts_repository()
    use_case = GetAccountsUseCase(repository=repository)
    return use_case.execute()


def _fetch_accounts_tree() -> Sequence[AccountDTO]:
    """Fetch full accounts hierarchy from the analytics mirror."""
    repository = build_accounts_tree_repository()
    use_case = GetAccountsTreeUseCase(repository=repository)
    return use_case.execute()


def _fetch_budgets() -> Sequence[BudgetDTO]:
    """Fetch budgets using the configured backend."""
    repository = build_budget_repository()
    use_case = GetBudgetsUseCase(repository=repository)
    return use_case.execute()


def _fetch_budget_applicability(
    *,
    budget_guid: str,
    month_start: date,
) -> BudgetApplicabilityDTO:
    """Fetch applicability for the selected budget and month."""

    repository = build_budget_repository()
    use_case = GetBudgetApplicabilityUseCase(repository=repository)
    return use_case.execute(budget_guid=budget_guid, month_start=month_start)


def _fetch_budget_month_view(
    *,
    budget_guid: str,
    month_start: date,
    node_paths: Mapping[str, str] | None = None,
) -> BudgetMonthViewDTO:
    """Fetch month summary + per-node budget view for selected context."""

    repository = build_budget_repository()
    use_case = GetBudgetMonthViewUseCase(repository=repository)
    return use_case.execute(
        budget_guid=budget_guid,
        month_start=month_start,
        node_paths=node_paths,
    )


@st.cache_data(show_spinner=False)
def load_budgets(
    schema_version: int = 1,
    backend: str | None = None,
) -> Sequence[BudgetDTO]:
    """Load budgets and cache them for the Streamlit session.

    Args:
        schema_version: Cache-buster that increments after an analytics sync.
        backend: Optional backend identifier used to scope the cache key.

    Returns:
        Deterministically ordered list of available budgets.
    """
    resolved_backend = (
        backend
        if backend is not None
        else os.getenv("GNUCASH_BACKEND", "sqlalchemy")
    ).strip().lower()
    _ = (schema_version, resolved_backend)
    return _fetch_budgets()


@st.cache_data(show_spinner=False)
def load_budget_applicability(
    *,
    schema_version: int = 1,
    backend: str | None = None,
    budget_guid: str,
    month_start: date,
) -> BudgetApplicabilityDTO:
    """Load and cache the applicability for a selected budget/month context."""

    normalized_month_start = date(month_start.year, month_start.month, 1)
    resolved_backend = (
        backend
        if backend is not None
        else os.getenv("GNUCASH_BACKEND", "sqlalchemy")
    ).strip().lower()
    _ = (schema_version, resolved_backend, budget_guid, normalized_month_start)
    return _fetch_budget_applicability(
        budget_guid=budget_guid,
        month_start=normalized_month_start,
    )


@st.cache_data(show_spinner=False)
def load_budget_month_view(
    *,
    schema_version: int = 1,
    backend: str | None = None,
    budget_guid: str,
    month_start: date,
    node_paths: Mapping[str, str] | None = None,
) -> BudgetMonthViewDTO:
    """Load and cache monthly budget results for selected budget/month."""

    normalized_month_start = date(month_start.year, month_start.month, 1)
    normalized_node_paths = dict(node_paths or {})
    node_paths_cache_key = tuple(
        sorted(normalized_node_paths.items())
    )
    resolved_backend = (
        backend
        if backend is not None
        else os.getenv("GNUCASH_BACKEND", "sqlalchemy")
    ).strip().lower()
    _ = (
        schema_version,
        resolved_backend,
        budget_guid,
        normalized_month_start,
        node_paths_cache_key,
    )
    return _fetch_budget_month_view(
        budget_guid=budget_guid,
        month_start=normalized_month_start,
        node_paths=normalized_node_paths or None,
    )


@st.cache_data(show_spinner=False)
def load_accounts(schema_version: int = 1) -> Sequence[AccountDTO]:
    """Load accounts and cache them for the Streamlit session.

    Args:
        schema_version: Cache-buster that increments after an analytics sync.

    Returns:
        Flat account list from the analytics mirror.
    """
    _ = schema_version
    return _fetch_accounts()


@st.cache_data(show_spinner=False)
def load_accounts_tree(schema_version: int = 1) -> Sequence[AccountDTO]:
    """Load the full accounts hierarchy and cache it for the session.

    Args:
        schema_version: Cache-buster that increments after an analytics sync.

    Returns:
        Flat account list containing parent relationships (tree in edges).
    """
    _ = schema_version
    return _fetch_accounts_tree()


def _fetch_cashflow_asset_selection(asset_root_name: str) -> CashflowAssetSelection:
    """Fetch and build cashflow asset account selection options."""
    repository = build_accounts_tree_repository()
    use_case = GetCashflowAssetSelectionUseCase(repository=repository)
    return use_case.execute(asset_root_name=asset_root_name)


@st.cache_data(show_spinner=False)
def load_cashflow_asset_selection(
    asset_root_name: str,
    schema_version: int = 1,
) -> CashflowAssetSelection:
    """Load cashflow asset selection options with Streamlit caching.

    Args:
        asset_root_name: Root account name identifying assets ("Actif").
        schema_version: Cache-buster that increments after an analytics sync.

    Returns:
        CashflowAssetSelection: Deterministic options and default selection.
    """
    _ = schema_version
    return _fetch_cashflow_asset_selection(asset_root_name)


def _fetch_net_worth_summary(
    start_date: date | None,
    end_date: date | None,
) -> NetWorthSummary:
    """Fetch the net worth summary from the analytics database."""
    gnucash_repository = build_analytics_repository()
    use_case = GetNetWorthSummaryUseCase(gnucash_repository=gnucash_repository)
    return use_case.execute(start_date=start_date, end_date=end_date)


@st.cache_data(show_spinner=False)
def load_net_worth_summary(
    start_date: date | None,
    end_date: date | None,
    schema_version: int = 1,
) -> NetWorthSummary:
    """Load a net worth summary with Streamlit caching.

    Args:
        start_date: Optional start date.
        end_date: Optional end date.
        schema_version: Cache-buster that increments after an analytics sync.

    Returns:
        NetWorthSummary for the provided period.
    """
    _ = schema_version
    return _fetch_net_worth_summary(start_date, end_date)


def _fetch_account_balances(
    end_date: date | None,
    target_currency: str,
) -> Sequence[AccountBalanceDTO]:
    """Fetch account balances using the analytics database."""
    repository = build_analytics_repository()
    use_case = GetAccountBalancesUseCase(gnucash_repository=repository)
    return use_case.execute(end_date=end_date, target_currency=target_currency)


@st.cache_data(show_spinner=False)
def load_account_balances(
    end_date: date | None,
    target_currency: str,
    schema_version: int = 1,
) -> Sequence[AccountBalanceDTO]:
    """Load account balances with Streamlit caching.

    Args:
        end_date: Optional end date used for balances.
        target_currency: Currency code for conversion (e.g. "EUR").
        schema_version: Cache-buster that increments after an analytics sync.

    Returns:
        AccountBalanceDTO rows for the requested end date.
    """
    _ = schema_version
    return _fetch_account_balances(end_date, target_currency)


def _fetch_asset_category_breakdown(
    end_date: date | None,
    level: int,
) -> AssetCategoryBreakdown:
    """Fetch asset category breakdown in EUR from analytics."""
    gnucash_repository = build_analytics_repository()
    use_case = GetAssetCategoryBreakdownUseCase(
        gnucash_repository=gnucash_repository
    )
    return use_case.execute(
        end_date=end_date,
        target_currency="EUR",
        level=level,
    )


@st.cache_data(show_spinner=False)
def load_asset_category_breakdown(
    end_date: date | None,
    level: int,
    schema_version: int = 1,
) -> AssetCategoryBreakdown:
    """Load asset category breakdown with Streamlit caching.

    Args:
        end_date: Optional end date used for balances.
        level: Category depth.
        schema_version: Cache-buster that increments after an analytics sync.

    Returns:
        Aggregated asset totals by category.
    """
    _ = schema_version
    return _fetch_asset_category_breakdown(end_date, level)


def _fetch_cashflow_view(
    start_date: date | None,
    end_date: date | None,
    asset_account_guids: tuple[str, ...] | None = None,
) -> CashflowView:
    """Fetch cashflow view using the analytics database."""
    repository = build_analytics_repository()
    use_case = GetCashflowUseCase(gnucash_repository=repository)
    return use_case.execute(
        start_date=start_date,
        end_date=end_date,
        target_currency="EUR",
        asset_account_guids=list(asset_account_guids)
        if asset_account_guids is not None
        else None,
    )


@st.cache_data(show_spinner=False)
def load_cashflow_view(
    start_date: date | None,
    end_date: date | None,
    asset_account_guids: tuple[str, ...] | None = None,
    schema_version: int = 1,
) -> CashflowView:
    """Load cashflow view with Streamlit caching.

    Args:
        start_date: Optional start date.
        end_date: Optional end date.
        asset_account_guids: Optional set of asset accounts to scope cashflow.
        schema_version: Cache-buster that increments after an analytics sync.

    Returns:
        A fully computed CashflowView.
    """
    _ = schema_version
    return _fetch_cashflow_view(start_date, end_date, asset_account_guids)


def format_currency(value: Decimal, currency_code: str) -> str:
    """Format currency values for display."""
    symbol = "€" if currency_code == "EUR" else currency_code
    return f"{value:,.2f} {symbol}"


def format_optional_currency(value: Decimal | None, currency_code: str) -> str:
    """Format currency values while handling missing amounts."""
    if value is None:
        return "—"
    return format_currency(value, currency_code)


def format_delta(value: Decimal) -> str:
    """Format delta values for display."""
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:,.2f}"


def format_delta_with_percent(delta: Decimal, baseline: Decimal) -> str:
    """Format delta value with percentage change."""
    if baseline == 0:
        return format_delta(delta)
    percent = (delta / baseline) * Decimal("100")
    sign = "+" if percent >= 0 else ""
    return f"{format_delta(delta)} ({sign}{percent:.2f}%)"


def get_period_start(period: str, today: date) -> date | None:
    """Return the start date for the selected period."""
    if period == "All Time":
        return None
    if period == "YTD":
        return date(today.year, 1, 1)
    if period == "MTD":
        return date(today.year, today.month, 1)
    if period == "QTD":
        quarter = (today.month - 1) // 3
        start_month = quarter * 3 + 1
        return date(today.year, start_month, 1)
    return None


def get_date_inputs(today: date, *, key_prefix: str) -> tuple[date, date]:
    """Return start/end dates chosen in the dashboard.

    Args:
        today: Reference date used for max values and defaults.
        key_prefix: Prefix used to keep widget state isolated per page.

    Returns:
        Tuple of (start_date, end_date).
    """
    start_key = f"{key_prefix}_start_date"
    end_key = f"{key_prefix}_end_date"
    form_key = f"{key_prefix}_date_form"

    if start_key not in st.session_state:
        st.session_state[start_key] = date(today.year, 1, 1)
    if end_key not in st.session_state:
        st.session_state[end_key] = today

    with st.form(form_key, clear_on_submit=False):
        start_col, end_col = st.columns(2)
        with start_col:
            st.date_input(
                "Start date",
                key=start_key,
                max_value=today,
            )
        with end_col:
            st.date_input(
                "End date",
                key=end_key,
                max_value=today,
            )
        st.form_submit_button("Appliquer")

    start_date: date = st.session_state[start_key]
    end_date: date = st.session_state[end_key]
    if start_date > end_date:
        st.warning("Start date is after end date. Swapping values.")
        st.session_state[start_key] = end_date
        st.session_state[end_key] = start_date
        start_date, end_date = end_date, start_date
    return start_date, end_date
