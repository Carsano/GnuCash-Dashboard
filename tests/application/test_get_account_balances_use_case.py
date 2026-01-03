"""Tests for the GetAccountBalancesUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from src.application.use_cases.get_account_balances import (
    GetAccountBalancesUseCase,
)
from src.domain.models import AccountBalanceRow, PriceRow


def _build_repository(
    *,
    currency_guid: str,
    balances: list[AccountBalanceRow],
    prices: list[PriceRow],
) -> MagicMock:
    repository = MagicMock()
    repository.fetch_currency_guid.return_value = currency_guid
    repository.fetch_account_balances.return_value = balances
    repository.fetch_latest_prices.return_value = prices
    return repository


def test_execute_returns_sorted_balances_with_conversions() -> None:
    """Use case should convert balances and sort by account name."""
    balances = [
        AccountBalanceRow(
            guid="b",
            name="Savings",
            account_type="BANK",
            commodity_guid="usd-guid",
            parent_guid=None,
            mnemonic="USD",
            namespace="CURRENCY",
            balance=Decimal("10.00"),
        ),
        AccountBalanceRow(
            guid="d",
            name="Loan",
            account_type="LIABILITY",
            commodity_guid="eur-guid",
            parent_guid=None,
            mnemonic="EUR",
            namespace="CURRENCY",
            balance=Decimal("-40.00"),
        ),
        AccountBalanceRow(
            guid="a",
            name="Checking",
            account_type="BANK",
            commodity_guid="eur-guid",
            parent_guid=None,
            mnemonic="EUR",
            namespace="CURRENCY",
            balance=Decimal("100.00"),
        ),
        AccountBalanceRow(
            guid="c",
            name="Broker",
            account_type="STOCK",
            commodity_guid="stock-guid",
            parent_guid=None,
            mnemonic="ACME",
            namespace="NASDAQ",
            balance=Decimal("2"),
        ),
    ]
    prices = [
        PriceRow(
            commodity_guid="usd-guid",
            value_num=Decimal("9"),
            value_denom=Decimal("10"),
            date=date(2024, 2, 1),
        )
    ]
    repository = _build_repository(
        currency_guid="eur-guid",
        balances=balances,
        prices=prices,
    )

    use_case = GetAccountBalancesUseCase(
        gnucash_repository=repository
    )

    result = use_case.execute(end_date=date(2024, 2, 15))

    assert [item.name for item in result] == [
        "Checking",
        "Loan",
        "Savings",
    ]
    assert result[0].balance == Decimal("100.00")
    assert result[1].balance == Decimal("40.00")
    assert result[2].balance == Decimal("9.00")
    repository.fetch_account_balances.assert_called_once_with(
        date(2024, 2, 15)
    )
    repository.fetch_latest_prices.assert_called_once_with(
        "eur-guid",
        date(2024, 2, 15),
    )
