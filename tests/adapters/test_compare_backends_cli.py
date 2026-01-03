"""Tests for the compare_backends_cli adapter."""

from decimal import Decimal
from pathlib import Path

from src.adapters import compare_backends_cli
from src.application.use_cases.compare_backends import (
    BackendComparison,
    BackendDiff,
    BackendSnapshot,
)


def test_main_runs_use_case_and_prints_result(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """The CLI should instantiate the use case and print the summary."""
    dummy_adapter = object()
    dummy_sql_repo = object()
    dummy_piecash_repo = object()

    class _Logger:
        def __init__(self) -> None:
            self.messages: list[str] = []

        def warning(self, msg: str) -> None:
            self.messages.append(msg)

        def error(self, msg: str) -> None:
            self.messages.append(msg)

        def info(self, msg: str) -> None:
            self.messages.append(msg)

    monkeypatch.setenv("PIECASH_FILE", str(tmp_path))
    monkeypatch.setattr(
        compare_backends_cli,
        "build_database_adapter",
        lambda: dummy_adapter,
    )
    monkeypatch.setattr(
        compare_backends_cli,
        "SqlAlchemyGnuCashRepository",
        lambda adapter: dummy_sql_repo,
    )
    monkeypatch.setattr(
        compare_backends_cli,
        "PieCashGnuCashRepository",
        lambda path, logger=None: dummy_piecash_repo,
    )
    monkeypatch.setattr(
        compare_backends_cli,
        "get_app_logger",
        lambda: _Logger(),
    )

    comparison = BackendComparison(
        left=BackendSnapshot(
            name="sqlalchemy",
            balance_count=2,
            price_count=1,
            asset_total=Decimal("100.00"),
            liability_total=Decimal("20.00"),
            net_worth=Decimal("80.00"),
            currency_code="EUR",
        ),
        right=BackendSnapshot(
            name="piecash",
            balance_count=2,
            price_count=1,
            asset_total=Decimal("101.00"),
            liability_total=Decimal("22.00"),
            net_worth=Decimal("79.00"),
            currency_code="EUR",
        ),
        diff=BackendDiff(
            balance_count_delta=0,
            price_count_delta=0,
            asset_delta=Decimal("1.00"),
            liability_delta=Decimal("2.00"),
            net_worth_delta=Decimal("-1.00"),
        ),
    )

    class _FakeUseCase:
        def __init__(self, left_repository, right_repository, logger=None):
            assert left_repository is dummy_sql_repo
            assert right_repository is dummy_piecash_repo
            assert logger is not None

        def execute(self, **_kwargs):
            return comparison

    monkeypatch.setattr(
        compare_backends_cli,
        "CompareBackendsUseCase",
        _FakeUseCase,
    )

    compare_backends_cli.main()

    captured = capsys.readouterr()
    assert "Backend comparison" in captured.out
    assert "Deltas (right - left)" in captured.out
