"""Tests for analytics repository selection."""

from unittest.mock import MagicMock

from src.infrastructure.container import build_analytics_repository
from src.infrastructure.analytics_gnucash_repository import (
    AnalyticsGnuCashRepository,
)
from src.infrastructure.analytics_views_repository import (
    AnalyticsViewsRepository,
)


def test_build_analytics_repository_defaults_to_tables() -> None:
    """Default selection should use table-backed repository."""
    db_port = MagicMock()

    repository = build_analytics_repository(db_port=db_port)

    assert isinstance(repository, AnalyticsGnuCashRepository)


def test_build_analytics_repository_uses_views(monkeypatch) -> None:
    """Selection should honor the views mode."""
    db_port = MagicMock()
    monkeypatch.setenv("ANALYTICS_READ_MODE", "views")

    repository = build_analytics_repository(db_port=db_port)

    assert isinstance(repository, AnalyticsViewsRepository)
