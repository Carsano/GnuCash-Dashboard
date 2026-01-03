"""Tests for the sync_accounts_cli adapter."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.adapters import sync_accounts_cli


def test_main_runs_use_case_and_prints_result(monkeypatch, capsys):
    """The CLI should instantiate the use case and print the summary."""
    fake_logger = MagicMock()
    dummy_source = object()
    dummy_destination = object()
    fake_use_case = MagicMock()
    fake_use_case.run.return_value = SimpleNamespace(inserted_count=3)

    monkeypatch.setattr(
        sync_accounts_cli,
        "get_app_logger",
        lambda: fake_logger,
    )
    monkeypatch.setattr(
        sync_accounts_cli,
        "build_accounts_source",
        lambda: dummy_source,
    )
    monkeypatch.setattr(
        sync_accounts_cli,
        "build_accounts_destination",
        lambda: dummy_destination,
    )

    def _fake_use_case(source_port, destination_port, logger):
        assert source_port is dummy_source
        assert destination_port is dummy_destination
        assert logger is fake_logger
        return fake_use_case

    monkeypatch.setattr(
        sync_accounts_cli,
        "SyncAccountsUseCase",
        _fake_use_case,
    )

    sync_accounts_cli.main()

    fake_use_case.run.assert_called_once()
    captured = capsys.readouterr()
    assert "3" in captured.out
