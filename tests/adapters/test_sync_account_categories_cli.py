"""Tests for the sync_account_categories_cli adapter."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.adapters import sync_account_categories_cli


def test_main_runs_use_case_and_prints_result(monkeypatch, capsys):
    """The CLI should instantiate the use case and print the summary."""
    fake_logger = MagicMock()
    dummy_adapter = object()
    fake_use_case = MagicMock()
    fake_use_case.run.return_value = SimpleNamespace(
        source_count=4,
        inserted_count=4,
    )

    monkeypatch.setattr(
        sync_account_categories_cli,
        "get_app_logger",
        lambda: fake_logger,
    )
    monkeypatch.setattr(
        sync_account_categories_cli,
        "build_database_adapter",
        lambda: dummy_adapter,
    )

    def _fake_use_case(db_port, logger):
        assert db_port is dummy_adapter
        assert logger is fake_logger
        return fake_use_case

    monkeypatch.setattr(
        sync_account_categories_cli,
        "SyncAccountCategoriesUseCase",
        _fake_use_case,
    )

    sync_account_categories_cli.main()

    fake_use_case.run.assert_called_once()
    captured = capsys.readouterr()
    assert "source=4" in captured.out
    assert "inserted=4" in captured.out
