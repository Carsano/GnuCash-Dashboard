"""Tests for the test_db_connection adapter."""

from src.adapters import test_db_connection


class _DummyConnection:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def exec_driver_sql(self, statement: str) -> None:
        self.executed.append(statement)


class _DummyEngine:
    def __init__(self, url: str) -> None:
        self.url = url
        self.connection = _DummyConnection()

    def connect(self):
        return self.connection


def test_main_logs_successful_checks(monkeypatch):
    """The CLI should log connection URLs and execute SELECT 1."""
    gnucash_engine = _DummyEngine("postgresql://gnucash")
    analytics_engine = _DummyEngine("postgresql://analytics")

    class _Adapter:
        def get_gnucash_engine(self):
            return gnucash_engine

        def get_analytics_engine(self):
            return analytics_engine

    log_messages: list[str] = []

    class _Logger:
        def info(self, msg: str) -> None:
            log_messages.append(msg)

    monkeypatch.setattr(
        test_db_connection,
        "build_database_adapter",
        lambda: _Adapter(),
    )
    monkeypatch.setattr(
        test_db_connection,
        "get_app_logger",
        lambda: _Logger(),
    )

    test_db_connection.main()

    assert "postgresql://gnucash" in log_messages[0]
    assert "postgresql://analytics" in log_messages[1]
    assert gnucash_engine.connection.executed == ["SELECT 1"]
    assert analytics_engine.connection.executed == ["SELECT 1"]
