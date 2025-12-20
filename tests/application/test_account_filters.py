"""Tests for account filtering helpers."""

from src.application.use_cases.account_filters import is_valid_account_name


def test_is_valid_account_name_rejects_empty_or_whitespace() -> None:
    """Empty names should be rejected."""
    assert is_valid_account_name("") is False
    assert is_valid_account_name("   ") is False


def test_is_valid_account_name_rejects_32_char_hex() -> None:
    """Hex-only 32-char names are treated as opaque identifiers."""
    assert is_valid_account_name("552dbab9691b4dadb80cc170009f9cce") is False
    assert is_valid_account_name("B13E492052BF4ACFAF4BD739B1351B5D") is False


def test_is_valid_account_name_accepts_non_hex_or_shorter_values() -> None:
    """Non-hex or non-32-length names are accepted."""
    assert is_valid_account_name("Checking") is True
    assert is_valid_account_name("552dbab9691b4dadb80cc170009f9ccg") is True
    assert is_valid_account_name("deadbeef") is True
