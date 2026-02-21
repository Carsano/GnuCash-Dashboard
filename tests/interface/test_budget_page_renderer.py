from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.domain.models.budget import BudgetDTO


class _Stop(Exception):
    pass


class _FakeExpander:
    def __init__(self, st, label: str, expanded: bool) -> None:
        self._st = st
        self.label = label
        self.expanded = expanded

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.subheaders: list[str] = []
        self.captions: list[str] = []
        self.errors: list[str] = []
        self.infos: list[str] = []
        self.markdowns: list[str] = []
        self.button_calls: list[dict[str, object]] = []
        self.selectbox_calls: list[dict[str, object]] = []
        self.expander_calls: list[dict[str, object]] = []
        self.next_selectbox_value: str | None = None
        self.next_columns_count: int | None = None
        self.next_button_values: dict[str, bool] = {}
        self.context = type(
            "_Context",
            (),
            {"headers": {"user-agent": "Desktop Browser"}},
        )()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def markdown(self, text: str, **_kwargs) -> None:
        self.markdowns.append(text)

    def button(self, label: str, *, key: str | None = None, **_kwargs) -> bool:
        self.button_calls.append({"label": label, "key": key})
        if isinstance(key, str):
            return self.next_button_values.pop(key, False)
        return False

    def expander(self, label: str, expanded: bool = False):
        self.expander_calls.append({"label": label, "expanded": expanded})
        return _FakeExpander(self, label=label, expanded=expanded)

    def columns(self, spec):
        if isinstance(spec, int):
            count = spec
        else:
            count = len(spec)
        return [self for _ in range(count)]

    def selectbox(
        self,
        label: str,
        *,
        options,
        index: int = 0,
        disabled: bool = False,
        **_kwargs,
    ):
        key = _kwargs.get("key")
        self.selectbox_calls.append(
            {
                "label": label,
                "options": list(options),
                "index": index,
                "disabled": disabled,
            }
        )
        if self.next_selectbox_value is not None:
            value = self.next_selectbox_value
        else:
            value = list(options)[index]
        if isinstance(key, str):
            self.session_state[key] = value
        return value

    def date_input(
        self,
        _label: str,
        *,
        value=None,
        disabled: bool = False,
        **_kwargs,
    ):
        key = _kwargs.get("key")
        if value is None and isinstance(key, str):
            value = self.session_state.get(key)
        self.selectbox_calls.append(
            {
                "label": "date_input",
                "value": value,
                "disabled": disabled,
            }
        )
        if isinstance(key, str):
            self.session_state[key] = value
        return value

    def error(self, text: str) -> None:
        self.errors.append(text)

    def info(self, text: str) -> None:
        self.infos.append(text)

    def stop(self) -> None:
        raise _Stop()


def test_budget_page_selecting_budget_updates_session_and_summary_line(
    monkeypatch,
) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=50,
                total_remaining=50,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert fake_st.session_state["selected_budget_guid"] == "g1"
    assert fake_st.session_state["selected_budget_name"] == "Household"
    assert any("Budget:" in line and "Household" in line for line in fake_st.captions)
    assert any("vs last month" in line for line in fake_st.captions)


def test_budget_page_defaults_month_and_renders_in_caption(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=50,
                total_remaining=50,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "_today",
        lambda: date(2026, 2, 9),
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert fake_st.session_state["selected_month_start"] == date(2026, 2, 1)
    assert any(
        "Month:" in line and "2026-02" in line for line in fake_st.captions
    )
    assert any("Month Summary" in text for text in fake_st.subheaders)
    assert any("Expense hierarchy" in text for text in fake_st.subheaders)
    assert any("Remaining / Over" in text for text in fake_st.markdowns)
    assert any("Status" in text for text in fake_st.markdowns)


def test_previous_month_start_handles_year_boundary() -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page

    assert budget_page._previous_month_start(date(2026, 2, 1)) == date(2026, 1, 1)
    assert budget_page._previous_month_start(date(2026, 1, 1)) == date(2025, 12, 1)


def test_format_vs_last_month_delta_supports_sign_and_na() -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page

    assert budget_page._format_vs_last_month_delta(12.34) == "vs last month: +12.34"
    assert budget_page._format_vs_last_month_delta(-8.5) == "vs last month: -8.50"
    assert budget_page._format_vs_last_month_delta(None) == "vs last month: n/a"


def test_budget_page_renders_micro_deltas_in_context_and_remaining_kpi(
    monkeypatch,
) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )

    def _load_month_view(
        *,
        schema_version,
        backend,
        budget_guid,
        month_start,
        node_paths=None,
    ):
        if month_start == date(2026, 2, 1):
            return BudgetMonthViewDTO(
                summary=BudgetMonthSummaryDTO(
                    total_budget=100,
                    total_actual=80,
                    total_remaining=20,
                    total_over=0,
                    status_label="On track",
                ),
                node_results=[],
            )
        return BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=70,
                total_remaining=30,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        )

    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        _load_month_view,
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "_today",
        lambda: date(2026, 2, 9),
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert any(
        "Month: 2026-02 · Budget: Household · vs last month: "
        "Actual +10.00 · Remaining/Over -10.00" in line
        for line in fake_st.captions
    )
    assert any("vs last month: -10.00" in line for line in fake_st.captions)


def test_budget_page_renders_na_deltas_when_previous_month_unavailable(
    monkeypatch,
) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )

    def _load_month_view(
        *,
        schema_version,
        backend,
        budget_guid,
        month_start,
        node_paths=None,
    ):
        if month_start == date(2026, 2, 1):
            return BudgetMonthViewDTO(
                summary=BudgetMonthSummaryDTO(
                    total_budget=100,
                    total_actual=80,
                    total_remaining=20,
                    total_over=0,
                    status_label="On track",
                ),
                node_results=[],
            )
        raise RuntimeError("Previous month unavailable")

    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        _load_month_view,
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "_today",
        lambda: date(2026, 2, 9),
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert any(
        "Month: 2026-02 · Budget: Household · vs last month: n/a" in line
        for line in fake_st.captions
    )
    assert sum(1 for line in fake_st.captions if "vs last month: n/a" in line) >= 2


def test_budget_page_changing_month_updates_session(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=50,
                total_remaining=50,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "_today",
        lambda: date(2026, 2, 9),
    )
    fake_st.session_state["budget_context_month"] = date(2026, 1, 20)

    budget_page.render_budget_page(analytics_schema_version=1)

    assert fake_st.session_state["selected_month_start"] == date(2026, 1, 1)


def test_budget_page_no_budgets_blocks_and_disables_selector(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page

    fake_st = _FakeStreamlit()
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [],
    )

    with pytest.raises(_Stop):
        budget_page.render_budget_page(analytics_schema_version=1)

    assert any("No budgets found" in msg for msg in fake_st.errors)
    assert any(
        call["label"] == "Context" and call["expanded"] is True
        for call in fake_st.expander_calls
    )
    assert fake_st.selectbox_calls
    assert fake_st.selectbox_calls[-1]["disabled"] is True


def test_budget_page_unsupported_backend_error_is_actionable(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.ports.budget_repository import BudgetsUnsupportedBackendError

    fake_st = _FakeStreamlit()
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: (_ for _ in ()).throw(
            BudgetsUnsupportedBackendError(backend="analytics")
        ),
    )

    with pytest.raises(_Stop):
        budget_page.render_budget_page(analytics_schema_version=1)

    assert any("Budgets are not available" in msg for msg in fake_st.errors)
    assert any(
        call["label"] == "Context" and call["expanded"] is True
        for call in fake_st.expander_calls
    )


def test_budget_page_missing_env_var_error_is_helpful(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page

    fake_st = _FakeStreamlit()
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: (_ for _ in ()).throw(
            RuntimeError("Missing environment variable: GNUCASH_DB_URL")
        ),
    )

    with pytest.raises(_Stop):
        budget_page.render_budget_page(analytics_schema_version=1)

    assert any("Missing configuration: set `GNUCASH_DB_URL`" in msg for msg in fake_st.errors)
    assert any(
        call["label"] == "Context" and call["expanded"] is True
        for call in fake_st.expander_calls
    )


def test_budget_page_inapplicable_budget_blocks_and_expands_context(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetInapplicableReason,
        BudgetDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.session_state["selected_budget_guid"] = "g1"
    fake_st.session_state["selected_budget_name"] = "Household"
    fake_st.session_state["selected_month_start"] = date(2026, 2, 1)

    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=False,
            reason=BudgetInapplicableReason.NO_TARGETS,
        ),
    )

    with pytest.raises(_Stop):
        budget_page.render_budget_page(analytics_schema_version=1)

    assert any("cannot be applied" in msg.lower() for msg in fake_st.errors)
    assert any(
        call["label"] == "Context" and call["expanded"] is True
        for call in fake_st.expander_calls
    )


def test_budget_page_inapplicable_budget_out_of_range_is_explained(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetInapplicableReason,
        BudgetDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.session_state["selected_budget_guid"] = "g1"
    fake_st.session_state["selected_budget_name"] = "Household"
    fake_st.session_state["selected_month_start"] = date(2026, 2, 1)

    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=False,
            reason=BudgetInapplicableReason.OUT_OF_RANGE,
        ),
    )

    with pytest.raises(_Stop):
        budget_page.render_budget_page(analytics_schema_version=1)

    assert any("out of range" in msg.lower() for msg in fake_st.errors)


def test_budget_page_renders_real_month_summary_values_when_applicable(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=75,
                total_remaining=25,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert any("100.00" in line for line in fake_st.captions)
    assert any("75.00" in line for line in fake_st.captions)
    assert any("25.00 / 0.00" in line for line in fake_st.captions)
    assert any("Computed 0 expense hierarchy rows" in line for line in fake_st.captions)


def test_budget_page_renders_expense_hierarchy_rows_when_available(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=75,
                total_remaining=25,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "build_budget_hierarchy_rows",
        lambda accounts, node_results: (
            BudgetHierarchyRow(
                node_guid="food",
                node_name="Food",
                node_path="Expenses:Home:Food",
                depth=2,
                budget=100,
                actual=75,
                remaining=25,
                over=0,
                status_label="On track",
                no_budget=False,
            ),
        ),
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert any("Category" in text for text in fake_st.markdowns)
    assert any("Progress" in text for text in fake_st.markdowns)
    assert any("|  |- Food" in line for line in fake_st.markdowns)
    assert any("100.00" in line for line in fake_st.markdowns)
    assert any("Remaining: 25.00" in line for line in fake_st.markdowns)
    assert any("On track" in line for line in fake_st.markdowns)


def test_budget_page_passes_account_node_paths_to_month_view_loader(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.accounts import AccountDTO
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    captured: dict[str, object] = {}

    def _load_month_view(
        *,
        schema_version,
        backend,
        budget_guid,
        month_start,
        node_paths=None,
    ):
        captured["node_paths"] = dict(node_paths or {})
        return BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=50,
                total_remaining=50,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        )

    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        _load_month_view,
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [
            AccountDTO(
                guid="root-exp",
                name="Expenses",
                account_type="EXPENSE",
                commodity_guid=None,
                parent_guid=None,
            ),
            AccountDTO(
                guid="food",
                name="Food",
                account_type="EXPENSE",
                commodity_guid=None,
                parent_guid="root-exp",
            ),
        ],
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert captured["node_paths"] == {
        "root-exp": "Expenses",
        "food": "Expenses:Food",
    }


def test_budget_page_hierarchy_is_collapsed_by_default_and_expands_from_session(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=75,
                total_remaining=25,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "build_budget_hierarchy_rows",
        lambda accounts, node_results: (
            BudgetHierarchyRow(
                node_guid="parent",
                node_name="Parent",
                node_path="Expenses:Parent",
                depth=0,
                budget=100,
                actual=75,
                remaining=25,
                over=0,
                status_label="On track",
                no_budget=False,
            ),
            BudgetHierarchyRow(
                node_guid="child",
                node_name="Child",
                node_path="Expenses:Parent:Child",
                depth=1,
                budget=100,
                actual=75,
                remaining=25,
                over=0,
                status_label="On track",
                no_budget=False,
            ),
        ),
    )

    budget_page.render_budget_page(analytics_schema_version=1)
    assert any("Parent" in call["label"] for call in fake_st.button_calls)
    assert not any("Child" in line for line in fake_st.markdowns)

    fake_st.session_state["budget_hierarchy_expanded_guids"] = {"parent"}
    budget_page.render_budget_page(analytics_schema_version=1)
    assert any("|- Child" in line for line in fake_st.markdowns)


def test_budget_page_hierarchy_shows_explicit_over_label(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=125,
                total_remaining=0,
                total_over=25,
                status_label="Over",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "build_budget_hierarchy_rows",
        lambda accounts, node_results: (
            BudgetHierarchyRow(
                node_guid="row-1",
                node_name="Row 1",
                node_path="Expenses:Row1",
                depth=0,
                budget=100,
                actual=125,
                remaining=0,
                over=25,
                status_label="Over",
                no_budget=False,
            ),
        ),
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert any("Over: 25.00" in line for line in fake_st.markdowns)
    assert any("Over" in line for line in fake_st.markdowns)
    assert any("TOP-OVER" in line for line in fake_st.markdowns)


def test_select_top_over_highlight_guids_is_deterministic_and_capped() -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow

    visible_rows = (
        BudgetHierarchyRow(
            node_guid="a",
            node_name="A",
            node_path="Expenses:Alpha",
            depth=0,
            budget=100,
            actual=140,
            remaining=0,
            over=40,
            status_label="Over",
            no_budget=False,
        ),
        BudgetHierarchyRow(
            node_guid="b",
            node_name="B",
            node_path="Expenses:Beta",
            depth=0,
            budget=100,
            actual=140,
            remaining=0,
            over=40,
            status_label="Over",
            no_budget=False,
        ),
        BudgetHierarchyRow(
            node_guid="c",
            node_name="C",
            node_path="Expenses:Gamma",
            depth=0,
            budget=100,
            actual=130,
            remaining=0,
            over=30,
            status_label="Over",
            no_budget=False,
        ),
        BudgetHierarchyRow(
            node_guid="d",
            node_name="D",
            node_path="Expenses:Delta",
            depth=0,
            budget=100,
            actual=120,
            remaining=0,
            over=20,
            status_label="Over",
            no_budget=False,
        ),
        BudgetHierarchyRow(
            node_guid="e",
            node_name="E",
            node_path="Expenses:Epsilon",
            depth=0,
            budget=100,
            actual=115,
            remaining=0,
            over=15,
            status_label="Over",
            no_budget=False,
        ),
        BudgetHierarchyRow(
            node_guid="f",
            node_name="F",
            node_path="Expenses:Zeta",
            depth=0,
            budget=100,
            actual=110,
            remaining=0,
            over=10,
            status_label="Over",
            no_budget=False,
        ),
    )

    selected = budget_page._select_top_over_highlight_guids(
        visible_rows=visible_rows,
        cap=5,
    )
    # Tie on over=40 resolved deterministically by node_path, then guid.
    assert selected == {"a", "b", "c", "d", "e"}


def test_select_top_over_highlight_guids_ignores_non_over_rows() -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow

    visible_rows = (
        BudgetHierarchyRow(
            node_guid="over-row",
            node_name="Over Row",
            node_path="Expenses:Over",
            depth=0,
            budget=100,
            actual=125,
            remaining=0,
            over=25,
            status_label="Over",
            no_budget=False,
        ),
        BudgetHierarchyRow(
            node_guid="remaining-row",
            node_name="Remaining Row",
            node_path="Expenses:Remaining",
            depth=0,
            budget=100,
            actual=75,
            remaining=25,
            over=0,
            status_label="On track",
            no_budget=False,
        ),
    )

    selected = budget_page._select_top_over_highlight_guids(
        visible_rows=visible_rows,
        cap=5,
    )
    assert selected == {"over-row"}


def test_build_mobile_row_card_html_contains_core_labels_and_values() -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow

    row = BudgetHierarchyRow(
        node_guid="row-1",
        node_name="Food",
        node_path="Expenses:Food",
        depth=1,
        budget=100,
        actual=125,
        remaining=0,
        over=25,
        status_label="Over",
        no_budget=False,
    )

    html = budget_page._build_mobile_row_card_html(
        row=row,
        highlighted=True,
        node_label="|- Food",
    )

    assert "budget-mobile-card" in html
    assert "Category: |- Food" in html
    assert "Status" in html
    assert "Budget" in html
    assert "Actual" in html
    assert "Remaining/Over" in html
    assert "Over: 25.00" in html


def test_budget_page_renders_mobile_card_markup_for_hierarchy_rows(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.context.headers["user-agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit Mobile"
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=75,
                total_remaining=25,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "build_budget_hierarchy_rows",
        lambda accounts, node_results: (
            BudgetHierarchyRow(
                node_guid="mobile-row",
                node_name="Mobile Row",
                node_path="Expenses:MobileRow",
                depth=0,
                budget=100,
                actual=75,
                remaining=25,
                over=0,
                status_label="On track",
                no_budget=False,
            ),
        ),
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert any("budget-mobile-card" in line for line in fake_st.markdowns)
    assert any("Category: Mobile Row" in line for line in fake_st.markdowns)


def test_budget_page_desktop_layout_does_not_render_mobile_card_markup(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.application.use_cases.build_budget_hierarchy_rows import BudgetHierarchyRow
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.context.headers["user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X)"
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=75,
                total_remaining=25,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "build_budget_hierarchy_rows",
        lambda accounts, node_results: (
            BudgetHierarchyRow(
                node_guid="desktop-row",
                node_name="Desktop Row",
                node_path="Expenses:DesktopRow",
                depth=0,
                budget=100,
                actual=75,
                remaining=25,
                over=0,
                status_label="On track",
                no_budget=False,
            ),
        ),
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert not any(
        "<div class='budget-mobile-card" in line for line in fake_st.markdowns
    )


def test_is_mobile_layout_active_uses_client_hint_header(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page

    fake_st = _FakeStreamlit()
    fake_st.context.headers["user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X)"
    fake_st.context.headers["sec-ch-ua-mobile"] = "?1"

    monkeypatch.setattr(budget_page, "st", fake_st)
    assert budget_page._is_mobile_layout_active() is True


def test_budget_accessibility_css_contains_focus_visible_and_touch_target_rules() -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page

    css = budget_page._budget_accessibility_css_text()

    assert ":focus-visible" in css
    assert "outline: 2px solid" in css
    assert "min-height: 44px" in css


def test_budget_page_injects_accessibility_css(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=100,
                total_actual=75,
                total_remaining=25,
                total_over=0,
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert any(":focus-visible" in line for line in fake_st.markdowns)


def test_budget_month_view_cache_key_is_stable_and_context_scoped() -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page

    node_paths = {"a": "Expenses:A", "b": "Expenses:B"}
    key_1 = budget_page._budget_month_view_cache_key(
        schema_version=3,
        backend="SQLAlchemy",
        budget_guid="g1",
        month_start=date(2026, 2, 13),
        node_paths=node_paths,
    )
    key_2 = budget_page._budget_month_view_cache_key(
        schema_version=3,
        backend="sqlalchemy",
        budget_guid="g1",
        month_start=date(2026, 2, 1),
        node_paths={"b": "Expenses:B", "a": "Expenses:A"},
    )
    key_3 = budget_page._budget_month_view_cache_key(
        schema_version=3,
        backend="sqlalchemy",
        budget_guid="g1",
        month_start=date(2026, 3, 1),
        node_paths=node_paths,
    )

    assert key_1 == key_2
    assert key_1 != key_3


def test_budget_page_reuses_cached_month_views_across_rerender(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )

    calls = {"count": 0}

    def _load_month_view(
        *,
        schema_version,
        backend,
        budget_guid,
        month_start,
        node_paths=None,
    ):
        calls["count"] += 1
        return BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=Decimal("100"),
                total_actual=Decimal("50"),
                total_remaining=Decimal("50"),
                total_over=Decimal("0"),
                status_label="On track",
            ),
            node_results=[],
        )

    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        _load_month_view,
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )
    monkeypatch.setattr(
        budget_page,
        "_today",
        lambda: date(2026, 2, 9),
    )

    budget_page.render_budget_page(analytics_schema_version=1)
    budget_page.render_budget_page(analytics_schema_version=1)

    # First render: current month + previous month fetch. Second render: session cache hits.
    assert calls["count"] == 2


def test_budget_page_perf_debug_emits_timing_captions(monkeypatch) -> None:
    from src.adapters.interface.streamlit.page_renderers import budget as budget_page
    from src.domain.models.budget import (
        BudgetApplicabilityDTO,
        BudgetMonthSummaryDTO,
        BudgetMonthViewDTO,
    )

    fake_st = _FakeStreamlit()
    fake_st.next_selectbox_value = "Household"
    monkeypatch.setattr(budget_page, "st", fake_st)
    monkeypatch.setenv("BUDGET_PERF_DEBUG", "1")
    monkeypatch.setattr(
        budget_page,
        "load_budgets",
        lambda *, schema_version, backend: [
            BudgetDTO(guid="g1", name="Household", num_periods=12)
        ],
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_applicability",
        lambda *, schema_version, backend, budget_guid, month_start: BudgetApplicabilityDTO(
            applicable=True,
            reason=None,
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_budget_month_view",
        lambda *, schema_version, backend, budget_guid, month_start, node_paths=None: BudgetMonthViewDTO(
            summary=BudgetMonthSummaryDTO(
                total_budget=Decimal("100"),
                total_actual=Decimal("50"),
                total_remaining=Decimal("50"),
                total_over=Decimal("0"),
                status_label="On track",
            ),
            node_results=[],
        ),
    )
    monkeypatch.setattr(
        budget_page,
        "load_accounts_tree",
        lambda *, schema_version: [],
    )

    budget_page.render_budget_page(analytics_schema_version=1)

    assert any("Perf (debug): Budget render" in line for line in fake_st.captions)
