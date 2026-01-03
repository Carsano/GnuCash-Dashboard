"""Tests for the PieCashGnuCashRepository adapter."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from src.infrastructure import piecash_repository
from src.infrastructure.piecash_repository import PieCashGnuCashRepository


def test_fetch_currency_guid_reads_commodities(monkeypatch, tmp_path):
    """Repository should return matching currency GUID."""
    close_called = {"value": False}

    class _Book:
        def __init__(self):
            self.commodities = [
                SimpleNamespace(
                    guid="eur-guid",
                    mnemonic="EUR",
                    namespace="CURRENCY",
                )
            ]
            self.splits = []
            self.prices = []

        def close(self):
            close_called["value"] = True

    def _open_book(path, readonly=True, open_if_lock=True, check_exists=False):
        assert path == str(tmp_path)
        return _Book()

    monkeypatch.setattr(
        piecash_repository,
        "load_piecash",
        lambda: SimpleNamespace(open_book=_open_book),
    )

    repository = PieCashGnuCashRepository(tmp_path)
    result = repository.fetch_currency_guid("EUR")

    assert result == "eur-guid"
    assert close_called["value"] is True


def test_fetch_net_worth_balances_aggregates_splits(monkeypatch, tmp_path):
    """Repository should aggregate split balances per account type."""
    class _Numeric:
        def __init__(self, num, denom):
            self.num = num
            self.denom = denom

    class _Transaction:
        def __init__(self, post_date):
            self.post_date = post_date

    class _Account:
        def __init__(self, guid, name, account_type, commodity):
            self.guid = guid
            self.name = name
            self.type = account_type
            self.commodity = commodity

    class _Split:
        def __init__(self, account, transaction, value):
            self.account = account
            self.transaction = transaction
            self.value = value

    class _Book:
        def __init__(self):
            commodity = SimpleNamespace(
                guid="eur-guid",
                mnemonic="EUR",
                namespace="CURRENCY",
            )
            account = _Account("a", "Cash", "ASSET", commodity)
            self.commodities = [commodity]
            self.splits = [
                _Split(
                    account=account,
                    transaction=_Transaction(date(2024, 1, 2)),
                    value=_Numeric(100, 1),
                ),
            ]
            self.prices = []

        def close(self):
            return None

    def _open_book(path, readonly=True, open_if_lock=True, check_exists=False):
        return _Book()

    monkeypatch.setattr(
        piecash_repository,
        "load_piecash",
        lambda: SimpleNamespace(open_book=_open_book),
    )

    repository = PieCashGnuCashRepository(tmp_path)
    rows = repository.fetch_net_worth_balances(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    assert len(rows) == 1
    assert rows[0].balance == Decimal("100")


def test_fetch_latest_prices_filters_currency(monkeypatch, tmp_path):
    """Repository should filter prices by currency GUID."""
    close_called = {"value": False}

    class _Book:
        def __init__(self):
            self.commodities = []
            self.splits = []
            self.prices = [
                SimpleNamespace(
                    commodity=SimpleNamespace(guid="usd-guid"),
                    currency=SimpleNamespace(guid="eur-guid"),
                    date=date(2024, 2, 1),
                    value_num=Decimal("10"),
                    value_denom=Decimal("1"),
                ),
                SimpleNamespace(
                    commodity=SimpleNamespace(guid="gbp-guid"),
                    currency=SimpleNamespace(guid="gbp-currency"),
                    date=date(2024, 2, 2),
                    value_num=Decimal("1"),
                    value_denom=Decimal("1"),
                ),
            ]

        def close(self):
            close_called["value"] = True

    def _open_book(path, readonly=True, open_if_lock=True, check_exists=False):
        return _Book()

    monkeypatch.setattr(
        piecash_repository,
        "load_piecash",
        lambda: SimpleNamespace(open_book=_open_book),
    )

    repository = PieCashGnuCashRepository(tmp_path)
    rows = repository.fetch_latest_prices("eur-guid", end_date=None)

    assert len(rows) == 1
    assert rows[0].commodity_guid == "usd-guid"
    assert close_called["value"] is True
