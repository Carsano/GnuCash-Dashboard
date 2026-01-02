"""Tests for piecash compatibility helpers."""

from pathlib import Path

from src.infrastructure import piecash_compat


class _FakePiecash:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, object] = {}

    def open_book(self, **kwargs):
        self.last_kwargs = kwargs
        return object()


def test_open_piecash_book_with_uri() -> None:
    """URI inputs should be routed through uri_conn."""
    fake = _FakePiecash()
    uri = "postgresql://user:pass@host/dbname"

    piecash_compat.open_piecash_book(fake, uri)

    assert fake.last_kwargs["uri_conn"] == uri
    assert fake.last_kwargs["sqlite_file"] is None


def test_open_piecash_book_with_path(tmp_path: Path) -> None:
    """Path inputs should be routed through sqlite_file."""
    fake = _FakePiecash()

    piecash_compat.open_piecash_book(fake, tmp_path)

    assert fake.last_kwargs["sqlite_file"] == str(tmp_path)
    assert fake.last_kwargs["uri_conn"] is None
