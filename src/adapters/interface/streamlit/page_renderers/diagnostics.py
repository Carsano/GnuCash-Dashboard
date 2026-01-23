"""Diagnostics page for the Streamlit dashboard."""

from __future__ import annotations

import os

import streamlit as st
from sqlalchemy import text

from src.infrastructure.container import build_database_adapter
from src.infrastructure.logging.logger import get_app_logger


_EXPECTED_ANALYTICS_VIEWS = (
    "vw_currency_lookup",
    "vw_net_worth_balances",
    "vw_asset_category_balances",
    "vw_latest_prices",
)


def _safe_env_present(name: str) -> bool:
    """Return True when env var exists and is non-empty."""
    value = os.getenv(name)
    return bool(value and value.strip())


def render_diagnostics_page(*, analytics_schema_version: int) -> None:
    """Render the diagnostics page.

    Args:
        analytics_schema_version: Cache-buster that increments after a sync.
    """
    _ = analytics_schema_version
    logger = get_app_logger()

    st.subheader("Diagnostics")

    read_mode = os.getenv("ANALYTICS_READ_MODE", "tables").strip().lower()
    st.markdown(f"**ANALYTICS_READ_MODE**: `{read_mode}`")

    st.markdown("#### Environment")
    env_rows = [
        {"Variable": "ANALYTICS_DB_URL", "Present": _safe_env_present("ANALYTICS_DB_URL")},
        {"Variable": "GNUCASH_DB_URL", "Present": _safe_env_present("GNUCASH_DB_URL")},
    ]
    st.dataframe(env_rows, width="stretch", hide_index=True)

    st.markdown("#### Analytics DB connectivity")
    try:
        engine = build_database_adapter().get_analytics_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
        st.success("Analytics DB connection OK.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Analytics DB connectivity check failed: %s", exc)
        st.error(f"Analytics DB connection failed: {type(exc).__name__}: {exc}")
        return

    if read_mode != "views":
        st.caption("Mode is not `views`, skipping expected view checks.")
        return

    st.markdown("#### Expected analytics views")
    rows: list[dict[str, object]] = []
    try:
        with engine.connect() as conn:
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
                rows.append({"View": view_name, "Present": bool(exists)})
    except Exception as exc:  # noqa: BLE001
        logger.warning("View presence check failed: %s", exc)
        st.error(f"Failed to check views: {type(exc).__name__}: {exc}")
        return

    st.dataframe(rows, width="stretch", hide_index=True)
    missing = [row["View"] for row in rows if not row["Present"]]
    if missing:
        st.warning(
            "Missing views for `ANALYTICS_READ_MODE=views`: "
            + ", ".join(str(name) for name in missing)
        )

