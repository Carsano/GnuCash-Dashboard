"""Serialization helpers for the FastAPI adapter."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def to_api_value(value: Any) -> Any:
    """Convert values to API-safe JSON primitives.

    - Decimal values are serialized as strings.
    - Dataclasses are converted recursively.
    """
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value):
        return to_api_value(asdict(value))
    if isinstance(value, dict):
        return {key: to_api_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_api_value(item) for item in value]
    return value

