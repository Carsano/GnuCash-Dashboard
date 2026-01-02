"""Tests for the GetNetWorthSummaryUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from src.domain.models import NetWorthBalanceRow, PriceRow
from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
)


def _build_repository(
    *,
    currency_guid: str,
    balances: list[NetWorthBalanceRow],
    prices: list[PriceRow],
) -> MagicMock:
    repository = MagicMock()
    repository.fetch_currency_guid.return_value = currency_guid
    repository.fetch_net_worth_balances.return_value = balances
    repository.fetch_latest_prices.return_value = prices
    return repository


def test_execute_returns_summary_totals() -> None:
    """Use case should aggregate assets, liabilities, and net worth."""
    balances = [
        NetWorthBalanceRow(
            account_type="ASSET",
            commodity_guid="usd-guid",
            mnemonic="USD",
            namespace="CURRENCY",
            balance=Decimal("100.00"),
        ),
        NetWorthBalanceRow(
            account_type="LIABILITY",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            namespace="CURRENCY",
            balance=Decimal("-40.25"),
        ),
        NetWorthBalanceRow(
            account_type="INCOME",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            namespace="CURRENCY",
            balance=Decimal("999.00"),
        ),
        NetWorthBalanceRow(
            account_type="STOCK",
            commodity_guid="stock-guid",
            mnemonic="ACME",
            namespace="NASDAQ",
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

    use_case = GetNetWorthSummaryUseCase(
        gnucash_repository=repository
    )

    result = use_case.execute()

    assert result.asset_total == Decimal("190.00")
    assert result.liability_total == Decimal("40.25")
    assert result.net_worth == Decimal("149.75")
    assert result.currency_code == "EUR"


def test_execute_applies_date_filters() -> None:
    """Use case should pass date filters to the query."""
    balances = [
        NetWorthBalanceRow(
            account_type="ASSET",
            commodity_guid="eur-guid",
            mnemonic="EUR",
            namespace="CURRENCY",
            balance=Decimal("10.00"),
        ),
    ]
    prices = []
    repository = _build_repository(
        currency_guid="eur-guid",
        balances=balances,
        prices=prices,
    )

    use_case = GetNetWorthSummaryUseCase(
        gnucash_repository=repository
    )

    start_date = date(2024, 1, 1)
    end_date = date(2024, 3, 31)
    use_case.execute(start_date=start_date, end_date=end_date)

    repository.fetch_net_worth_balances.assert_called_once_with(
        start_date,
        end_date,
    )
    repository.fetch_latest_prices.assert_called_once_with(
        "eur-guid",
        end_date,
    )
