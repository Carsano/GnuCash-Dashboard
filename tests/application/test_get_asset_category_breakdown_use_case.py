"""Tests for the GetAssetCategoryBreakdownUseCase."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.application.use_cases.get_asset_category_breakdown import (
    GetAssetCategoryBreakdownUseCase,
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


def test_execute_returns_category_amounts_in_eur() -> None:
    """Use case should aggregate asset categories and convert to EUR."""
    currency_row = [SimpleNamespace(guid="eur-guid")]
    balances = [
        SimpleNamespace(
            account_type="BANK",
            commodity_guid="usd-guid",
            mnemonic="USD",
            namespace="CURRENCY",
            actif_category="Actifs actuels",
            balance=Decimal("100.00"),
        ),
        SimpleNamespace(
            account_type="CASH",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            namespace="CURRENCY",
            actif_category="Actifs actuels",
            balance=Decimal("20.00"),
        ),
        SimpleNamespace(
            account_type="LIABILITY",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            namespace="CURRENCY",
            actif_category=None,
            balance=Decimal("-5.00"),
        ),
        SimpleNamespace(
            account_type="STOCK",
            commodity_guid="stock-guid",
            mnemonic="ACME",
            namespace="NASDAQ",
            actif_category="Investissements",
            balance=Decimal("2.0"),
        ),
    ]
    prices = [
        SimpleNamespace(
            commodity_guid="usd-guid",
            value_num=Decimal("9"),
            value_denom=Decimal("10"),
            date=date(2024, 1, 5),
        ),
        SimpleNamespace(
            commodity_guid="stock-guid",
            value_num=Decimal("50"),
            value_denom=Decimal("1"),
            date=date(2024, 1, 6),
        ),
    ]
    db_port = _build_db_port([currency_row, balances, prices])

    use_case = GetAssetCategoryBreakdownUseCase(db_port=db_port)

    result = use_case.execute(end_date=date(2024, 1, 10))

    categories = {item.category: item.amount for item in result.categories}
    assert categories == {
        "Actifs actuels": Decimal("110.00"),
        "Investissements": Decimal("100.00"),
    }
    assert result.currency_code == "EUR"
