"""Budget page renderer for the Streamlit dashboard."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
import os
from time import perf_counter
import streamlit as st

from src.adapters.interface.streamlit.shared import load_budgets
from src.adapters.interface.streamlit.shared import load_accounts_tree
from src.adapters.interface.streamlit.shared import load_budget_applicability
from src.adapters.interface.streamlit.shared import load_budget_month_view
from src.application.use_cases.build_budget_hierarchy_rows import (
    BudgetHierarchyRow,
    build_budget_hierarchy_rows,
)
from src.application.use_cases.budget_hierarchy_visibility import (
    build_children_map,
)
from src.application.ports.budget_repository import BudgetsUnsupportedBackendError
from src.domain.models.accounts import AccountDTO
from src.domain.models.budget import BudgetInapplicableReason
from src.domain.models.budget import BudgetMonthSummaryDTO


def _today() -> date:
    return date.today()


def _previous_month_start(month_start: date) -> date:
    if month_start.month == 1:
        return date(month_start.year - 1, 12, 1)
    return date(month_start.year, month_start.month - 1, 1)


def _format_vs_last_month_delta(
    delta: Decimal | float | int | None,
) -> str:
    if delta is None:
        return "vs last month: n/a"
    return f"vs last month: {delta:+.2f}"


def _format_context_delta_text(
    *,
    actual_delta: Decimal | float | int | None,
    remaining_over_delta: Decimal | float | int | None,
) -> str:
    if actual_delta is None or remaining_over_delta is None:
        return "vs last month: n/a"
    return (
        "vs last month: "
        f"Actual {actual_delta:+.2f} · "
        f"Remaining/Over {remaining_over_delta:+.2f}"
    )


def _remaining_over_value(summary: BudgetMonthSummaryDTO) -> Decimal:
    return Decimal(summary.total_remaining) - Decimal(summary.total_over)


def _render_month_summary_shell(*, status_label_text: str) -> None:
    st.subheader("Month Summary")
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown("**Total Budget**")
        st.caption("—")
    with kpi_cols[1]:
        st.markdown("**Total Actual**")
        st.caption("—")
    with kpi_cols[2]:
        st.markdown("**Remaining / Over**")
        st.caption("—")
        st.caption("vs last month: —")
    with kpi_cols[3]:
        st.markdown("**Status**")
        st.caption(status_label_text)
        st.caption("Status is a placeholder until budget calculations land.")


def _render_month_summary(
    *,
    summary: BudgetMonthSummaryDTO,
    remaining_over_delta: Decimal | float | int | None,
) -> None:
    st.subheader("Month Summary")
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown("**Total Budget**")
        st.caption(f"{summary.total_budget:,.2f}")
    with kpi_cols[1]:
        st.markdown("**Total Actual**")
        st.caption(f"{summary.total_actual:,.2f}")
    with kpi_cols[2]:
        st.markdown("**Remaining / Over**")
        st.caption(f"{summary.total_remaining:,.2f} / {summary.total_over:,.2f}")
        st.caption(_format_vs_last_month_delta(remaining_over_delta))
    with kpi_cols[3]:
        st.markdown("**Status**")
        st.caption(summary.status_label)


def _render_expense_hierarchy_shell() -> None:
    st.subheader("Expense hierarchy")
    st.caption("Expense hierarchy values land in later stories.")


def _render_expense_hierarchy(
    *,
    rows: tuple[BudgetHierarchyRow, ...],
    mobile_layout_active: bool,
) -> None:
    st.subheader("Expense hierarchy")
    if not rows:
        st.caption("No expense hierarchy nodes available for this context.")
        return
    _inject_mobile_hierarchy_css()
    expand_state_key = "budget_hierarchy_expanded_guids"
    expanded_guids = set(
        st.session_state.get(expand_state_key, set())
    )
    children_by_guid = build_children_map(rows)

    header_cols = st.columns([5, 1.5, 1.5, 2.0, 1.3, 1.0])
    with header_cols[0]:
        st.markdown("**Category**")
    with header_cols[1]:
        st.markdown("**Budget**")
    with header_cols[2]:
        st.markdown("**Actual**")
    with header_cols[3]:
        st.markdown("**Remaining/Over**")
    with header_cols[4]:
        st.markdown("**Status**")
    with header_cols[5]:
        st.markdown("**Progress**")

    ancestor_stack: list[tuple[int, str]] = []
    visible_rows: list[BudgetHierarchyRow] = []
    for row in rows:
        while ancestor_stack and ancestor_stack[-1][0] >= row.depth:
            ancestor_stack.pop()
        is_visible = all(
            parent_guid in expanded_guids for _, parent_guid in ancestor_stack
        )
        ancestor_stack.append((row.depth, row.node_guid))
        if not is_visible:
            continue
        visible_rows.append(row)

    highlight_guids = _select_top_over_highlight_guids(
        visible_rows=tuple(visible_rows),
        cap=5,
    )

    if not mobile_layout_active:
        for row in visible_rows:
            row_cols = st.columns([5, 1.5, 1.5, 2.0, 1.3, 1.0])
            children = children_by_guid.get(row.node_guid, ())
            has_children = bool(children)
            is_highlighted = row.node_guid in highlight_guids

            prefix = ""
            if row.depth > 0:
                prefix = f"{'|  ' * (row.depth - 1)}|- "
            toggle_symbol = " "
            if has_children:
                toggle_symbol = "-" if row.node_guid in expanded_guids else "+"
            with row_cols[0]:
                if has_children:
                    clicked = st.button(
                        f"{toggle_symbol} {prefix}{row.node_name}",
                        key=f"budget_hierarchy_toggle_{row.node_guid}",
                    )
                    if clicked:
                        if row.node_guid in expanded_guids:
                            expanded_guids.remove(row.node_guid)
                        else:
                            expanded_guids.add(row.node_guid)
                        st.session_state[expand_state_key] = expanded_guids
                        if hasattr(st, "rerun"):
                            st.rerun()
                        return
                else:
                    st.markdown(
                        _format_hierarchy_node_label(
                            label=f"{prefix}{row.node_name}",
                            highlighted=is_highlighted,
                        ),
                        unsafe_allow_html=True,
                    )
            with row_cols[1]:
                st.markdown(f"{row.budget:,.2f}")
            with row_cols[2]:
                st.markdown(f"{row.actual:,.2f}")
            with row_cols[3]:
                if row.over > 0:
                    st.markdown(f"Over: {row.over:,.2f}")
                else:
                    st.markdown(f"Remaining: {row.remaining:,.2f}")
            with row_cols[4]:
                st.markdown(
                    _format_status_label(
                        status_label=row.status_label,
                        highlighted=is_highlighted,
                    ),
                    unsafe_allow_html=True,
                )
            with row_cols[5]:
                if row.no_budget or row.budget <= 0:
                    st.markdown("—")
                else:
                    pct = (row.actual / row.budget) * 100
                    st.markdown(f"{pct:.0f}%")

    if mobile_layout_active:
        for row in visible_rows:
            children = children_by_guid.get(row.node_guid, ())
            has_children = bool(children)
            is_highlighted = row.node_guid in highlight_guids
            prefix = ""
            if row.depth > 0:
                prefix = f"{'|  ' * (row.depth - 1)}|- "
            toggle_symbol = " "
            if has_children:
                toggle_symbol = "-" if row.node_guid in expanded_guids else "+"
            if has_children:
                clicked = st.button(
                    f"{toggle_symbol} {prefix}{row.node_name}",
                    key=f"budget_hierarchy_mobile_toggle_{row.node_guid}",
                )
                if clicked:
                    if row.node_guid in expanded_guids:
                        expanded_guids.remove(row.node_guid)
                    else:
                        expanded_guids.add(row.node_guid)
                    st.session_state[expand_state_key] = expanded_guids
                    if hasattr(st, "rerun"):
                        st.rerun()
                    return
            st.markdown(
                _build_mobile_row_card_html(
                    row=row,
                    highlighted=is_highlighted,
                    node_label=f"{prefix}{row.node_name}",
                ),
                unsafe_allow_html=True,
            )

    st.session_state[expand_state_key] = expanded_guids


def _select_top_over_highlight_guids(
    *,
    visible_rows: tuple[BudgetHierarchyRow, ...],
    cap: int = 5,
) -> set[str]:
    eligible_rows = [row for row in visible_rows if row.over > 0]
    eligible_rows.sort(
        key=lambda row: (
            -abs(float(row.over)),
            row.node_path.casefold(),
            row.node_guid,
        )
    )
    return {row.node_guid for row in eligible_rows[:cap]}


def _format_hierarchy_node_label(*, label: str, highlighted: bool) -> str:
    if not highlighted:
        return label
    return (
        "<span style='border:1px solid #3a5270; background:#1b2a3f33; "
        "padding:1px 6px; border-radius:6px;'>"
        f"{label}</span>"
    )


def _format_status_label(*, status_label: str, highlighted: bool) -> str:
    if not highlighted:
        return status_label
    return (
        "<span style='border:1px solid #3a5270; background:#1b2a3f33; "
        "padding:1px 6px; border-radius:6px;'>"
        f"{status_label} · TOP-OVER</span>"
    )


def _build_mobile_row_card_html(
    *,
    row: BudgetHierarchyRow,
    highlighted: bool,
    node_label: str,
) -> str:
    remaining_over_text = (
        f"Over: {row.over:,.2f}"
        if row.over > 0
        else f"Remaining: {row.remaining:,.2f}"
    )
    highlight_class = " budget-mobile-card--highlight" if highlighted else ""
    return (
        f"<div class='budget-mobile-card{highlight_class}'>"
        f"<div class='budget-mobile-card__head'>Category: {node_label}</div>"
        f"<div class='budget-mobile-grid'>"
        f"<div><div class='budget-mobile-label'>Status</div><div class='budget-mobile-value'>{row.status_label}</div></div>"
        f"<div><div class='budget-mobile-label'>Budget</div><div class='budget-mobile-value'>{row.budget:,.2f}</div></div>"
        f"<div><div class='budget-mobile-label'>Actual</div><div class='budget-mobile-value'>{row.actual:,.2f}</div></div>"
        f"<div><div class='budget-mobile-label'>Remaining/Over</div><div class='budget-mobile-value'>{remaining_over_text}</div></div>"
        "</div></div>"
    )


def _inject_mobile_hierarchy_css() -> None:
    css_injected_key = "_budget_mobile_hierarchy_css_injected"
    if bool(st.session_state.get(css_injected_key)):
        return
    st.markdown(
        """
<style>
.block-container {
  overflow-x: hidden;
}
.budget-mobile-card {
  display: none;
  border: 1px solid #2a3a52;
  border-radius: 10px;
  padding: 10px;
  margin: 8px 0;
  background: rgba(17, 24, 36, 0.72);
}
.budget-mobile-card--highlight {
  border-color: #3a5270;
  box-shadow: inset 0 0 0 1px #3a527066;
}
.budget-mobile-card__head {
  font-weight: 600;
  margin-bottom: 8px;
}
.budget-mobile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}
.budget-mobile-label {
  font-size: 0.78rem;
  color: #9fb0c7;
}
.budget-mobile-value {
  font-size: 0.95rem;
}
@media (max-width: 767px) {
  .budget-mobile-card { display: block; }
}
</style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state[css_injected_key] = True


def _is_mobile_layout_active() -> bool:
    context = getattr(st, "context", None)
    headers = getattr(context, "headers", None)
    if headers is None:
        return False
    user_agent = ""
    sec_ch_ua_mobile = ""
    if hasattr(headers, "get"):
        user_agent = str(headers.get("User-Agent") or headers.get("user-agent") or "")
        sec_ch_ua_mobile = str(
            headers.get("sec-ch-ua-mobile")
            or headers.get("Sec-CH-UA-Mobile")
            or ""
        )
    ua = user_agent.lower()
    ua_mobile = (
        "android" in ua
        or "iphone" in ua
        or "ipad" in ua
        or "mobile" in ua
    )
    ch_mobile = sec_ch_ua_mobile.strip() == "?1"
    return ua_mobile or ch_mobile


def _budget_accessibility_css_text() -> str:
    return """
<style>
/* Keyboard-visible focus ring */
button:focus-visible,
[role="button"]:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid #6ea8ff !important;
  outline-offset: 2px !important;
  box-shadow: 0 0 0 2px rgba(110, 168, 255, 0.28) !important;
}

/* Touch target intent (~44px) for core controls */
button[kind],
.stSelectbox [data-baseweb="select"] > div,
.stDateInput [data-baseweb="input"] > div {
  min-height: 44px !important;
}
</style>
    """


def _inject_budget_accessibility_css() -> None:
    css_injected_key = "_budget_accessibility_css_injected"
    if bool(st.session_state.get(css_injected_key)):
        return
    st.markdown(_budget_accessibility_css_text(), unsafe_allow_html=True)
    st.session_state[css_injected_key] = True


def _build_account_full_paths(
    accounts: Sequence[AccountDTO],
) -> dict[str, str]:
    accounts_by_guid = {account.guid: account for account in accounts}
    full_path_by_guid: dict[str, str] = {}

    for account in accounts:
        if account.guid in full_path_by_guid:
            continue
        parts: list[str] = []
        cursor: AccountDTO | None = account
        seen: set[str] = set()
        while cursor is not None and cursor.guid not in seen:
            seen.add(cursor.guid)
            parts.append(cursor.name)
            cursor = (
                accounts_by_guid.get(cursor.parent_guid)
                if cursor.parent_guid
                else None
            )
        full_path_by_guid[account.guid] = ":".join(reversed(parts))
    return full_path_by_guid


def render_budget_page(*, analytics_schema_version: int) -> None:
    """Render the Budget page.

    Args:
        analytics_schema_version: Cache-buster that increments after a sync.
    """
    st.subheader("Budget (Expenses)")
    _inject_budget_accessibility_css()

    backend = os.getenv("GNUCASH_BACKEND", "sqlalchemy").strip().lower()
    selector_disabled = False
    expander_expanded = False
    error_message: str | None = None
    inapplicable_reason: BudgetInapplicableReason | None = None
    month_widget_key = "budget_context_month"
    budget_widget_key = "budget_context_budget_label"
    layout_mode_key = "budget_layout_mode"

    if "selected_month_start" not in st.session_state:
        today = _today()
        st.session_state["selected_month_start"] = date(today.year, today.month, 1)

    try:
        budgets = list(
            load_budgets(
                schema_version=analytics_schema_version,
                backend=backend,
            )
        )
    except BudgetsUnsupportedBackendError as exc:
        budgets = []
        selector_disabled = True
        expander_expanded = True
        error_message = str(exc)
    except RuntimeError as exc:
        budgets = []
        selector_disabled = True
        expander_expanded = True
        message = str(exc)
        if message.startswith("Missing environment variable: "):
            missing_key = message.split(":", 1)[-1].strip()
            error_message = (
                f"Missing configuration: set `{missing_key}` to connect to your GnuCash database."
            )
        else:
            error_message = (
                "Unable to load budgets from the configured backend. "
                "Verify your DB connection and backend configuration."
            )
    except Exception:
        budgets = []
        selector_disabled = True
        expander_expanded = True
        error_message = (
            "Unable to load budgets from the configured backend. "
            "Verify your DB connection and backend configuration."
        )

    if not budgets and not selector_disabled:
        selector_disabled = True
        expander_expanded = True
        error_message = (
            "No budgets found in the configured data source. "
            "Create a budget in GnuCash, then refresh."
        )

    placeholder = "— Select a budget —"
    labels: list[str]
    label_to_guid: dict[str, str] = {}
    label_to_name: dict[str, str] = {}
    if selector_disabled:
        labels = ["—"]
        st.session_state[budget_widget_key] = "—"
        st.session_state.pop("selected_budget_guid", None)
        st.session_state.pop("selected_budget_name", None)
    else:
        # Ensure the widget state is present even on the first render.
        if budget_widget_key not in st.session_state:
            st.session_state[budget_widget_key] = placeholder

        name_counts: dict[str, int] = {}
        for budget in budgets:
            name_counts[budget.name] = name_counts.get(budget.name, 0) + 1

        labels = [placeholder]
        for budget in budgets:
            label = budget.name
            if name_counts.get(budget.name, 0) > 1:
                label = f"{budget.name} ({budget.guid})"
            labels.append(label)
            label_to_guid[label] = budget.guid
            label_to_name[label] = budget.name

        # If a budget was previously selected, align the widget label with the
        # stored GUID so the selection persists across reruns.
        persisted_guid = st.session_state.get("selected_budget_guid")
        current_widget_label = st.session_state.get(budget_widget_key)
        if (
            persisted_guid
            and (not isinstance(current_widget_label, str) or current_widget_label == placeholder)
        ):
            for label, guid in label_to_guid.items():
                if guid == persisted_guid:
                    st.session_state[budget_widget_key] = label
                    break

        # Sanitize the stored label to avoid Streamlit widget state errors.
        selected_label = st.session_state.get(budget_widget_key)
        if not isinstance(selected_label, str) or selected_label not in labels:
            st.session_state[budget_widget_key] = placeholder

    # Resolve month context from a widget-backed key so applicability checks are not stale.
    month_widget_value = st.session_state.get(month_widget_key)
    if not isinstance(month_widget_value, date):
        month_widget_value = st.session_state.get("selected_month_start")
    if not isinstance(month_widget_value, date):
        month_widget_value = date(_today().year, _today().month, 1)
    if month_widget_key not in st.session_state:
        st.session_state[month_widget_key] = month_widget_value
    selected_month_start = date(month_widget_value.year, month_widget_value.month, 1)
    st.session_state["selected_month_start"] = selected_month_start

    # Apply current budget widget state into canonical selection keys (guid/name).
    if not selector_disabled:
        selected_label = st.session_state.get(budget_widget_key, placeholder)
        if selected_label == placeholder:
            st.session_state.pop("selected_budget_guid", None)
            st.session_state.pop("selected_budget_name", None)
        elif isinstance(selected_label, str) and selected_label in label_to_guid:
            st.session_state["selected_budget_guid"] = label_to_guid[selected_label]
            st.session_state["selected_budget_name"] = label_to_name[selected_label]
        else:
            st.session_state[budget_widget_key] = placeholder
            st.session_state.pop("selected_budget_guid", None)
            st.session_state.pop("selected_budget_name", None)

    # Pre-expander applicability check for current context (auto-opens Context on load).
    selected_budget_guid = st.session_state.get("selected_budget_guid")
    if (
        not selector_disabled
        and selected_budget_guid
        and isinstance(selected_month_start, date)
    ):
        applicability = load_budget_applicability(
            schema_version=analytics_schema_version,
            backend=backend,
            budget_guid=str(selected_budget_guid),
            month_start=selected_month_start,
        )
        if not applicability.applicable:
            inapplicable_reason = applicability.reason
            expander_expanded = True

    if error_message:
        st.error(error_message)

    with st.expander("Context", expanded=expander_expanded):
        st.date_input(
            "Month",
            key=month_widget_key,
            disabled=selector_disabled,
        )
        budget_index = 0
        current_label = st.session_state.get(budget_widget_key)
        if isinstance(current_label, str) and current_label in labels:
            budget_index = labels.index(current_label)
        st.selectbox(
            "Budget",
            options=labels,
            index=budget_index,
            key=budget_widget_key,
            disabled=selector_disabled,
        )
        st.selectbox(
            "Layout",
            options=["Auto", "Desktop", "Mobile"],
            index=0,
            key=layout_mode_key,
            disabled=selector_disabled,
        )

    # Apply current widget state into the canonical context keys.
    resolved_month_value = st.session_state.get(month_widget_key)
    if isinstance(resolved_month_value, date):
        selected_month_start = date(
            resolved_month_value.year,
            resolved_month_value.month,
            1,
        )
        st.session_state["selected_month_start"] = selected_month_start

    if not selector_disabled:
        selected_label = st.session_state.get(budget_widget_key, placeholder)
        if selected_label == placeholder:
            st.session_state.pop("selected_budget_guid", None)
            st.session_state.pop("selected_budget_name", None)
        elif isinstance(selected_label, str) and selected_label in label_to_guid:
            st.session_state["selected_budget_guid"] = label_to_guid[selected_label]
            st.session_state["selected_budget_name"] = label_to_name[selected_label]
        else:
            st.session_state[budget_widget_key] = placeholder
            st.session_state.pop("selected_budget_guid", None)
            st.session_state.pop("selected_budget_name", None)

    layout_mode = st.session_state.get(layout_mode_key, "Auto")
    if layout_mode not in {"Auto", "Desktop", "Mobile"}:
        st.session_state[layout_mode_key] = "Auto"
        layout_mode = "Auto"

    selected_budget_name = st.session_state.get("selected_budget_name") or "—"
    month_label = "—"
    if isinstance(selected_month_start, date):
        month_label = selected_month_start.strftime("%Y-%m")
    context_delta_text = "vs last month: —"

    if selector_disabled:
        st.caption(
            f"Month: {month_label} · Budget: {selected_budget_name} · {context_delta_text}"
        )
        _render_month_summary_shell(status_label_text="—")
        _render_expense_hierarchy_shell()
        st.stop()

    if not st.session_state.get("selected_budget_guid"):
        st.caption(
            f"Month: {month_label} · Budget: {selected_budget_name} · {context_delta_text}"
        )
        _render_month_summary_shell(status_label_text="—")
        _render_expense_hierarchy_shell()
        st.error("Open Context and select a budget to continue.")
        st.stop()

    applicability = load_budget_applicability(
        schema_version=analytics_schema_version,
        backend=backend,
        budget_guid=str(st.session_state["selected_budget_guid"]),
        month_start=selected_month_start,
    )
    if not applicability.applicable:
        inapplicable_reason = applicability.reason

    if inapplicable_reason is not None:
        status_label_text = "No budget"
        st.caption(
            f"Month: {month_label} · Budget: {selected_budget_name} · {context_delta_text}"
        )
        _render_month_summary_shell(status_label_text=status_label_text)
        _render_expense_hierarchy_shell()
        if inapplicable_reason == BudgetInapplicableReason.OUT_OF_RANGE:
            st.error(
                "Selected budget cannot be applied to this month (out of range). "
                "Open Context and select a different budget."
            )
        elif inapplicable_reason == BudgetInapplicableReason.NO_TARGETS:
            st.error(
                "Selected budget cannot be applied to this month (no expense targets). "
                "Open Context and select a different budget."
            )
        else:
            st.error(
                "Budget data is unavailable for the selected context. "
                "Open Context and select a different budget."
            )
        st.stop()

    accounts_tree = load_accounts_tree(schema_version=analytics_schema_version)
    node_paths = _build_account_full_paths(accounts_tree)
    selected_budget_guid_str = str(st.session_state["selected_budget_guid"])
    month_view_cache_key = _budget_month_view_cache_key(
        schema_version=analytics_schema_version,
        backend=backend,
        budget_guid=selected_budget_guid_str,
        month_start=selected_month_start,
        node_paths=node_paths,
    )
    month_view_cache = st.session_state.setdefault("budget_month_view_cache", {})

    perf_enabled = os.getenv("BUDGET_PERF_DEBUG", "").strip() in {"1", "true", "True"}
    perf_start = perf_counter()
    perf_events: list[tuple[str, float]] = []

    if month_view_cache_key in month_view_cache:
        month_view = month_view_cache[month_view_cache_key]
        if perf_enabled:
            perf_events.append(("month_view_cache_hit", perf_counter()))
    else:
        month_view = load_budget_month_view(
            schema_version=analytics_schema_version,
            backend=backend,
            budget_guid=selected_budget_guid_str,
            month_start=selected_month_start,
            node_paths=node_paths,
        )
        month_view_cache[month_view_cache_key] = month_view
        if perf_enabled:
            perf_events.append(("month_view_fetch", perf_counter()))
    previous_month_start = _previous_month_start(selected_month_start)
    previous_month_summary: BudgetMonthSummaryDTO | None = None
    previous_month_cache_key = _budget_month_view_cache_key(
        schema_version=analytics_schema_version,
        backend=backend,
        budget_guid=selected_budget_guid_str,
        month_start=previous_month_start,
        node_paths=node_paths,
    )
    try:
        if previous_month_cache_key in month_view_cache:
            previous_month_view = month_view_cache[previous_month_cache_key]
            if perf_enabled:
                perf_events.append(("previous_month_cache_hit", perf_counter()))
        else:
            previous_month_view = load_budget_month_view(
                schema_version=analytics_schema_version,
                backend=backend,
                budget_guid=selected_budget_guid_str,
                month_start=previous_month_start,
                node_paths=node_paths,
            )
            month_view_cache[previous_month_cache_key] = previous_month_view
            if perf_enabled:
                perf_events.append(("previous_month_fetch", perf_counter()))
        previous_month_summary = previous_month_view.summary
    except RuntimeError:
        # Missing/unavailable previous-month context falls back to explicit n/a.
        previous_month_summary = None

    actual_delta: Decimal | None = None
    remaining_over_delta: Decimal | None = None
    if previous_month_summary is not None:
        actual_delta = (
            Decimal(month_view.summary.total_actual)
            - Decimal(previous_month_summary.total_actual)
        )
        remaining_over_delta = (
            _remaining_over_value(month_view.summary)
            - _remaining_over_value(previous_month_summary)
        )
    context_delta_text = _format_context_delta_text(
        actual_delta=actual_delta,
        remaining_over_delta=remaining_over_delta,
    )
    st.caption(
        f"Month: {month_label} · Budget: {selected_budget_name} · {context_delta_text}"
    )
    hierarchy_rows = build_budget_hierarchy_rows(
        accounts_tree,
        month_view.node_results,
    )
    _render_month_summary(
        summary=month_view.summary,
        remaining_over_delta=remaining_over_delta,
    )
    if layout_mode == "Mobile":
        mobile_layout_active = True
    elif layout_mode == "Desktop":
        mobile_layout_active = False
    else:
        mobile_layout_active = _is_mobile_layout_active()
    _render_expense_hierarchy(
        rows=hierarchy_rows,
        mobile_layout_active=mobile_layout_active,
    )
    if perf_enabled:
        total_ms = (perf_counter() - perf_start) * 1000
        st.caption(f"Perf (debug): Budget render {total_ms:.1f} ms")
        for label, ts in perf_events:
            delta_ms = (ts - perf_start) * 1000
            st.caption(f"Perf (debug): {label} at {delta_ms:.1f} ms")
    st.caption(
        f"Computed {len(hierarchy_rows)} expense hierarchy rows."
    )


def _budget_month_view_cache_key(
    *,
    schema_version: int,
    backend: str,
    budget_guid: str,
    month_start: date,
    node_paths: dict[str, str],
) -> tuple[
    int,
    str,
    str,
    date,
    tuple[tuple[str, str], ...],
]:
    return (
        schema_version,
        backend.strip().lower(),
        budget_guid,
        date(month_start.year, month_start.month, 1),
        tuple(sorted(node_paths.items())),
    )
