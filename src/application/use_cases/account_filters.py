"""Shared account filtering helpers for application use cases."""


_HEX_CHARS = set("0123456789abcdef")


def is_valid_account_name(name: str) -> bool:
    """Return True when the account name is not an opaque hex id.

    Args:
        name: Account name to evaluate.

    Returns:
        bool: True when the name should be retained.
    """
    candidate = name.strip()
    if not candidate:
        return False
    if len(candidate) == 32:
        lowered = candidate.lower()
        if all(char in _HEX_CHARS for char in lowered):
            return False
    return True
