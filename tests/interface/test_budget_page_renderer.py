from __future__ import annotations

from datetime import date

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def markdown(self, text: str) -> None:
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
    assert any("Over" == line for line in fake_st.markdowns)
