"""Tests for the Streamlit wiring layer.

The entry-point `app.py` is intentionally thin: it configures Streamlit and
delegates rendering to page modules. Cached data loaders live in `shared.py`.
"""

from __future__ import annotations

from types import SimpleNamespace

from src.adapters.interface.streamlit import app, shared


def test_fetch_accounts_invokes_use_case(monkeypatch) -> None:
    """_fetch_accounts should instantiate the repository + use case."""
    fake_accounts = ["a"]

    class _FakeUseCase:
        def __init__(self, repository):
            self.repository = repository

        def execute(self):
            return fake_accounts

    monkeypatch.setattr(shared, "build_accounts_repository", lambda: "repository")
    monkeypatch.setattr(
        shared,
        "GetAccountsUseCase",
        lambda repository: _FakeUseCase(repository),
    )

    result = shared._fetch_accounts()
    assert result == fake_accounts


def test_load_accounts_delegates_to_fetch(monkeypatch) -> None:
    """The cached loader should delegate to _fetch_accounts."""
    fake_accounts = ["cached"]
    monkeypatch.setattr(shared, "_fetch_accounts", lambda: fake_accounts)
    result = shared.load_accounts(schema_version=999)
    assert result == fake_accounts


def test_fetch_net_worth_summary_invokes_use_case(monkeypatch) -> None:
    """_fetch_net_worth_summary should instantiate the repository + use case."""
    fake_summary = SimpleNamespace(
        asset_total=1,
        liability_total=2,
        net_worth=3,
        currency_code="EUR",
    )

    class _FakeUseCase:
        def __init__(self, gnucash_repository):
            self.gnucash_repository = gnucash_repository

        def execute(self, start_date=None, end_date=None):
            return fake_summary

    monkeypatch.setattr(shared, "build_analytics_repository", lambda: "repository")
    monkeypatch.setattr(
        shared,
        "GetNetWorthSummaryUseCase",
        lambda gnucash_repository: _FakeUseCase(gnucash_repository),
    )

    result = shared._fetch_net_worth_summary(start_date=None, end_date=None)
    assert result == fake_summary


def test_fetch_account_balances_invokes_use_case(monkeypatch) -> None:
    """_fetch_account_balances should instantiate the repository + use case."""
    fake_balances = ["balance"]

    class _FakeUseCase:
        def __init__(self, gnucash_repository):
            self.gnucash_repository = gnucash_repository

        def execute(self, end_date=None, target_currency="EUR"):
            return fake_balances

    monkeypatch.setattr(shared, "build_analytics_repository", lambda: "repository")
    monkeypatch.setattr(
        shared,
        "GetAccountBalancesUseCase",
        lambda gnucash_repository: _FakeUseCase(gnucash_repository),
    )

    result = shared._fetch_account_balances(end_date=None, target_currency="EUR")
    assert result == fake_balances


def test_load_account_balances_delegates_to_fetch(monkeypatch) -> None:
    """The cached loader should delegate to _fetch_account_balances."""
    fake_balances = ["cached"]
    monkeypatch.setattr(
        shared,
        "_fetch_account_balances",
        lambda end_date, target_currency: fake_balances,
    )
    result = shared.load_account_balances(
        end_date=None,
        target_currency="EUR",
        schema_version=999,
    )
    assert result == fake_balances


class _FakeSidebar:
    def __init__(self, selection: str) -> None:
        self.selection = selection

    def radio(self, _label: str, options):
        _ = options
        return self.selection


class _FakeStreamlit:
    def __init__(self, selection: str) -> None:
        self.sidebar = _FakeSidebar(selection)
        self.session_state: dict[str, object] = {}
        self.config_kwargs: dict[str, object] | None = None
        self.title_text: str | None = None

    def set_page_config(self, **kwargs):
        self.config_kwargs = kwargs

    def title(self, text: str):
        self.title_text = text


def test_main_delegates_to_accounts_page(monkeypatch) -> None:
    """main should call Accounts page renderer when selected."""
    fake_st = _FakeStreamlit("Accounts")
    monkeypatch.setattr(app, "st", fake_st)
    called: dict[str, bool] = {"accounts": False}

    monkeypatch.setattr(
        app,
        "render_accounts_page",
        lambda *, analytics_schema_version: called.__setitem__("accounts", True),
    )
    monkeypatch.setattr(app, "render_dashboard_page", lambda *, analytics_schema_version: None)
    monkeypatch.setattr(app, "render_cashflow_page", lambda *, analytics_schema_version: None)
    monkeypatch.setattr(app, "render_budget_page", lambda *, analytics_schema_version: None)
    monkeypatch.setattr(app, "render_diagnostics_page", lambda *, analytics_schema_version: None)

    app.main()

    assert fake_st.config_kwargs == {"page_title": "GnuCash Dashboard", "layout": "wide"}
    assert fake_st.title_text == "GnuCash Dashboard"
    assert called["accounts"] is True


def test_main_delegates_to_diagnostics_page(monkeypatch) -> None:
    """main should call Diagnostics renderer when selected."""
    fake_st = _FakeStreamlit("Diagnostics")
    monkeypatch.setattr(app, "st", fake_st)
    called: dict[str, bool] = {"diagnostics": False}

    monkeypatch.setattr(app, "render_dashboard_page", lambda *, analytics_schema_version: None)
    monkeypatch.setattr(app, "render_accounts_page", lambda *, analytics_schema_version: None)
    monkeypatch.setattr(app, "render_cashflow_page", lambda *, analytics_schema_version: None)
    monkeypatch.setattr(app, "render_budget_page", lambda *, analytics_schema_version: None)
    monkeypatch.setattr(
        app,
        "render_diagnostics_page",
        lambda *, analytics_schema_version: called.__setitem__("diagnostics", True),
    )

    app.main()

    assert called["diagnostics"] is True
