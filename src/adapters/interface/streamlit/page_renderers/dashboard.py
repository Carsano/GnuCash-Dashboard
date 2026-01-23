"""Dashboard page renderer for the Streamlit dashboard."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

import altair as alt
import streamlit as st

from src.adapters.interface.streamlit.shared import (
    format_currency,
    format_delta_with_percent,
    format_optional_currency,
    get_date_inputs,
    invalidate_streamlit_caches,
    load_account_balances,
    load_asset_category_breakdown,
    load_net_worth_summary,
    sync_gnucash_analytics,
)
from src.application.use_cases.get_account_balances import AccountBalanceDTO
from src.application.use_cases.get_asset_category_breakdown import AssetCategoryBreakdown
from src.application.use_cases.get_net_worth_summary import NetWorthSummary
from src.infrastructure.logging.logger import get_app_logger


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


def _zero_summary(currency_code: str) -> NetWorthSummary:
    """Return a zeroed net worth summary."""
    return NetWorthSummary(
        asset_total=Decimal("0"),
        liability_total=Decimal("0"),
        net_worth=Decimal("0"),
        currency_code=currency_code,
    )


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
        label = f"{node.name} • {format_optional_currency(total, currency_code)}"
        children = children_by_parent.get(node.guid, [])
        if not children:
            st.write(
                f"{'  ' * depth}{node.name} — "
                f"{format_optional_currency(node.balance, currency_code)}"
            )
            return
        with st.expander(label, expanded=False):
            if node.balance is not None:
                st.caption(
                    "Own balance: "
                    f"{format_optional_currency(node.balance, currency_code)}"
                )
            for child in children:
                render_node(child, depth + 1)

    for root in roots:
        render_node(root, 0)


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
    data, total_amount = _prepare_bar_chart_data(breakdown, max_categories=max_categories)
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
    base = alt.Chart(alt.Data(values=data)).mark_bar(cornerRadiusEnd=4).encode(
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
            alt.condition(selection, alt.value(1.0), alt.value(0.25))
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
        y=alt.Y("label:N", sort=alt.SortField(field="amount", order="descending")),
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
        y=alt.Y("label:N", sort=alt.SortField(field="amount", order="descending")),
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
    sorted_items = sorted(breakdown.categories, key=lambda item: item.amount, reverse=True)
    top_items = sorted_items[:max_categories]
    other_items = sorted_items[max_categories:]
    other_amount = sum((item.amount for item in other_items), start=Decimal("0"))
    if other_items and other_amount != 0:
        top_items = [
            *top_items,
            type(other_items[0])(
                category="Other",
                amount=other_amount,
                parent_category=None,
            ),
        ]
    total_amount = sum((item.amount for item in sorted_items), start=Decimal("0"))
    data: list[dict[str, str | float]] = []
    for item in top_items:
        share = (item.amount / total_amount) * Decimal("100") if total_amount else Decimal("0")
        data.append(
            {
                "label": item.category,
                "parent_label": getattr(item, "parent_category", None) or item.category,
                "amount": float(item.amount),
                "amount_label": format_currency(item.amount, breakdown.currency_code),
                "share_label": f"{share:.1f}%",
            }
        )
    return data, total_amount


def render_dashboard_page(*, analytics_schema_version: int) -> None:
    """Render the dashboard page.

    Args:
        analytics_schema_version: Cache-buster that increments after a sync.
    """
    action_col, _ = st.columns([1, 3])
    with action_col:
        if st.button(
            "Mettre à jour la base analytics",
            help=(
                "Synchronise les tables GnuCash vers la base analytics "
                "puis invalide les caches Streamlit."
            ),
            type="primary",
        ):
            with st.spinner("Synchronisation analytics en cours…"):
                result = sync_gnucash_analytics()
            st.session_state["analytics_schema_version"] = analytics_schema_version + 1
            invalidate_streamlit_caches()
            st.success(
                "Analytics mise à jour "
                f"(accounts={result.accounts_count}, "
                f"commodities={result.commodities_count}, "
                f"splits={result.splits_count}, "
                f"transactions={result.transactions_count}, "
                f"prices={result.prices_count})."
            )
            st.rerun()

    today = date.today()
    start_date, end_date = get_date_inputs(today, key_prefix="dashboard")
    baseline_end = start_date - timedelta(days=1)

    summary = load_net_worth_summary(None, end_date, schema_version=analytics_schema_version)
    currency_code = getattr(summary, "currency_code", "EUR")
    baseline_summary = (
        load_net_worth_summary(None, baseline_end, schema_version=analytics_schema_version)
        if baseline_end
        else _zero_summary(currency_code)
    )

    asset_delta_display = format_delta_with_percent(
        summary.asset_total - baseline_summary.asset_total,
        baseline_summary.asset_total,
    )
    liability_delta_display = format_delta_with_percent(
        summary.liability_total - baseline_summary.liability_total,
        baseline_summary.liability_total,
    )
    net_worth_delta_display = format_delta_with_percent(
        summary.net_worth - baseline_summary.net_worth,
        baseline_summary.net_worth,
    )

    assets_col, liabilities_col, net_worth_col = st.columns(3)
    assets_col.metric(
        "Assets",
        format_currency(summary.asset_total, currency_code),
        asset_delta_display,
    )
    liabilities_col.metric(
        "Liabilities",
        format_currency(summary.liability_total, currency_code),
        liability_delta_display,
        delta_color="inverse",
    )
    net_worth_col.metric(
        "Net Worth",
        format_currency(summary.net_worth, currency_code),
        net_worth_delta_display,
    )

    breakdown_level_1 = load_asset_category_breakdown(
        end_date, level=1, schema_version=analytics_schema_version
    )
    breakdown_level_2 = load_asset_category_breakdown(
        end_date, level=2, schema_version=analytics_schema_version
    )
    deps_ok, deps_error = _check_altair_dependencies()
    if not deps_ok:
        logger = get_app_logger()
        logger.warning("Altair dependency check failed: %s", deps_error or "unknown error")
        st.error(
            "Charts are unavailable because NumPy/Pandas failed to import. "
            "Reinstall dependencies and restart Streamlit."
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
    combined = (
        alt.hconcat(left_chart, right_chart, spacing=16)
        .properties(title=alt.TitleParams(text=""))
        .configure_view(stroke=None)
        .configure_legend(labelColor="#e7ecf3")
    )
    st.altair_chart(combined, width="stretch")

    account_balances = load_account_balances(
        end_date=end_date,
        target_currency=currency_code,
        schema_version=analytics_schema_version,
    )
    _render_account_tree(account_balances, currency_code)
