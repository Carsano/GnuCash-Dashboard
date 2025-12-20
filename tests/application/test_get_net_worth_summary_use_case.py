"""Tests for the GetNetWorthSummaryUseCase."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
)


class _FakeResult:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self._rows = rows

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


def _build_db_port(results: list[list[SimpleNamespace]]) -> MagicMock:
    engine = MagicMock()
    conn = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = conn
    engine.connect.return_value = context
    conn.execute.side_effect = [_FakeResult(rows) for rows in results]

    db_port = MagicMock()
    db_port.get_gnucash_engine.return_value = engine
    return db_port


def test_execute_returns_summary_totals() -> None:
    """Use case should aggregate assets, liabilities, and net worth."""
    currency_row = [SimpleNamespace(guid="eur-guid")]
    balances = [
        SimpleNamespace(
            account_type="ASSET",
            commodity_guid="usd-guid",
            mnemonic="USD",
            balance=Decimal("100.00"),
        ),
        SimpleNamespace(
            account_type="LIABILITY",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            balance=Decimal("-40.25"),
        ),
        SimpleNamespace(
            account_type="INCOME",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            balance=Decimal("999.00"),
        ),
    ]
    prices = [
        SimpleNamespace(
            commodity_guid="usd-guid",
            value_num=Decimal("9"),
            value_denom=Decimal("10"),
            date=date(2024, 1, 5),
        )
    ]
    db_port = _build_db_port([currency_row, balances, prices])

    use_case = GetNetWorthSummaryUseCase(db_port=db_port)

    result = use_case.execute()

    assert result.asset_total == Decimal("90.00")
    assert result.liability_total == Decimal("40.25")
    assert result.net_worth == Decimal("49.75")
    assert result.currency_code == "EUR"


def test_execute_applies_date_filters() -> None:
    """Use case should pass date filters to the query."""
    currency_row = [SimpleNamespace(guid="eur-guid")]
    balances = [
        SimpleNamespace(
            account_type="ASSET",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            balance=Decimal("10.00"),
        ),
    ]
    prices = []
    db_port = _build_db_port([currency_row, balances, prices])
    engine = db_port.get_gnucash_engine.return_value

    use_case = GetNetWorthSummaryUseCase(db_port=db_port)

    use_case.execute(start_date=date(2024, 1, 1), end_date=date(2024, 3, 31))

    _, params = engine.connect.return_value.__enter__.return_value.execute.call_args_list[1]
    assert params == {
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 3, 31),
    }
