"""Streamlit dashboard entry point."""

from collections import Counter
from collections.abc import Sequence

import streamlit as st

from src.application.use_cases.get_accounts import (
    AccountDTO,
    GetAccountsUseCase,
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

def _apply_theme() -> None:
    """Inject CSS theme for the dashboard."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=IBM+Plex+Serif:wght@400;600&display=swap');

        :root {
            --bg-start: #f7efe5;
            --bg-end: #e6f0ee;
            --ink: #1f1f22;
            --muted: #6b6e76;
            --accent: #cc7a2f;
            --accent-2: #2f7f6c;
            --panel: rgba(255, 255, 255, 0.7);
        }

        .stApp {
            background: radial-gradient(circle at 15% 15%, #fff5e8 0%, transparent 35%),
                        radial-gradient(circle at 85% 10%, #e1f5f1 0%, transparent 30%),
                        linear-gradient(145deg, var(--bg-start), var(--bg-end));
            color: var(--ink);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            animation: fade-in 0.6s ease-out;
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", "Avenir Next", "Trebuchet MS", sans-serif;
            letter-spacing: -0.01em;
        }

        p, div, span, label, input {
            font-family: "IBM Plex Serif", "Georgia", serif;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1.5rem;
            border-radius: 18px;
            background: var(--panel);
            box-shadow: 0 12px 30px rgba(31, 31, 34, 0.08);
            backdrop-filter: blur(8px);
            margin-bottom: 1.5rem;
        }

        .brand {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }

        .brand-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--ink);
        }

        .brand-subtitle {
            font-size: 0.9rem;
            color: var(--muted);
        }

        .pill {
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: rgba(204, 122, 47, 0.15);
            color: var(--accent);
            font-weight: 600;
            font-size: 0.85rem;
        }

        .stTabs [data-baseweb="tab"] {
            font-family: "Space Grotesk", "Avenir Next", "Trebuchet MS", sans-serif;
            font-size: 0.95rem;
            padding: 0.5rem 1rem;
            border-radius: 999px;
            background: transparent;
        }

        .stTabs [aria-selected="true"] {
            background: rgba(47, 127, 108, 0.18);
            color: var(--accent-2);
        }

        .metric-card {
            padding: 1rem;
            border-radius: 16px;
            background: var(--panel);
            box-shadow: 0 10px 24px rgba(31, 31, 34, 0.06);
        }

        @keyframes fade-in {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 640px) {
            .topbar {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.6rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_overview(accounts: Sequence[AccountDTO]) -> None:
    """Render the overview tab content."""
    type_counts = Counter(acc.account_type for acc in accounts)
    total_accounts = len(accounts)
    unique_types = len(type_counts)

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Portfolio Snapshot")
        st.write(
            "Highlights from your analytics snapshot. The sync pulls accounts "
            "from GnuCash and cleans technical identifiers."
        )
        metric_left, metric_right = st.columns(2)
        with metric_left:
            st.markdown(
                f"<div class='metric-card'><h3>{total_accounts}</h3>"
                "<p>Total accounts</p></div>",
                unsafe_allow_html=True,
            )
        with metric_right:
            st.markdown(
                f"<div class='metric-card'><h3>{unique_types}</h3>"
                "<p>Account types</p></div>",
                unsafe_allow_html=True,
            )
    with right:
        st.subheader("Account Types")
        if type_counts:
            st.bar_chart(type_counts, height=220)
        else:
            st.info("No account types available yet.")


def _render_accounts(accounts: Sequence[AccountDTO]) -> None:
    """Render the accounts table with light filtering."""
    st.subheader("Accounts Directory")
    query = st.text_input("Search by name or guid", placeholder="Type to filter")
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
        if query_lower and query_lower not in acc.name.lower() and query_lower not in acc.guid.lower():
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


def _render_health(accounts: Sequence[AccountDTO]) -> None:
    """Render basic health and sync hints."""
    st.subheader("Data Health")
    if not accounts:
        st.warning("No accounts detected. Run the sync to populate analytics.")
        return

    missing_parent = sum(1 for acc in accounts if not acc.parent_guid)
    st.write(
        "Quick checks for completeness and structure of the analytics data."
    )
    st.markdown(
        f"<div class='metric-card'><h3>{missing_parent}</h3>"
        "<p>Accounts without parent</p></div>",
        unsafe_allow_html=True,
    )
    st.info(
        "Tip: Run the sync after changes in GnuCash to keep analytics aligned."
    )


def main() -> None:
    """Render the Streamlit app."""
    st.set_page_config(page_title="GnuCash Dashboard", layout="wide")
    _apply_theme()

    accounts = _load_accounts()
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">
                <div class="brand-title">GnuCash Dashboard</div>
                <div class="brand-subtitle">Analytics & portfolio structure</div>
            </div>
            <div class="pill">Sync ready</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"{len(accounts)} accounts synced from analytics.accounts_dim")

    overview_tab, accounts_tab, health_tab = st.tabs(
        ["Overview", "Accounts", "Health"]
    )
    with overview_tab:
        _render_overview(accounts)
    with accounts_tab:
        _render_accounts(accounts)
    with health_tab:
        _render_health(accounts)


if __name__ == "__main__":  # pragma: no cover
    main()
