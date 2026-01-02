"""Contract-style tests for use cases using GnuCashRepositoryPort."""

from datetime import date
from decimal import Decimal

from src.application.ports.gnucash_repository import GnuCashRepositoryPort
from src.domain.models import (
    AssetCategoryBalanceRow,
    NetWorthBalanceRow,
    PriceRow,
)
from src.application.use_cases.get_asset_category_breakdown import (
    GetAssetCategoryBreakdownUseCase,
)
from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
)


class FakeGnuCashRepository(GnuCashRepositoryPort):
    """Fake repository representing a non-SQL backend like piecash."""

    def __init__(
        self,
        currency_guid: str,
        balances: list[NetWorthBalanceRow],
        categories: list[AssetCategoryBalanceRow],
        prices: list[PriceRow],
    ) -> None:
        self._currency_guid = currency_guid
        self._balances = balances
        self._categories = categories
        self._prices = prices

    def fetch_currency_guid(self, currency: str) -> str:
        return self._currency_guid

    def fetch_net_worth_balances(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> list[NetWorthBalanceRow]:
        return list(self._balances)

    def fetch_asset_category_balances(
        self,
        start_date: date | None,
        end_date: date | None,
        actif_root_name: str,
    ) -> list[AssetCategoryBalanceRow]:
        return list(self._categories)

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date: date | None,
    ) -> list[PriceRow]:
        return list(self._prices)


def test_net_worth_use_case_accepts_fake_repository() -> None:
    """Use case should operate with a non-SQL repository."""
    repository = FakeGnuCashRepository(
        currency_guid="eur-guid",
        balances=[
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
                balance=Decimal("-10.00"),
            ),
        ],
        categories=[],
        prices=[
            PriceRow(
                commodity_guid="usd-guid",
                value_num=Decimal("2"),
                value_denom=Decimal("1"),
                date=date(2024, 2, 1),
            ),
        ],
    )

    use_case = GetNetWorthSummaryUseCase(gnucash_repository=repository)
    result = use_case.execute()

    assert result.asset_total == Decimal("200.00")
    assert result.liability_total == Decimal("10.00")
    assert result.net_worth == Decimal("190.00")


def test_asset_breakdown_use_case_accepts_fake_repository() -> None:
    """Use case should operate with a non-SQL repository."""
    repository = FakeGnuCashRepository(
        currency_guid="eur-guid",
        balances=[],
        categories=[
            AssetCategoryBalanceRow(
                account_type="ASSET",
                commodity_guid="eur-guid",
                mnemonic="EUR",
                namespace="CURRENCY",
                actif_category="Liquid",
                actif_subcategory="Cash",
                balance=Decimal("50.00"),
            ),
            AssetCategoryBalanceRow(
                account_type="ASSET",
                commodity_guid="usd-guid",
                mnemonic="USD",
                namespace="CURRENCY",
                actif_category="Liquid",
                actif_subcategory="Broker",
                balance=Decimal("25.00"),
            ),
        ],
        prices=[
            PriceRow(
                commodity_guid="usd-guid",
                value_num=Decimal("2"),
                value_denom=Decimal("1"),
                date=date(2024, 2, 1),
            ),
        ],
    )

    use_case = GetAssetCategoryBreakdownUseCase(
        gnucash_repository=repository
    )
    result = use_case.execute(level=2)

    labels = [entry.category for entry in result.categories]
    assert labels == ["Broker", "Cash"]
    amounts = [entry.amount for entry in result.categories]
    assert amounts == [Decimal("50.00"), Decimal("50.00")]
