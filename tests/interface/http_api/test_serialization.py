"""Tests for HTTP API serialization helpers."""

from dataclasses import dataclass
from decimal import Decimal

from src.adapters.interface.http_api.serialization import to_api_value


@dataclass(frozen=True)
class _Payload:
    amount: Decimal
    nested: dict[str, Decimal]


def test_to_api_value_serializes_decimal_as_string() -> None:
    payload = _Payload(
        amount=Decimal("123.45"),
        nested={"value": Decimal("7.00")},
    )

    result = to_api_value(payload)

    assert result == {"amount": "123.45", "nested": {"value": "7.00"}}

