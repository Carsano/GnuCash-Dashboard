"""Tests for the GetAssetCategoryBreakdownUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from src.application.ports.gnucash_repository import (
    AssetCategoryBalanceRow,
    PriceRow,
)
from src.application.use_cases.get_asset_category_breakdown import (
    GetAssetCategoryBreakdownUseCase,
)


def _build_repository(
    *,
    currency_guid: str,
    balances: list[AssetCategoryBalanceRow],
    prices: list[PriceRow],
) -> MagicMock:
    repository = MagicMock()
    repository.fetch_currency_guid.return_value = currency_guid
    repository.fetch_asset_category_balances.return_value = balances
    repository.fetch_latest_prices.return_value = prices
    return repository


def test_execute_returns_category_amounts_in_eur() -> None:
    """Use case should aggregate asset categories and convert to EUR."""
    balances = [
        AssetCategoryBalanceRow(
            account_type="BANK",
            commodity_guid="usd-guid",
            mnemonic="USD",
            namespace="CURRENCY",
            actif_category="Actifs actuels",
            actif_subcategory="Liquidites",
            balance=Decimal("100.00"),
        ),
        AssetCategoryBalanceRow(
            account_type="CASH",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            namespace="CURRENCY",
            actif_category="Actifs actuels",
            actif_subcategory="Liquidites",
            balance=Decimal("20.00"),
        ),
        AssetCategoryBalanceRow(
            account_type="LIABILITY",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            namespace="CURRENCY",
            actif_category=None,
            actif_subcategory=None,
            balance=Decimal("-5.00"),
        ),
        AssetCategoryBalanceRow(
            account_type="STOCK",
            commodity_guid="stock-guid",
            mnemonic="ACME",
            namespace="NASDAQ",
            actif_category="Investissements",
            actif_subcategory="Actions",
            balance=Decimal("2.0"),
        ),
    ]
    prices = [
        PriceRow(
            commodity_guid="usd-guid",
            value_num=Decimal("9"),
            value_denom=Decimal("10"),
            date=date(2024, 1, 5),
        ),
        PriceRow(
            commodity_guid="stock-guid",
            value_num=Decimal("50"),
            value_denom=Decimal("1"),
            date=date(2024, 1, 6),
        ),
    ]
    repository = _build_repository(
        currency_guid="eur-guid",
        balances=balances,
        prices=prices,
    )

    use_case = GetAssetCategoryBreakdownUseCase(
        gnucash_repository=repository
    )

    result = use_case.execute(end_date=date(2024, 1, 10))

    categories = {item.category: item.amount for item in result.categories}
    assert categories == {
        "Actifs actuels": Decimal("110.00"),
        "Investissements": Decimal("100.00"),
    }
    assert result.currency_code == "EUR"


def test_execute_returns_subcategory_amounts_in_eur() -> None:
    """Use case should aggregate asset subcategories when level=2."""
    balances = [
        AssetCategoryBalanceRow(
            account_type="BANK",
            commodity_guid="usd-guid",
            mnemonic="USD",
            namespace="CURRENCY",
            actif_category="Actifs actuels",
            actif_subcategory="Liquidites",
            balance=Decimal("100.00"),
        ),
        AssetCategoryBalanceRow(
            account_type="STOCK",
            commodity_guid="stock-guid",
            mnemonic="ACME",
            namespace="NASDAQ",
            actif_category="Investissements",
            actif_subcategory="Actions",
            balance=Decimal("2.0"),
        ),
    ]
    prices = [
        PriceRow(
            commodity_guid="usd-guid",
            value_num=Decimal("9"),
            value_denom=Decimal("10"),
            date=date(2024, 1, 5),
        ),
        PriceRow(
            commodity_guid="stock-guid",
            value_num=Decimal("50"),
            value_denom=Decimal("1"),
            date=date(2024, 1, 6),
        ),
    ]
    repository = _build_repository(
        currency_guid="eur-guid",
        balances=balances,
        prices=prices,
    )

    use_case = GetAssetCategoryBreakdownUseCase(
        gnucash_repository=repository
    )

    result = use_case.execute(end_date=date(2024, 1, 10), level=2)

    categories = {item.category: item.amount for item in result.categories}
    assert categories == {
        "Actions": Decimal("100.00"),
        "Liquidites": Decimal("90.00"),
    }
