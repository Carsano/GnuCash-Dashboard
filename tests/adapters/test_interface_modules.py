"""Ensure interface adapter packages expose the expected metadata."""

from importlib import import_module


def test_interface_package_exports_are_empty() -> None:
    module = import_module("src.adapters.interface")
    assert module.__all__ == []
