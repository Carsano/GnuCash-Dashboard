"""Tests for the CompareBackendsUseCase."""

from decimal import Decimal

from src.application.ports.gnucash_repository import (
    AssetCategoryBalanceRow,
    NetWorthBalanceRow,
    PriceRow,
)
from src.application.use_cases.compare_backends import (
    CompareBackendsUseCase,
)


class _FakeRepository:
    def __init__(
        self,
        currency_guid: str,
        balances: list[NetWorthBalanceRow],
        prices: list[PriceRow],
    ) -> None:
        self._currency_guid = currency_guid
        self._balances = balances
        self._prices = prices

    def fetch_currency_guid(self, currency: str) -> str:
        return self._currency_guid

    def fetch_net_worth_balances(
        self,
        start_date=None,
        end_date=None,
    ) -> list[NetWorthBalanceRow]:
        return list(self._balances)

    def fetch_asset_category_balances(
        self,
        start_date,
        end_date,
        actif_root_name: str,
    ) -> list[AssetCategoryBalanceRow]:
        return []

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date=None,
    ) -> list[PriceRow]:
        return list(self._prices)


def test_execute_returns_counts_and_deltas() -> None:
    """Use case should compare counts and totals."""
    left_repo = _FakeRepository(
        currency_guid="eur-guid",
        balances=[
            NetWorthBalanceRow(
                account_type="ASSET",
                commodity_guid="eur-guid",
                mnemonic="EUR",
                namespace="CURRENCY",
                balance=Decimal("100.00"),
            ),
            NetWorthBalanceRow(
                account_type="LIABILITY",
                commodity_guid="eur-guid",
                mnemonic="EUR",
                namespace="CURRENCY",
                balance=Decimal("-20.00"),
            ),
        ],
        prices=[],
    )
    right_repo = _FakeRepository(
        currency_guid="eur-guid",
        balances=[
            NetWorthBalanceRow(
                account_type="ASSET",
                commodity_guid="eur-guid",
                mnemonic="EUR",
                namespace="CURRENCY",
                balance=Decimal("110.00"),
            ),
            NetWorthBalanceRow(
                account_type="LIABILITY",
                commodity_guid="eur-guid",
                mnemonic="EUR",
                namespace="CURRENCY",
                balance=Decimal("-25.00"),
            ),
        ],
        prices=[],
    )

    use_case = CompareBackendsUseCase(left_repo, right_repo)

    result = use_case.execute(target_currency="EUR")

    assert result.left.balance_count == 2
    assert result.right.balance_count == 2
    assert result.left.net_worth == Decimal("80.00")
    assert result.right.net_worth == Decimal("85.00")
    assert result.diff.net_worth_delta == Decimal("5.00")
    assert result.diff.asset_delta == Decimal("10.00")
    assert result.diff.liability_delta == Decimal("5.00")
