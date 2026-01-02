"""Compatibility helpers for importing piecash."""

from __future__ import annotations

import inspect
import warnings
from pathlib import Path
from urllib.parse import urlparse

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


def open_piecash_book(
    piecash,
    book_path: Path | str,
    *,
    readonly: bool = True,
    open_if_lock: bool = True,
    check_exists: bool = False,
):
    """Open a piecash book from a filesystem path or URI."""
    uri: str | None = None
    sqlite_file: str | None = None
    if isinstance(book_path, Path):
        sqlite_file = str(book_path)
    else:
        parsed = urlparse(book_path)
        if parsed.scheme and parsed.scheme != "file":
            uri = book_path
        else:
            sqlite_file = str(Path(book_path).expanduser().resolve())
    return piecash.open_book(
        sqlite_file=sqlite_file,
        uri_conn=uri,
        readonly=readonly,
        open_if_lock=open_if_lock,
        check_exists=check_exists,
    )


__all__ = ["load_piecash", "open_piecash_book"]
