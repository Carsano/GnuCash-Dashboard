"""Streamlit dashboard entry point."""

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

import altair as alt
import streamlit as st

from src.application.use_cases.get_accounts import (
    AccountDTO,
    GetAccountsUseCase,
)
from src.application.use_cases.get_account_balances import (
    AccountBalanceDTO,
    GetAccountBalancesUseCase,
)
from src.application.use_cases.get_cashflow import (
    CashflowView,
    GetCashflowUseCase,
)
from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
    NetWorthSummary,
)
from src.application.use_cases.get_asset_category_breakdown import (
    AssetCategoryBreakdown,
    GetAssetCategoryBreakdownUseCase,
)
from src.infrastructure.container import (
    build_accounts_repository,
    build_analytics_repository,
)
from src.infrastructure.logging.logger import get_app_logger

from src.adapters.interface.streamlit.sankey_cashflow import (
    SankeyState,
    apply_click,
    build_plotly_figure,
    build_sankey_model,
)


def _fetch_accounts() -> Sequence[AccountDTO]:
    """Fetch accounts using the analytics database."""
    repository = build_accounts_repository()
    use_case = GetAccountsUseCase(repository=repository)
    return use_case.execute()


@st.cache_data(show_spinner=False)
def _load_accounts() -> Sequence[AccountDTO]:
    """Cached wrapper around _fetch_accounts for Streamlit sessions."""
    return _fetch_accounts()


def _fetch_net_worth_summary(
    start_date: date | None,
    end_date: date | None,
) -> NetWorthSummary:
    """Fetch the net worth summary from the analytics database."""
    gnucash_repository = build_analytics_repository()
    use_case = GetNetWorthSummaryUseCase(
        gnucash_repository=gnucash_repository
    )
    return use_case.execute(start_date=start_date, end_date=end_date)


@st.cache_data(show_spinner=False)
def _load_net_worth_summary(
    start_date: date | None,
    end_date: date | None,
    schema_version: int = 1,
) -> NetWorthSummary:
    """Cached wrapper around _fetch_net_worth_summary."""
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
def _load_account_balances(
    end_date: date | None,
    target_currency: str,
    schema_version: int = 1,
) -> Sequence[AccountBalanceDTO]:
    """Cached wrapper around _fetch_account_balances."""
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
def _load_asset_category_breakdown(
    end_date: date | None,
    level: int,
    schema_version: int = 1,
) -> AssetCategoryBreakdown:
    """Cached wrapper around _fetch_asset_category_breakdown."""
    _ = schema_version
    return _fetch_asset_category_breakdown(end_date, level)


def _fetch_cashflow_view(
    start_date: date | None,
    end_date: date | None,
) -> CashflowView:
    """Fetch cashflow view using the analytics database."""
    repository = build_analytics_repository()
    use_case = GetCashflowUseCase(gnucash_repository=repository)
    return use_case.execute(
        start_date=start_date,
        end_date=end_date,
        target_currency="EUR",
    )


@st.cache_data(show_spinner=False)
def _load_cashflow_view(
    start_date: date | None,
    end_date: date | None,
    schema_version: int = 1,
) -> CashflowView:
    """Cached wrapper around _fetch_cashflow_view."""
    _ = schema_version
    return _fetch_cashflow_view(start_date, end_date)


def _format_currency(value: Decimal, currency_code: str) -> str:
    """Format currency values for display."""
    symbol = "€" if currency_code == "EUR" else currency_code
    return f"{value:,.2f} {symbol}"


def _format_optional_currency(
    value: Decimal | None,
    currency_code: str,
) -> str:
    """Format currency values while handling missing amounts."""
    if value is None:
        return "—"
    return _format_currency(value, currency_code)


def _format_delta(value: Decimal) -> str:
    """Format delta values for display."""
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:,.2f}"


def _format_delta_with_percent(
    delta: Decimal,
    baseline: Decimal,
) -> str:
    """Format delta value with percentage change."""
    if baseline == 0:
        return _format_delta(delta)
    percent = (delta / baseline) * Decimal("100")
    sign = "+" if percent >= 0 else ""
    return f"{_format_delta(delta)} ({sign}{percent:.2f}%)"


def _check_altair_dependencies() -> tuple[bool, str | None]:
    """Check that Altair dependencies are available and healthy.

    Returns:
        Tuple with a boolean status and an optional error message.
    """
    try:
        import numpy as np
        import pandas as pd
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    if not hasattr(np, "ndarray"):
        return False, "numpy import incomplete: missing ndarray"
    if not hasattr(pd, "Timestamp"):
        return False, "pandas import incomplete: missing Timestamp"
    return True, None


def _get_period_start(
    period: str,
    today: date,
) -> date | None:
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


def _get_date_inputs(today: date, *, key_prefix: str) -> tuple[date, date]:
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


def _zero_summary(currency_code: str) -> NetWorthSummary:
    """Return a zeroed net worth summary."""
    return NetWorthSummary(
        asset_total=Decimal("0"),
        liability_total=Decimal("0"),
        net_worth=Decimal("0"),
        currency_code=currency_code,
    )


def _render_cashflow_summary(view: CashflowView) -> None:
    """Render cashflow totals with colored difference."""
    summary = view.summary
    incoming_col, outgoing_col, diff_col = st.columns(3)
    incoming_col.metric(
        "Entrées",
        _format_currency(summary.total_in, summary.currency_code),
    )
    outgoing_col.metric(
        "Sorties",
        _format_currency(summary.total_out, summary.currency_code),
    )
    diff = summary.difference
    diff_color = "#2e7d32" if diff >= 0 else "#c62828"
    diff_col.markdown(
        "<div style='font-size:0.9rem;color:#98a2b3'>"
        "Différence</div>"
        f"<div style='font-size:1.35rem;font-weight:600;"
        f"color:{diff_color}'>"
        f"{_format_currency(diff, summary.currency_code)}</div>",
        unsafe_allow_html=True,
    )


def _render_cashflow_details(view: CashflowView) -> None:
    """Render cashflow incoming and outgoing tables."""
    incoming_data = [
        {
            "Compte": item.account_full_name,
            "Montant": _format_currency(
                item.amount,
                view.summary.currency_code,
            ),
        }
        for item in view.incoming
    ]
    outgoing_data = [
        {
            "Compte": item.account_full_name,
            "Montant": _format_currency(
                item.amount,
                view.summary.currency_code,
            ),
        }
        for item in view.outgoing
    ]
    incoming_col, outgoing_col = st.columns(2)
    with incoming_col:
        st.markdown("#### Entrants")
        if incoming_data:
            st.dataframe(
                incoming_data,
                width="stretch",
                hide_index=True,
                height=360,
            )
        else:
            st.caption("Aucun flux entrant sur la période.")
    with outgoing_col:
        st.markdown("#### Sortants")
        if outgoing_data:
            st.dataframe(
                outgoing_data,
                width="stretch",
                hide_index=True,
                height=360,
            )
        else:
            st.caption("Aucun flux sortant sur la période.")


def _render_accounts(accounts: Sequence[AccountDTO]) -> None:
    """Render the accounts table with light filtering."""
    st.subheader("Accounts")
    query = st.text_input("Search by name", placeholder="Type to filter")
    account_types = sorted({acc.account_type for acc in accounts})
    account_type_filter = st.selectbox(
        "Filter by type",
        options=["All"] + account_types,
        index=0,
    )

    filtered = []
    query_lower = query.strip().lower()
    for acc in accounts:
        if (account_type_filter != "All"
                and acc.account_type != account_type_filter):
            continue
        if query_lower and query_lower not in acc.name.lower():
            continue
        filtered.append(acc)

    st.caption(f"{len(filtered)} accounts shown")
    name_by_guid = {acc.guid: acc.name for acc in accounts}
    data = [
        {
            "Name": acc.name,
            "Type": acc.account_type,
            "Parent": name_by_guid.get(acc.parent_guid, "—")
            if acc.parent_guid
            else "—",
        }
        for acc in filtered
    ]
    st.dataframe(data, width="stretch", hide_index=True, height=420)


def _render_account_tree(
    accounts: Sequence[AccountBalanceDTO],
    currency_code: str,
) -> None:
    """Render account balances in a tree with expandable nodes."""
    st.subheader("Account Tree")
    if not accounts:
        st.info("No account balances available yet.")
        return
    accounts_by_guid = {account.guid: account for account in accounts}
    children_by_parent: dict[str | None, list[AccountBalanceDTO]] = {}
    for account in accounts:
        children_by_parent.setdefault(account.parent_guid, []).append(account)
    for children in children_by_parent.values():
        children.sort(key=lambda item: (item.name.lower(), item.guid))

    roots = list(children_by_parent.get(None, []))
    orphaned = [
        account
        for account in accounts
        if account.parent_guid not in accounts_by_guid
        and account.parent_guid is not None
    ]
    roots.extend(orphaned)
    roots.sort(key=lambda item: (item.name.lower(), item.guid))

    def compute_total(node: AccountBalanceDTO) -> Decimal:
        total = node.balance or Decimal("0")
        for child in children_by_parent.get(node.guid, []):
            total += compute_total(child)
        return total

    def render_node(node: AccountBalanceDTO, depth: int) -> None:
        total = compute_total(node)
        label = (
            f"{node.name} • "
            f"{_format_optional_currency(total, currency_code)}"
        )
        children = children_by_parent.get(node.guid, [])
        if not children:
            st.write(
                f"{'  ' * depth}{node.name} — "
                f"{_format_optional_currency(node.balance, currency_code)}"
            )
            return
        with st.expander(label, expanded=False):
            if node.balance is not None:
                st.caption(
                    "Own balance: "
                    f"{_format_optional_currency(node.balance, currency_code)}"
                )
            for child in children:
                render_node(child, depth + 1)

    for root in roots:
        render_node(root, 0)


def _render_asset_category_chart(
    breakdown: AssetCategoryBreakdown,
    title: str,
    max_categories: int = 6,
    chart_size: int | str | None = 300,
    row_height: int = 38,
    min_height: int = 220,
    height: int | None = None,
    enable_selection: bool = False,
    selection: object | None = None,
    filter_selection: bool = False,
    dim_by_selection: bool = False,
    show_legend: bool = False,
    legend_columns: int = 3,
    palette: Sequence[str] | None = None,
) -> None:
    """Render a horizontal bar chart of asset amounts by category.

    Args:
        breakdown: Aggregated asset totals by category.
        title: Chart title to display above the chart.
        max_categories: Maximum categories before grouping into Other.
        chart_size: Width for the chart canvas.
        row_height: Height in pixels per category row.
        min_height: Minimum chart height in pixels.
        height: Optional explicit chart height override.
        enable_selection: Whether clicking highlights one category.
        selection: Optional Altair selection to reuse across charts.
        filter_selection: Whether to filter this chart by selection.
        dim_by_selection: Whether to dim non-selected categories.
        show_legend: Whether to display the legend.
        legend_columns: Column count when legend is shown.
        palette: Optional color palette override.
    """
    chart = _build_asset_category_chart(
        breakdown=breakdown,
        title=title,
        max_categories=max_categories,
        chart_size=chart_size,
        row_height=row_height,
        min_height=min_height,
        height=height,
        enable_selection=enable_selection,
        selection=selection,
        filter_selection=filter_selection,
        dim_by_selection=dim_by_selection,
        show_legend=show_legend,
        legend_columns=legend_columns,
        palette=palette,
    )
    st.altair_chart(chart, width="stretch")


def _build_asset_category_chart(
    breakdown: AssetCategoryBreakdown,
    title: str,
    max_categories: int,
    chart_size: int | str | None,
    row_height: int,
    min_height: int,
    height: int | None,
    enable_selection: bool,
    selection: object | None,
    filter_selection: bool,
    dim_by_selection: bool,
    show_legend: bool,
    legend_columns: int,
    palette: Sequence[str] | None,
    attach_selection: bool = True,
) -> alt.Chart:
    """Build a horizontal bar chart of asset amounts by category.

    Args:
        breakdown: Aggregated asset totals by category.
        title: Chart title to display above the chart.
        max_categories: Maximum categories before grouping into Other.
        chart_size: Width for the chart canvas.
        row_height: Height in pixels per category row.
        min_height: Minimum chart height in pixels.
        height: Optional explicit chart height override.
        enable_selection: Whether clicking highlights one category.
        selection: Optional Altair selection to reuse across charts.
        filter_selection: Whether to filter this chart by selection.
        dim_by_selection: Whether to dim non-selected categories.
        show_legend: Whether to display the legend.
        legend_columns: Column count when legend is shown.
        palette: Optional color palette override.
        attach_selection: Whether to register the selection on the chart.

    Returns:
        Altair chart object ready to render.
    """
    if not breakdown.categories:
        return alt.Chart(alt.Data(values=[])).mark_text(
            text="No asset amounts available for the chart."
        )
    data, total_amount = _prepare_bar_chart_data(
        breakdown,
        max_categories=max_categories,
    )
    _ = total_amount

    palette_scale = list(
        palette
        or [
            "#1b9aaa",
            "#2e7d32",
            "#f4a261",
            "#e76f51",
            "#457b9d",
            "#f6c453",
            "#6c8ead",
            "#a0c4ff",
        ]
    )
    legend = (
        alt.Legend(
            orient="bottom",
            title=None,
            direction="horizontal",
            columns=legend_columns,
            labelLimit=180,
        )
        if show_legend
        else None
    )

    bar_height = height or max(min_height, len(data) * row_height)
    base = alt.Chart(alt.Data(values=data)).mark_bar(
        cornerRadiusEnd=4
    ).encode(
        x=alt.X(
            "amount:Q",
            axis=alt.Axis(
                title=None,
                grid=True,
                labelColor="#e7ecf3",
                tickColor="#2b313d",
                gridColor="#212631",
            ),
        ),
        y=alt.Y(
            "label:N",
            sort=alt.SortField(field="amount", order="descending"),
            axis=alt.Axis(
                title=None,
                labelColor="#e7ecf3",
                tickColor="#2b313d",
            ),
        ),
        color=alt.Color(
            "label:N",
            scale=alt.Scale(range=palette_scale),
            legend=legend,
        ),
        detail=alt.Detail("parent_label:N"),
        opacity=(
            alt.condition(
                selection,
                alt.value(1.0),
                alt.value(0.25),
            )
            if (enable_selection or dim_by_selection) and selection is not None
            else alt.value(1.0)
        ),
        tooltip=[
            alt.Tooltip("label:N"),
            alt.Tooltip("amount_label:N"),
            alt.Tooltip("share_label:N"),
        ],
    )

    value_text = alt.Chart(alt.Data(values=data)).mark_text(
        align="left",
        baseline="middle",
        dx=8,
        color="#f5f7ff",
        fontSize=12,
        fontWeight="bold",
    ).encode(
        x="amount:Q",
        y=alt.Y(
            "label:N",
            sort=alt.SortField(field="amount", order="descending"),
        ),
        text=alt.Text("amount_label:N"),
    )

    percent_text = alt.Chart(alt.Data(values=data)).mark_text(
        align="left",
        baseline="middle",
        dx=8,
        dy=14,
        color="#b9c1d1",
        fontSize=11,
    ).encode(
        x="amount:Q",
        y=alt.Y(
            "label:N",
            sort=alt.SortField(field="amount", order="descending"),
        ),
        text=alt.Text("share_label:N"),
    )

    if filter_selection and selection is not None:
        base = base.transform_filter(selection)
        value_text = value_text.transform_filter(selection)
        percent_text = percent_text.transform_filter(selection)

    chart = alt.layer(base, value_text, percent_text)
    if chart_size is not None:
        chart = chart.properties(width=chart_size)
    chart = chart.properties(
        height=bar_height,
        title=alt.TitleParams(
            text=title,
            anchor="start",
            color="#f5f7ff",
            fontSize=18,
            fontWeight="bold",
            offset=8,
        ),
    )
    if (
        attach_selection
        and selection is not None
        and (enable_selection or filter_selection or dim_by_selection)
    ):
        chart = chart.add_params(selection)
    return chart


def _prepare_bar_chart_data(
    breakdown: AssetCategoryBreakdown,
    max_categories: int = 6,
) -> tuple[list[dict[str, str | float]], Decimal]:
    """Prepare bar chart data with a Top-N + Other grouping.

    Args:
        breakdown: Aggregated asset totals by category.
        max_categories: Maximum categories to keep before grouping into Other.

    Returns:
        Tuple with Altair-ready chart data and the total amount.
    """
    sorted_items = sorted(
        breakdown.categories,
        key=lambda item: item.amount,
        reverse=True,
    )
    top_items = sorted_items[:max_categories]
    other_items = sorted_items[max_categories:]
    other_amount = sum(
        (item.amount for item in other_items),
        start=Decimal("0"),
    )
    if other_items and other_amount != 0:
        top_items = [
            *top_items,
            type(other_items[0])(
                category="Other",
                amount=other_amount,
                parent_category=None,
            ),
        ]
    total_amount = sum(
        (item.amount for item in sorted_items),
        start=Decimal("0"),
    )
    data: list[dict[str, str | float]] = []
    for item in top_items:
        share = (
            (item.amount / total_amount) * Decimal("100")
            if total_amount
            else Decimal("0")
        )
        data.append(
            {
                "label": item.category,
                "parent_label": getattr(
                    item,
                    "parent_category",
                    None,
                ) or item.category,
                "amount": float(item.amount),
                "amount_label": _format_currency(
                    item.amount,
                    breakdown.currency_code,
                ),
                "share_label": f"{share:.1f}%",
            }
        )
    return data, total_amount


def main() -> None:
    """Render the Streamlit app."""
    st.set_page_config(page_title="GnuCash Dashboard", layout="wide")
    st.title("GnuCash Dashboard")

    page = st.sidebar.radio(
        "Page",
        ["Dashboard", "Accounts", "Flux de trésorerie", "Budget"],
    )

    if page == "Dashboard":
        today = date.today()
        start_date, end_date = _get_date_inputs(today, key_prefix="dashboard")
        baseline_end = start_date - timedelta(days=1)

        summary = _load_net_worth_summary(None, end_date, schema_version=2)
        currency_code = getattr(summary, "currency_code", "EUR")
        baseline_summary = (
            _load_net_worth_summary(None, baseline_end, schema_version=2)
            if baseline_end
            else _zero_summary(currency_code)
        )

        asset_delta = summary.asset_total - baseline_summary.asset_total
        liability_delta = (
            summary.liability_total - baseline_summary.liability_total
        )
        net_worth_delta = summary.net_worth - baseline_summary.net_worth

        asset_delta_display = _format_delta_with_percent(
            asset_delta,
            baseline_summary.asset_total,
        )
        liability_delta_display = _format_delta_with_percent(
            liability_delta,
            baseline_summary.liability_total,
        )
        net_worth_delta_display = _format_delta_with_percent(
            net_worth_delta,
            baseline_summary.net_worth,
        )

        assets_col, liabilities_col, net_worth_col = st.columns(3)
        assets_col.metric(
            "Assets",
            _format_currency(summary.asset_total, currency_code),
            asset_delta_display,
        )
        liabilities_col.metric(
            "Liabilities",
            _format_currency(summary.liability_total, currency_code),
            liability_delta_display,
            delta_color="inverse",
        )
        net_worth_col.metric(
            "Net Worth",
            _format_currency(summary.net_worth, currency_code),
            net_worth_delta_display,
        )
        breakdown_level_1 = _load_asset_category_breakdown(
            end_date,
            level=1,
            schema_version=2,
        )
        breakdown_level_2 = _load_asset_category_breakdown(
            end_date,
            level=2,
            schema_version=2,
        )
        deps_ok, deps_error = _check_altair_dependencies()
        if not deps_ok:
            logger = get_app_logger()
            logger.warning(
                "Altair dependency check failed: %s",
                deps_error or "unknown error",
            )
            st.error(
                "Charts are unavailable because NumPy/Pandas failed to "
                "import. Reinstall dependencies and restart Streamlit."
            )
            return
        category_selection = alt.selection_point(
            name="category_selection",
            fields=["parent_label"],
            on="click",
            clear="dblclick",
            empty="all",
        )
        left_chart = _build_asset_category_chart(
            breakdown=breakdown_level_1,
            title="Assets by Category (€)",
            max_categories=5,
            chart_size=None,
            row_height=38,
            min_height=220,
            height=500,
            enable_selection=True,
            selection=category_selection,
            filter_selection=False,
            dim_by_selection=False,
            show_legend=False,
            legend_columns=2,
            palette=None,
        )
        right_chart = _build_asset_category_chart(
            breakdown=breakdown_level_2,
            title="Assets by Subcategory (€)",
            max_categories=10,
            chart_size=None,
            row_height=38,
            min_height=220,
            height=500,
            enable_selection=False,
            selection=category_selection,
            filter_selection=False,
            dim_by_selection=True,
            show_legend=False,
            legend_columns=3,
            palette=None,
            attach_selection=False,
        )
        combined = alt.hconcat(left_chart, right_chart, spacing=16).properties(
            title=alt.TitleParams(text="")
        ).configure_view(
            stroke=None
        ).configure_legend(
            labelColor="#e7ecf3"
        )
        st.altair_chart(combined, width="stretch")
        account_balances = _load_account_balances(
            end_date=end_date,
            target_currency=currency_code,
            schema_version=2,
        )
        _render_account_tree(account_balances, currency_code)
    elif page == "Accounts":
        accounts = _load_accounts()
        st.caption(f"{len(accounts)} accounts synced "
                   f"from analytics.accounts_dim")
        if not accounts:
            st.warning("No accounts found. Run the sync first.")
            return
        _render_accounts(accounts)
    elif page == "Flux de trésorerie":
        today = date.today()
        start_date, end_date = _get_date_inputs(today, key_prefix="cashflow")
        view = _load_cashflow_view(
            start_date,
            end_date,
            schema_version=1,
        )
        st.subheader("Synthèse")
        _render_cashflow_summary(view)
        st.subheader("Cashflow Sankey")
        show_sankey = st.toggle(
            "Afficher la visualisation Sankey (peut ralentir si très dense)",
            value=False,
            key="cashflow_show_sankey",
        )
        if show_sankey:
            state_key = "cashflow_sankey_state"
            if state_key not in st.session_state:
                st.session_state[state_key] = SankeyState()
            sankey_state: SankeyState = st.session_state[state_key]

            controls = st.columns([1, 1, 2])
            with controls[0]:
                if st.button("Reset tout", key="cashflow_sankey_reset_all"):
                    sankey_state.reset_all()
                    st.rerun()
            with controls[1]:
                if st.button(
                    "Reset branche",
                    key="cashflow_sankey_reset_branch",
                    disabled=not (
                        sankey_state.last_clicked_side
                        and sankey_state.last_clicked_root
                    ),
                ):
                    sankey_state.reset_last_branch()
                    st.rerun()
            with controls[2]:
                sankey_state.allow_negative_diff = st.toggle(
                    "Afficher le déficit si la différence est négative",
                    value=sankey_state.allow_negative_diff,
                    key="cashflow_sankey_allow_negative",
                )
            if (
                view.summary.difference < 0
                and not sankey_state.allow_negative_diff
            ):
                st.warning(
                    "La différence est négative sur la période, mais le nœud "
                    "« Déficit » est désactivé."
                )

            open_left = ", ".join(
                f"{root} (niveau {depth})"
                for root, depth in sorted(sankey_state.left_focus.items())
            )
            open_right = ", ".join(
                f"{root} (niveau {depth})"
                for root, depth in sorted(sankey_state.right_focus.items())
            )
            if open_left or open_right:
                st.caption(
                    "Entrées ouvertes: "
                    f"{open_left or '—'} · Sorties ouvertes: {open_right or '—'}"
                )

            model = build_sankey_model(view, sankey_state)
            fig = build_plotly_figure(model)

            enable_drilldown = st.toggle(
                "Activer le drill-down au clic (peut ralentir)",
                value=True,
                key="cashflow_sankey_enable_drilldown",
            )
            if not enable_drilldown:
                st.plotly_chart(fig, use_container_width=True)
            else:
                try:
                    from streamlit_plotly_events import plotly_events
                except ImportError:  # pragma: no cover
                    st.error(
                        "Le module 'streamlit-plotly-events' est requis pour "
                        "le drill-down. Exécuter: uv sync"
                    )
                    plotly_events = None

                if plotly_events is not None:
                    events = plotly_events(
                        fig,
                        click_event=True,
                        hover_event=False,
                        select_event=False,
                        key="cashflow_sankey_events",
                    )

                    node_index: int | None = None
                    if events:
                        point = events[0] or {}
                        candidate = point.get(
                            "pointNumber",
                            point.get("pointIndex"),
                        )
                        if isinstance(candidate, int):
                            node_index = candidate
                        elif (
                            isinstance(candidate, (list, tuple))
                            and candidate
                            and isinstance(candidate[0], int)
                        ):
                            node_index = candidate[0]

                    if node_index is not None:
                        changed = apply_click(
                            state=sankey_state,
                            model=model,
                            node_index=node_index,
                        )
                        if changed:
                            st.rerun()
        st.subheader("Détails")
        _render_cashflow_details(view)
    else:
        st.subheader("Budget")
        st.info("Budget view coming soon.")


if __name__ == "__main__":  # pragma: no cover
    main()
