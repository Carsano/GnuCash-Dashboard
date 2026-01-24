"""Regression tests for cashflow SQL currency filtering."""

from datetime import date

from src.infrastructure.analytics_gnucash_repository import AnalyticsGnuCashRepository
from src.infrastructure.analytics_views_repository import AnalyticsViewsRepository


def test_cashflow_query_filters_on_transaction_currency_guid():
    with_currency = AnalyticsViewsRepository._build_cashflow_query(  # noqa: SLF001
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        use_asset_account_guids=False,
        filter_on_transaction_currency_guid=True,
    )
    assert "t.currency_guid = :currency_guid" in with_currency.text
    assert "c.guid = :currency_guid" not in with_currency.text

    without_currency = AnalyticsViewsRepository._build_cashflow_query(  # noqa: SLF001
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        use_asset_account_guids=False,
        filter_on_transaction_currency_guid=False,
    )
    assert "t.currency_guid = :currency_guid" not in without_currency.text


def test_cashflow_query_values_non_currency_accounts_using_split_value():
    query = AnalyticsGnuCashRepository._build_cashflow_query(  # noqa: SLF001
        start_date=None,
        end_date=None,
        use_asset_account_guids=False,
        filter_on_transaction_currency_guid=True,
    )
    assert "t.currency_guid = :currency_guid" in query.text
    assert "s.value_num" in query.text
    assert "quantity_num" not in query.text

    without_currency = AnalyticsGnuCashRepository._build_cashflow_query(  # noqa: SLF001
        start_date=None,
        end_date=None,
        use_asset_account_guids=False,
        filter_on_transaction_currency_guid=False,
    )
    assert "t.currency_guid = :currency_guid" not in without_currency.text
    assert "s.value_num" in without_currency.text
    assert "quantity_num" not in without_currency.text
