"""Tests for the GetCashflowUseCase."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from src.application.use_cases.get_cashflow import GetCashflowUseCase
from src.domain.models import CashflowRow


def test_execute_aggregates_rows_and_preserves_order() -> None:
    """Use case should aggregate rows without reordering them."""
    rows = [
        CashflowRow(
            account_guid="income-guid",
            account_full_name="Revenus:Salaire",
            top_parent_name="Revenus",
            amount=Decimal("100.00"),
        ),
        CashflowRow(
            account_guid="expense-guid",
            account_full_name="Depenses:Courses",
            top_parent_name="Depenses",
            amount=Decimal("-40.00"),
        ),
        CashflowRow(
            account_guid="income-guid",
            account_full_name="Revenus:Salaire",
            top_parent_name="Revenus",
            amount=Decimal("50.00"),
        ),
        CashflowRow(
            account_guid="liability-guid",
            account_full_name="Passif:Credit",
            top_parent_name="Passif",
            amount=Decimal("-10.00"),
        ),
    ]
    repository = MagicMock()
    repository.fetch_currency_guid.return_value = "eur-guid"
    repository.fetch_cashflow_rows.return_value = rows

    use_case = GetCashflowUseCase(gnucash_repository=repository)

    result = use_case.execute(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    assert result.summary.total_in == Decimal("150.00")
    assert result.summary.total_out == Decimal("50.00")
    assert result.summary.difference == Decimal("100.00")
    assert [item.account_full_name for item in result.incoming] == [
        "Revenus:Salaire",
    ]
    assert [item.amount for item in result.incoming] == [
        Decimal("150.00"),
    ]
    assert [item.amount for item in result.outgoing] == [
        Decimal("40.00"),
        Decimal("10.00"),
    ]
    assert result.outgoing[0].top_parent_name == "Depenses"
    repository.fetch_cashflow_rows.assert_called_once_with(
        date(2024, 1, 1),
        date(2024, 1, 31),
        asset_root_name="Actif",
        currency_guid="eur-guid",
        asset_account_guids=None,
    )
