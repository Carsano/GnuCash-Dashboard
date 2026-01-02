"""Tests for Streamlit Altair dependency checks."""

import sys
import types

from src.adapters.interface.streamlit import app


def test_check_altair_dependencies_ok(monkeypatch) -> None:
    """Return ok when numpy/pandas expose expected attributes."""
    fake_numpy = types.SimpleNamespace(ndarray=object)
    fake_pandas = types.SimpleNamespace(Timestamp=object)
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "pandas", fake_pandas)

    ok, message = app._check_altair_dependencies()

    assert ok is True
    assert message is None


def test_check_altair_dependencies_missing_numpy_ndarray(
    monkeypatch,
) -> None:
    """Return error when numpy import is incomplete."""
    fake_numpy = types.SimpleNamespace()
    fake_pandas = types.SimpleNamespace(Timestamp=object)
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "pandas", fake_pandas)

    ok, message = app._check_altair_dependencies()

    assert ok is False
    assert message is not None
    assert "numpy" in message


def test_check_altair_dependencies_missing_pandas_timestamp(
    monkeypatch,
) -> None:
    """Return error when pandas import is incomplete."""
    fake_numpy = types.SimpleNamespace(ndarray=object)
    fake_pandas = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "pandas", fake_pandas)

    ok, message = app._check_altair_dependencies()

    assert ok is False
    assert message is not None
    assert "pandas" in message
