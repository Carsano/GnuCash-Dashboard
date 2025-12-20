"""Streamlit dashboard entry point."""

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

import streamlit as st
import altair as alt

from src.application.use_cases.get_accounts import (
    AccountDTO,
    GetAccountsUseCase,
)
from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
    NetWorthSummary,
)
from src.application.use_cases.get_asset_category_breakdown import (
    AssetCategoryBreakdown,
    GetAssetCategoryBreakdownUseCase,
)
from src.infrastructure.db import SqlAlchemyDatabaseEngineAdapter


def _fetch_accounts() -> Sequence[AccountDTO]:
    """Fetch accounts using the analytics database."""
    adapter = SqlAlchemyDatabaseEngineAdapter()
    use_case = GetAccountsUseCase(db_port=adapter)
    return use_case.execute()


@st.cache_data(show_spinner=False)
def _load_accounts() -> Sequence[AccountDTO]:
    """Cached wrapper around _fetch_accounts for Streamlit sessions."""
    return _fetch_accounts()


def _fetch_net_worth_summary(
    start_date: date | None,
    end_date: date | None,
) -> NetWorthSummary:
    """Fetch the net worth summary from the GnuCash database."""
    adapter = SqlAlchemyDatabaseEngineAdapter()
    use_case = GetNetWorthSummaryUseCase(db_port=adapter)
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


def _fetch_asset_category_breakdown(
    end_date: date | None,
    level: int,
) -> AssetCategoryBreakdown:
    """Fetch asset category breakdown in EUR."""
    adapter = SqlAlchemyDatabaseEngineAdapter()
    use_case = GetAssetCategoryBreakdownUseCase(db_port=adapter)
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


def _format_currency(value: Decimal, currency_code: str) -> str:
    """Format currency values for display."""
    symbol = "€" if currency_code == "EUR" else currency_code
    return f"{value:,.2f} {symbol}"


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


def _zero_summary(currency_code: str) -> NetWorthSummary:
    """Return a zeroed net worth summary."""
    return NetWorthSummary(
        asset_total=Decimal("0"),
        liability_total=Decimal("0"),
        net_worth=Decimal("0"),
        currency_code=currency_code,
    )


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


def _render_asset_category_chart(
    breakdown: AssetCategoryBreakdown,
    title: str,
    max_categories: int = 6,
    chart_size: int = 300,
    row_height: int = 38,
    min_height: int = 220,
    height: int | None = None,
    enable_selection: bool = False,
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
        show_legend: Whether to display the legend.
        legend_columns: Column count when legend is shown.
        palette: Optional color palette override.
    """
    if not breakdown.categories:
        st.info("No asset amounts available for the chart.")
        return
    data, total_amount = _prepare_donut_chart_data(
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

    select_category = alt.selection_point(
        fields=["category"],
        on="click",
        clear="dblclick",
        empty="none",
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
            "category:N",
            sort=alt.SortField(field="amount", order="descending"),
            axis=alt.Axis(
                title=None,
                labelColor="#e7ecf3",
                tickColor="#2b313d",
            ),
        ),
        color=alt.Color(
            "category:N",
            scale=alt.Scale(range=palette_scale),
            legend=legend,
        ),
        opacity=(
            alt.condition(
                select_category,
                alt.value(1.0),
                alt.value(0.25),
            )
            if enable_selection
            else alt.value(1.0)
        ),
        tooltip=[
            alt.Tooltip("category:N"),
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
            "category:N",
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
            "category:N",
            sort=alt.SortField(field="amount", order="descending"),
        ),
        text=alt.Text("share_label:N"),
    )

    chart = alt.layer(base, value_text, percent_text).properties(
        width=chart_size,
        height=bar_height,
    ).configure_view(
        stroke=None
    ).configure_legend(
        labelColor="#e7ecf3"
    )
    if enable_selection:
        chart = chart.add_params(select_category)
    st.subheader(title)
    st.altair_chart(chart, width='stretch')


def _prepare_donut_chart_data(
    breakdown: AssetCategoryBreakdown,
    max_categories: int = 6,
) -> tuple[list[dict[str, str | float]], Decimal]:
    """Prepare donut chart data with a Top-N + Other grouping.

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
            type(other_items[0])(category="Other", amount=other_amount),
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
                "category": item.category,
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

    page = st.sidebar.selectbox("Page", ["Dashboard", "Accounts"])

    if page == "Dashboard":
        period = st.sidebar.selectbox(
            "Period",
            ["YTD", "MTD", "QTD", "All Time"],
        )
        today = date.today()
        start_date = _get_period_start(period, today)
        baseline_end = start_date - timedelta(days=1) if start_date else None

        summary = _load_net_worth_summary(None, today, schema_version=2)
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
            today,
            level=1,
            schema_version=1,
        )
        breakdown_level_2 = _load_asset_category_breakdown(
            today,
            level=2,
            schema_version=1,
        )
        chart_left, chart_right = st.columns(2)
        with chart_left:
            _render_asset_category_chart(
                breakdown_level_1,
                "Assets by Category (€)",
                max_categories=5,
                chart_size=360,
                height=500,
                enable_selection=True,
                legend_columns=2,
            )
        with chart_right:
            _render_asset_category_chart(
                breakdown_level_2,
                "Assets by Subcategory (€)",
                max_categories=10,
                chart_size=360,
                height=500,
                legend_columns=3,
            )
    else:
        accounts = _load_accounts()
        st.caption(f"{len(accounts)} accounts synced "
                   f"from analytics.accounts_dim")
        if not accounts:
            st.warning("No accounts found. Run the sync first.")
            return
        _render_accounts(accounts)


if __name__ == "__main__":  # pragma: no cover
    main()
