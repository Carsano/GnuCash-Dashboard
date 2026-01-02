"""Settings helpers for infrastructure adapters."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from src.infrastructure.logging.logger import get_app_logger
from src.utils.utils import get_project_root


@dataclass(frozen=True)
class GnuCashSettings:
    """Settings for selecting the GnuCash backend.

    Attributes:
        backend: Backend identifier (sqlalchemy, analytics, or piecash).
        piecash_file: Optional path or URI to the piecash book.
    """

    backend: str = "sqlalchemy"
    piecash_file: Optional[Path | str] = None

    @classmethod
    def from_env(cls) -> "GnuCashSettings":
        """Build settings from environment variables.

        Returns:
            GnuCashSettings: Settings sourced from environment variables.
        """
        backend = os.getenv("GNUCASH_BACKEND", "sqlalchemy").strip().lower()
        raw_piecash = os.getenv("PIECASH_FILE")
        logger = get_app_logger()
        piecash_file = None
        if raw_piecash:
            piecash_file = cls._normalize_path(raw_piecash, logger=logger)
        else:
            piecash_file = cls._default_piecash_file(logger=logger)
        return cls(backend=backend, piecash_file=piecash_file)

    @staticmethod
    def _normalize_path(
        raw_path: str,
        logger,
    ) -> Path | str:
        """Normalize the piecash file path or URI.

        Args:
            raw_path: Raw file path string.
            logger: Logger used for warnings.

        Returns:
            Path | str: Normalized filesystem path or URI string.
        """
        parsed = urlparse(raw_path)
        if parsed.scheme and parsed.scheme != "file":
            return raw_path
        if parsed.scheme == "file":
            raw_path = unquote(parsed.path)
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            logger.warning(f"PieCash file does not exist at {path}")
        return path

    @staticmethod
    def _default_piecash_file(logger) -> Path | None:
        """Return a default piecash book path when available.

        Args:
            logger: Logger used for warnings.

        Returns:
            Path | None: Default path if a single book is found in data/.
        """
        data_dir = get_project_root() / "data"
        if not data_dir.exists():
            return None
        matches = sorted(data_dir.glob("*.gnucash"))
        if len(matches) == 1:
            return matches[0].resolve()
        if len(matches) > 1:
            logger.warning(
                "Multiple .gnucash files found in data/. "
                "Set PIECASH_FILE to choose one."
            )
        return None


__all__ = ["GnuCashSettings"]
