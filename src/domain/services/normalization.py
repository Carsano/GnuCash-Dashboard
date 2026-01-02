"""Domain normalization helpers."""


def normalize_namespace(namespace: str | None) -> str | None:
    """Normalize commodity namespace values.

    Args:
        namespace: Raw namespace value from a repository.

    Returns:
        str | None: Normalized namespace value.
    """
    if not namespace:
        return None
    cleaned = namespace.strip()
    return cleaned.upper() if cleaned else None


def normalize_mnemonic(mnemonic: str | None) -> str | None:
    """Normalize commodity mnemonic values.

    Args:
        mnemonic: Raw mnemonic value from a repository.

    Returns:
        str | None: Normalized mnemonic value.
    """
    if not mnemonic:
        return None
    cleaned = mnemonic.strip()
    return cleaned.upper() if cleaned else None


__all__ = ["normalize_namespace", "normalize_mnemonic"]
