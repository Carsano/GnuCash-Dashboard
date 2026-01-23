"""Accounts page renderer for the Streamlit dashboard."""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

from src.application.use_cases.get_accounts import AccountDTO
from src.adapters.interface.streamlit.shared import load_accounts


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

    filtered: list[AccountDTO] = []
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
    st.dataframe(data, width="stretch", hide_index=True, height=420)


def render_accounts_page(*, analytics_schema_version: int) -> None:
    """Render the Accounts page.

    Args:
        analytics_schema_version: Cache-buster that increments after a sync.
    """
    accounts = load_accounts(schema_version=analytics_schema_version)
    st.caption(f"{len(accounts)} accounts synced from analytics.accounts_dim")
    if not accounts:
        st.warning("No accounts found. Run the sync first.")
        return
    _render_accounts(accounts)
