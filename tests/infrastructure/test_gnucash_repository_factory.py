"""Tests for GnuCash repository backend selection."""

from pathlib import Path
from unittest.mock import MagicMock

from src.infrastructure import gnucash_repository_factory as factory
from src.infrastructure.gnucash_repository import SqlAlchemyGnuCashRepository
from src.infrastructure.settings import GnuCashSettings


def test_factory_defaults_to_sqlalchemy() -> None:
    """Factory should return SQLAlchemy repository by default."""
    db_port = MagicMock()
    repository = factory.create_gnucash_repository(db_port)
    assert isinstance(repository, SqlAlchemyGnuCashRepository)


def test_factory_uses_piecash_backend(monkeypatch, tmp_path: Path) -> None:
    """Factory should return piecash repository when configured."""
    db_port = MagicMock()
    dummy_repo = object()

    def _fake_repo(path, logger=None):
        assert path == tmp_path
        assert logger is not None
        return dummy_repo

    monkeypatch.setattr(factory, "PieCashGnuCashRepository", _fake_repo)
    settings = GnuCashSettings(backend="piecash", piecash_file=tmp_path)

    repository = factory.create_gnucash_repository(
        db_port,
        settings=settings,
    )

    assert repository is dummy_repo
