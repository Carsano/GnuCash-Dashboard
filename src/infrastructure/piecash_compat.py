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
    open_book = piecash.open_book
    kwargs = {
        "sqlite_file": sqlite_file,
        "uri_conn": uri,
        "readonly": readonly,
        "open_if_lock": open_if_lock,
        "check_exists": check_exists,
    }
    try:
        signature = inspect.signature(open_book)
    except (TypeError, ValueError):
        signature = None

    if signature is not None:
        params = signature.parameters
        accepts_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in params.values()
        )
        if accepts_kwargs or "sqlite_file" in params or "uri_conn" in params:
            return open_book(**kwargs)
        path_value = sqlite_file or uri
        if path_value is None:
            path_value = str(book_path)
        passthrough = {
            name: value
            for name, value in (
                ("readonly", readonly),
                ("open_if_lock", open_if_lock),
                ("check_exists", check_exists),
            )
            if name in params
        }
        if "path" in params:
            return open_book(path=path_value, **passthrough)
        return open_book(path_value, **passthrough)

    try:
        return open_book(**kwargs)
    except TypeError:
        path_value = sqlite_file or uri or str(book_path)
        return open_book(path_value, readonly, open_if_lock, check_exists)


__all__ = ["load_piecash", "open_piecash_book"]
