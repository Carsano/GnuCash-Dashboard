"""Tests for the SyncAccountsUseCase."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.application.ports.accounts_sync import AccountRecord
from src.application.use_cases.sync_accounts import SyncAccountsUseCase


def _build_ports(
    accounts: list[AccountRecord],
) -> tuple[MagicMock, MagicMock]:
    """Create configured source/destination ports for the tests."""
    source_port = MagicMock()
    source_port.fetch_accounts.return_value = accounts
    destination_port = MagicMock()
    destination_port.prepare_destination.return_value = None
    destination_port.refresh_accounts.side_effect = (
        lambda records: len(records)
    )
    return source_port, destination_port


def test_run_refreshes_analytics_with_sorted_accounts() -> None:
    """The use case should insert sorted accounts into the analytics table."""
    source_port, destination_port = _build_ports(
        accounts=[
            AccountRecord(
                guid="b",
                name="Savings",
                account_type="BANK",
                commodity_guid="USD",
                parent_guid="ROOT",
            ),
            AccountRecord(
                guid="a",
                name="Checking",
                account_type="BANK",
                commodity_guid="USD",
                parent_guid="ROOT",
            ),
        ]
    )

    use_case = SyncAccountsUseCase(
        source_port=source_port,
        destination_port=destination_port,
    )

    result = use_case.run()

    destination_port.prepare_destination.assert_called_once()
    destination_port.refresh_accounts.assert_called_once()
    passed_accounts = destination_port.refresh_accounts.call_args.args[0]
    assert [acc.guid for acc in passed_accounts] == ["a", "b"]
    assert result.source_count == 2
    assert result.inserted_count == 2


def test_run_handles_empty_source_without_insert() -> None:
    """No insert should happen when the GnuCash source is empty."""
    source_port, destination_port = _build_ports(accounts=[])

    use_case = SyncAccountsUseCase(
        source_port=source_port,
        destination_port=destination_port,
    )

    result = use_case.run()

    destination_port.prepare_destination.assert_called_once()
    destination_port.refresh_accounts.assert_called_once_with([])
    assert result.source_count == 0
    assert result.inserted_count == 0


def test_run_filters_hex_named_accounts() -> None:
    """Accounts with hex-only names should be filtered out."""
    source_port, destination_port = _build_ports(
        accounts=[
            AccountRecord(
                guid="b",
                name="552dbab9691b4dadb80cc170009f9cce",
                account_type="BANK",
                commodity_guid="USD",
                parent_guid="ROOT",
            ),
            AccountRecord(
                guid="c",
                name="Real Account",
                account_type="CASH",
                commodity_guid="USD",
                parent_guid="ROOT",
            ),
            AccountRecord(
                guid="a",
                name="Checking",
                account_type="BANK",
                commodity_guid="USD",
                parent_guid="ROOT",
            ),
        ]
    )

    use_case = SyncAccountsUseCase(
        source_port=source_port,
        destination_port=destination_port,
    )

    result = use_case.run()

    passed_accounts = destination_port.refresh_accounts.call_args.args[0]
    assert [acc.guid for acc in passed_accounts] == ["a", "c"]
    assert result.source_count == 3
    assert result.inserted_count == 2
