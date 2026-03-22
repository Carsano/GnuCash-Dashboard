"""Tests for the sync_account_daily_history_cli adapter."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.adapters import sync_account_daily_history_cli


def test_main_runs_use_case_and_prints_result(monkeypatch, capsys):
    """The CLI should instantiate the use case and print the summary."""
    fake_logger = MagicMock()
    dummy_adapter = object()
    fake_use_case = MagicMock()
    fake_use_case.run.return_value = SimpleNamespace(
        account_count=2,
        snapshot_count=3,
        inserted_count=6,
        target_currency="EUR",
    )

    monkeypatch.setattr(
        sync_account_daily_history_cli,
        "get_app_logger",
        lambda: fake_logger,
    )
    monkeypatch.setattr(
        sync_account_daily_history_cli,
        "build_database_adapter",
        lambda: dummy_adapter,
    )

    def _fake_use_case(db_port, logger):
        assert db_port is dummy_adapter
        assert logger is fake_logger
        return fake_use_case

    monkeypatch.setattr(
        sync_account_daily_history_cli,
        "SyncAccountDailyHistoryUseCase",
        _fake_use_case,
    )

    sync_account_daily_history_cli.main()

    fake_use_case.run.assert_called_once_with()
    captured = capsys.readouterr()
    assert "accounts=2" in captured.out
    assert "snapshots=3" in captured.out
    assert "inserted=6" in captured.out
