"""Tests for the infrastructure.db module."""

import pytest

from src.infrastructure import db as db_module


def test_get_env_var_reads_environment(monkeypatch):
    """_get_env_var should load .env and return the requested value."""
    monkeypatch.setattr(db_module.dotenv, "load_dotenv", lambda: None)
    monkeypatch.setenv("GNUCASH_DB_URL", "postgresql://example")

    assert db_module._get_env_var("GNUCASH_DB_URL") == "postgresql://example"


def test_get_env_var_raises_when_missing(monkeypatch):
    """Missing env vars should raise a RuntimeError."""
    monkeypatch.setattr(db_module.dotenv, "load_dotenv", lambda: None)
    monkeypatch.delenv("ANALYTICS_DB_URL", raising=False)

    with pytest.raises(RuntimeError):
        db_module._get_env_var("ANALYTICS_DB_URL")


def test_create_engine_passes_pool_configuration(monkeypatch):
    """_create_engine should configure QueuePool with health checks."""
    captured = {}

    def fake_create_engine(db_url, **kwargs):
        captured["db_url"] = db_url
        captured["kwargs"] = kwargs
        return "engine"

    monkeypatch.setattr(db_module, "create_engine", fake_create_engine)

    engine = db_module._create_engine("postgresql://analytics")

    assert engine == "engine"
    assert captured["db_url"] == "postgresql://analytics"
    assert captured["kwargs"]["poolclass"] is db_module.QueuePool
    assert captured["kwargs"]["pool_size"] == 5
    assert captured["kwargs"]["max_overflow"] == 5
    assert captured["kwargs"]["pool_pre_ping"] is True
    assert captured["kwargs"]["future"] is True


def test_get_gnucash_engine_caches_adapter(monkeypatch):
    """get_gnucash_engine should memoize the created engine."""
    db_module._gnucash_engine = None
    created = []

    def fake_create_engine(url):
        created.append(url)
        return f"engine:{url}"

    monkeypatch.setattr(db_module, "_create_engine", fake_create_engine)
    monkeypatch.setattr(db_module.dotenv, "load_dotenv", lambda: None)
    monkeypatch.setenv("GNUCASH_DB_URL", "postgresql://gnucash")

    engine_one = db_module.get_gnucash_engine()
    engine_two = db_module.get_gnucash_engine()

    assert engine_one is engine_two
    assert engine_one == "engine:postgresql://gnucash"
    assert created == ["postgresql://gnucash"]


def test_get_analytics_engine_caches_adapter(monkeypatch):
    """get_analytics_engine should memoize the analytics engine."""
    db_module._analytics_engine = None
    created = []

    def fake_create_engine(url):
        created.append(url)
        return f"engine:{url}"

    monkeypatch.setattr(db_module, "_create_engine", fake_create_engine)
    monkeypatch.setattr(db_module.dotenv, "load_dotenv", lambda: None)
    monkeypatch.setenv("ANALYTICS_DB_URL", "postgresql://analytics")

    engine_one = db_module.get_analytics_engine()
    engine_two = db_module.get_analytics_engine()

    assert engine_one is engine_two
    assert engine_one == "engine:postgresql://analytics"
    assert created == ["postgresql://analytics"]


def test_adapter_returns_underlying_engines(monkeypatch):
    """SqlAlchemyDatabaseEngineAdapter should proxy global helpers."""
    monkeypatch.setattr(
        db_module,
        "get_gnucash_engine",
        lambda: "gnucash_engine",
    )
    monkeypatch.setattr(
        db_module,
        "get_analytics_engine",
        lambda: "analytics_engine",
    )

    adapter = db_module.SqlAlchemyDatabaseEngineAdapter()

    assert adapter.get_gnucash_engine() == "gnucash_engine"
    assert adapter.get_analytics_engine() == "analytics_engine"
