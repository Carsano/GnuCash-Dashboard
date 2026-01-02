"""Compatibility helpers for importing piecash."""

from __future__ import annotations

import inspect
import warnings

from sqlalchemy.exc import SAWarning

_PIECASH = None


def _patch_sqlalchemy_for_piecash() -> None:
    """Patch SQLAlchemy for piecash compatibility when needed."""
    try:
        from sqlalchemy.orm import decl_api
    except Exception:
        return

    signature = inspect.signature(decl_api.registry.generate_base)
    if "constructor" in signature.parameters:
        return

    original = decl_api.registry.generate_base
    if getattr(original, "_piecash_patched", False):
        return

    def _generate_base(self, *args, **kwargs):
        kwargs.pop("constructor", None)
        return original(self, *args, **kwargs)

    _generate_base._piecash_patched = True  # type: ignore[attr-defined]
    decl_api.registry.generate_base = _generate_base


def load_piecash():
    """Import piecash with compatibility patches applied."""
    global _PIECASH
    if _PIECASH is not None:
        return _PIECASH
    _patch_sqlalchemy_for_piecash()
    warnings.filterwarnings(
        "ignore",
        category=SAWarning,
    )
    import piecash  # noqa: F401

    _PIECASH = piecash
    return piecash


__all__ = ["load_piecash"]
