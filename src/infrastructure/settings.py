"""Settings helpers for infrastructure adapters."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

from src.infrastructure.logging.logger import get_app_logger


@dataclass(frozen=True)
class GnuCashSettings:
    """Settings for selecting the GnuCash backend.

    Attributes:
        backend: Backend identifier (sqlalchemy or piecash).
        piecash_file: Optional path to the piecash book file.
    """

    backend: str = "sqlalchemy"
    piecash_file: Optional[Path] = None

    @classmethod
    def from_env(cls) -> "GnuCashSettings":
        """Build settings from environment variables.

        Returns:
            GnuCashSettings: Settings sourced from environment variables.
        """
        backend = os.getenv("GNUCASH_BACKEND", "sqlalchemy").strip().lower()
        raw_piecash = os.getenv("PIECASH_FILE")
        piecash_file = (
            cls._normalize_path(raw_piecash, logger=get_app_logger())
            if raw_piecash
            else None
        )
        return cls(backend=backend, piecash_file=piecash_file)

    @staticmethod
    def _normalize_path(
        raw_path: str,
        logger,
    ) -> Path:
        """Normalize the piecash file path.

        Args:
            raw_path: Raw file path string.
            logger: Logger used for warnings.

        Returns:
            Path: Normalized path.
        """
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            logger.warning(f"PieCash file does not exist at {path}")
        return path


__all__ = ["GnuCashSettings"]
