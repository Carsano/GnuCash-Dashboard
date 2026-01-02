"""Tests for infrastructure settings."""

from pathlib import Path

from src.infrastructure.settings import GnuCashSettings


def test_from_env_uses_file_path(monkeypatch, tmp_path: Path) -> None:
    """File paths should resolve to Path instances."""
    monkeypatch.setenv("PIECASH_FILE", str(tmp_path))

    settings = GnuCashSettings.from_env()

    assert isinstance(settings.piecash_file, Path)
    assert settings.piecash_file == tmp_path.resolve()


def test_from_env_allows_uri(monkeypatch) -> None:
    """URI values should pass through unchanged."""
    uri = "postgresql://user:pass@host/dbname"
    monkeypatch.setenv("PIECASH_FILE", uri)

    settings = GnuCashSettings.from_env()

    assert settings.piecash_file == uri
