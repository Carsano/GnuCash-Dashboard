"""Tests for the GetNetWorthSummaryUseCase."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
)


def _build_db_port(rows: list[SimpleNamespace]) -> MagicMock:
    engine = MagicMock()
    conn = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = conn
    engine.connect.return_value = context
    conn.execute.return_value.all.return_value = rows

    db_port = MagicMock()
    db_port.get_gnucash_engine.return_value = engine
    return db_port


def test_execute_returns_summary_totals() -> None:
    """Use case should aggregate assets, liabilities, and net worth."""
    rows = [
        SimpleNamespace(account_type="ASSET", balance=Decimal("120.50")),
        SimpleNamespace(account_type="LIABILITY", balance=Decimal("-40.25")),
        SimpleNamespace(account_type="INCOME", balance=Decimal("999.00")),
    ]
    db_port = _build_db_port(rows)

    use_case = GetNetWorthSummaryUseCase(db_port=db_port)

    result = use_case.execute()

    assert result.asset_total == Decimal("120.50")
    assert result.liability_total == Decimal("40.25")
    assert result.net_worth == Decimal("80.25")


def test_execute_applies_date_filters() -> None:
    """Use case should pass date filters to the query."""
    rows = [
        SimpleNamespace(account_type="ASSET", balance=Decimal("10.00")),
    ]
    db_port = _build_db_port(rows)
    engine = db_port.get_gnucash_engine.return_value

    use_case = GetNetWorthSummaryUseCase(db_port=db_port)

    use_case.execute(start_date=date(2024, 1, 1), end_date=date(2024, 3, 31))

    engine.connect.return_value.__enter__.return_value.execute.assert_called_once()
    _, params = engine.connect.return_value.__enter__.return_value.execute.call_args
    assert params == {
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 3, 31),
    }
