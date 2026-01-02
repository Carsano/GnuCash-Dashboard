"""Tests for the Streamlit app module."""

from types import SimpleNamespace

from src.adapters.interface.streamlit import app


def test_fetch_accounts_invokes_use_case(monkeypatch):
    """_fetch_accounts should instantiate the adapter and use case."""
    fake_accounts = ["a"]

    class _FakeUseCase:
        def __init__(self, db_port):
            self.db_port = db_port

        def execute(self):
            return fake_accounts

    monkeypatch.setattr(
        app,
        "build_database_adapter",
        lambda: "adapter",
    )
    monkeypatch.setattr(
        app,
        "GetAccountsUseCase",
        lambda db_port: _FakeUseCase(db_port),
    )

    result = app._fetch_accounts()

    assert result == fake_accounts


def test_load_accounts_uses_fetch(monkeypatch):
    """The cached loader should delegate to _fetch_accounts."""
    fake_accounts = ["cached"]
    monkeypatch.setattr(app, "_fetch_accounts", lambda: fake_accounts)
    result = app._load_accounts()
    assert result == fake_accounts


def test_fetch_net_worth_summary_invokes_use_case(monkeypatch):
    """_fetch_net_worth_summary should instantiate the adapter and use case."""
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

    monkeypatch.setattr(
        app,
        "build_database_adapter",
        lambda: "adapter",
    )
    monkeypatch.setattr(
        app,
        "build_gnucash_repository",
        lambda _adapter: "repository",
    )
    monkeypatch.setattr(
        app,
        "GetNetWorthSummaryUseCase",
        lambda gnucash_repository: _FakeUseCase(gnucash_repository),
    )

    result = app._fetch_net_worth_summary(start_date=None, end_date=None)

    assert result == fake_summary


class _FakeStreamlit:
    def __init__(self) -> None:
        self.config_called = False
        self.title_called = False
        self.captions: list[str] = []
        self.warning_called = False
        self.dataframe_payload = None
        self.sidebar = _FakeSidebar()

    def set_page_config(self, **kwargs):
        self.config_called = True
        self.config_kwargs = kwargs

    def title(self, text: str):
        self.title_called = True
        self.title_text = text

    def subheader(self, text: str):
        self.subheader_text = text

    def text_input(self, _label: str, placeholder: str = ""):
        return ""

    def selectbox(self, _label: str, options, index: int = 0):
        return options[index]

    def caption(self, text: str):
        self.captions.append(text)

    def warning(self, text: str):
        self.warning_called = True
        self.warning_text = text

    def dataframe(self, data, **kwargs):
        self.dataframe_payload = (data, kwargs)

    def columns(self, spec):
        return [_FakeMetricColumn(), _FakeMetricColumn(), _FakeMetricColumn()]

    def cache_data(self, **_kwargs):
        def decorator(func):
            return func

        return decorator


class _FakeSidebar:
    def __init__(self) -> None:
        self.selectbox_value = "Accounts"

    def radio(self, _label: str, options):
        return self.selectbox_value

    def selectbox(self, _label: str, options):
        return self.selectbox_value


class _FakeMetricColumn:
    def metric(self, label: str, value: str, delta: str | None = None):
        self.label = label
        self.value = value
        self.delta = delta


def test_main_displays_accounts(monkeypatch):
    """main should render the dataframe when accounts exist."""
    fake_st = _FakeStreamlit()
    accounts = [
        SimpleNamespace(
            guid="1",
            name="Checking",
            account_type="BANK",
            commodity_guid="USD",
            parent_guid=None,
        )
    ]

    fake_st.sidebar.selectbox_value = "Accounts"
    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "_load_accounts", lambda: accounts)
    monkeypatch.setattr(
        app,
        "_load_net_worth_summary",
        lambda start_date, end_date: SimpleNamespace(
            asset_total=1,
            liability_total=2,
            net_worth=3,
            currency_code="EUR",
        ),
    )

    app.main()

    assert fake_st.config_called
    assert fake_st.title_called
    assert fake_st.warning_called is False
    table_data, kwargs = fake_st.dataframe_payload
    assert table_data[0]["Name"] == "Checking"
    assert kwargs["width"] == "stretch"
    assert kwargs["hide_index"] is True


def test_main_warns_when_no_accounts(monkeypatch):
    """main should warn the user when analytics has no data."""
    fake_st = _FakeStreamlit()
    fake_st.sidebar.selectbox_value = "Accounts"
    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "_load_accounts", lambda: [])
    monkeypatch.setattr(
        app,
        "_load_net_worth_summary",
        lambda start_date, end_date: SimpleNamespace(
            asset_total=1,
            liability_total=2,
            net_worth=3,
            currency_code="EUR",
        ),
    )

    app.main()

    assert fake_st.warning_called
