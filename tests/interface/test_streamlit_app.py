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
        "SqlAlchemyDatabaseEngineAdapter",
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


class _FakeStreamlit:
    def __init__(self) -> None:
        self.config_called = False
        self.title_called = False
        self.captions: list[str] = []
        self.warning_called = False
        self.dataframe_payload = None

    def set_page_config(self, **kwargs):
        self.config_called = True
        self.config_kwargs = kwargs

    def title(self, text: str):
        self.title_called = True
        self.title_text = text

    def caption(self, text: str):
        self.captions.append(text)

    def warning(self, text: str):
        self.warning_called = True
        self.warning_text = text

    def dataframe(self, data, **kwargs):
        self.dataframe_payload = (data, kwargs)

    def cache_data(self, **_kwargs):
        def decorator(func):
            return func

        return decorator


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

    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "_load_accounts", lambda: accounts)

    app.main()

    assert fake_st.config_called
    assert fake_st.title_called
    assert fake_st.warning_called is False
    table_data, kwargs = fake_st.dataframe_payload
    assert table_data[0]["GUID"] == "1"
    assert kwargs["use_container_width"] is True
    assert kwargs["hide_index"] is True


def test_main_warns_when_no_accounts(monkeypatch):
    """main should warn the user when analytics has no data."""
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "_load_accounts", lambda: [])

    app.main()

    assert fake_st.warning_called
