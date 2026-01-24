"""Budget page renderer for the Streamlit dashboard."""

from __future__ import annotations

import streamlit as st


def render_budget_page(*, analytics_schema_version: int) -> None:
    """Render the Budget page.

    Args:
        analytics_schema_version: Cache-buster that increments after a sync.
    """
    _ = analytics_schema_version
    st.subheader("Budget")
    st.info("Budget view coming soon.")
