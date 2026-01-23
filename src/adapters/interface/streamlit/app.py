"""Streamlit dashboard entry point.

The Streamlit adapter is intentionally thin: `app.py` wires navigation and
delegates each screen to a dedicated page module.
"""

from __future__ import annotations

import streamlit as st

from src.adapters.interface.streamlit.page_renderers.accounts import (
    render_accounts_page,
)
from src.adapters.interface.streamlit.page_renderers.budget import (
    render_budget_page,
)
from src.adapters.interface.streamlit.page_renderers.cashflow import (
    render_cashflow_page,
)
from src.adapters.interface.streamlit.page_renderers.dashboard import (
    render_dashboard_page,
)
from src.adapters.interface.streamlit.page_renderers.diagnostics import (
    render_diagnostics_page,
)


def main() -> None:
    """Render the Streamlit app."""
    st.set_page_config(page_title="GnuCash Dashboard", layout="wide")
    st.title("GnuCash Dashboard")

    if "analytics_schema_version" not in st.session_state:
        st.session_state["analytics_schema_version"] = 1
    analytics_schema_version = int(st.session_state["analytics_schema_version"])

    page = st.sidebar.radio(
        "Page",
        ["Dashboard", "Accounts", "Flux de trésorerie", "Budget", "Diagnostics"],
    )

    if page == "Dashboard":
        render_dashboard_page(analytics_schema_version=analytics_schema_version)
    elif page == "Accounts":
        render_accounts_page(analytics_schema_version=analytics_schema_version)
    elif page == "Flux de trésorerie":
        render_cashflow_page(analytics_schema_version=analytics_schema_version)
    elif page == "Budget":
        render_budget_page(analytics_schema_version=analytics_schema_version)
    else:
        render_diagnostics_page(analytics_schema_version=analytics_schema_version)


if __name__ == "__main__":  # pragma: no cover
    main()
