"""Streamlit dashboard entry point."""

from collections.abc import Sequence
from decimal import Decimal

import streamlit as st

from src.application.use_cases.get_accounts import (
    AccountDTO,
    GetAccountsUseCase,
)
from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
    NetWorthSummary,
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


def _fetch_net_worth_summary() -> NetWorthSummary:
    """Fetch the net worth summary from the GnuCash database."""
    adapter = SqlAlchemyDatabaseEngineAdapter()
    use_case = GetNetWorthSummaryUseCase(db_port=adapter)
    return use_case.execute()


@st.cache_data(show_spinner=False)
def _load_net_worth_summary() -> NetWorthSummary:
    """Cached wrapper around _fetch_net_worth_summary."""
    return _fetch_net_worth_summary()


def _format_currency(value: Decimal) -> str:
    """Format currency values for display."""
    return f"{value:,.2f}"


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
        if account_type_filter != "All" and acc.account_type != account_type_filter:
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
    st.dataframe(data, use_container_width=True, hide_index=True, height=420)


def main() -> None:
    """Render the Streamlit app."""
    st.set_page_config(page_title="GnuCash Dashboard", layout="wide")
    st.title("GnuCash Dashboard")

    summary = _load_net_worth_summary()
    assets_col, liabilities_col, net_worth_col = st.columns(3)
    assets_col.metric("Assets", _format_currency(summary.asset_total))
    liabilities_col.metric(
        "Liabilities",
        _format_currency(summary.liability_total),
    )
    net_worth_col.metric("Net Worth", _format_currency(summary.net_worth))

    accounts = _load_accounts()
    st.caption(f"{len(accounts)} accounts synced from analytics.accounts_dim")
    if not accounts:
        st.warning("No accounts found. Run the sync first.")
        return
    _render_accounts(accounts)


if __name__ == "__main__":  # pragma: no cover
    main()
