"""Ensure interface adapter packages expose the expected metadata."""

from importlib import import_module


def test_interface_package_exports_are_empty() -> None:
    module = import_module("src.adapters.interface")
    assert module.__all__ == []


def test_streamlit_package_exports_are_empty() -> None:
    module = import_module("src.adapters.interface.streamlit")
    assert module.__all__ == []
