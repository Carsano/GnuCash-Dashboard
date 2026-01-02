"""Tests for the PieCashAccountsSource adapter."""

from types import SimpleNamespace

from src.infrastructure import accounts_sync
from src.infrastructure.accounts_sync import PieCashAccountsSource


def test_fetch_accounts_reads_book(monkeypatch, tmp_path):
    """Adapter should load accounts from the piecash book."""
    close_called = {"value": False}

    class _Account:
        def __init__(self, guid, name, account_type, commodity, parent=None):
            self.guid = guid
            self.name = name
            self.type = account_type
            self.commodity = commodity
            self.parent = parent

    class _Book:
        def __init__(self):
            commodity = SimpleNamespace(guid="USD")
            parent = _Account("a", "Root", "ROOT", None)
            self.accounts = [
                _Account("b", "Child", "BANK", commodity, parent),
                parent,
            ]

        def close(self):
            close_called["value"] = True

    def _open_book(path, readonly=True, open_if_lock=True, check_exists=False):
        assert path == str(tmp_path)
        assert readonly is True
        assert open_if_lock is True
        assert check_exists is False
        return _Book()

    monkeypatch.setattr(
        accounts_sync,
        "load_piecash",
        lambda: SimpleNamespace(open_book=_open_book),
    )

    source = PieCashAccountsSource(tmp_path)
    records = source.fetch_accounts()

    assert [record.guid for record in records] == ["a", "b"]
    assert close_called["value"] is True
