"""Helpers to classify GnuCash accounts into business steering categories."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import re
import unicodedata
from typing import Any, Iterable, Mapping


BUSINESS_CATEGORIES = (
    "Immobilier",
    "Livrets",
    "Actions & Fonds",
    "Comptes Bancaires",
    "Crypto",
    "Autres",
)


@dataclass(frozen=True)
class AccountCategoryRuleSet:
    """Centralized explicit account name mapping by business category."""

    immobilier: frozenset[str]
    livrets: frozenset[str]
    actions_fonds: frozenset[str]
    comptes_bancaires: frozenset[str]
    crypto: frozenset[str]


def _normalize_text(value: str) -> str:
    """Normalize text for robust name matching.

    The normalization intentionally:
    - strips accents;
    - normalizes apostrophes and punctuation;
    - collapses whitespace;
    - lowercases with ``casefold``.
    """
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    lowered = without_accents.casefold()
    lowered = lowered.replace("’", "'").replace("`", "'")
    lowered = lowered.replace("&", " & ")
    lowered = re.sub(r"[/_:-]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


RULES = AccountCategoryRuleSet(
    immobilier=frozenset(
        _normalize_text(name)
        for name in (
            "Parking Chemin Fried",
            "Villevieux",
            "Maison",
            "Immobilier",
        )
    ),
    livrets=frozenset(
        _normalize_text(name)
        for name in (
            "LDD",
            "Livret Bleu",
            "Compte d'épargne",
        )
    ),
    actions_fonds=frozenset(
        _normalize_text(name)
        for name in (
            "Apple",
            "Palantir",
            "S&P 500",
            "Air Liquide",
            "AM MSCI WORLD",
            "AM MSCI EM",
            "AM NASDAQ",
            "BNP S&P 500",
            "IND ET EXP EUROPE",
            "LVMH",
            "Total Energie",
            "IS MSCI WORLD",
            "Private Equity",
            "CTO",
            "PEA",
            "Compte de bourse/titre",
            "Investissements",
            "PER Swisslife",
            "PER Gédéon",
            "PER Amundi",
            "AV Cédit Mutuel",
            "AV Swisslife",
            "AV Linxea",
            "Assurances Vie",
            "Retraite",
            "PEG Schmidt",
        )
    ),
    comptes_bancaires=frozenset(
        _normalize_text(name)
        for name in (
            "Crédit Mutuel",
            "Revolut",
            "Revolut Pro",
            "Compte Liquidités PEA",
            "CD bancaire",
            "Non soldé-EUR",
            "Orphelin-EUR",
            "Espèces Trade Republic",
            "Argent du porte-monnaie",
        )
    ),
    crypto=frozenset(
        _normalize_text(name)
        for name in (
            "Crypto.com Invest",
            "Binance",
            "Exodus",
            "Crypto Cash",
            "Crypto Card",
            "Cryptomonnaies",
        )
    ),
)

_IMMOBILIER_KEYWORDS = tuple(
    _normalize_text(value)
    for value in ("immobilier", "maison", "parking")
)
_LIVRET_KEYWORDS = tuple(
    _normalize_text(value)
    for value in ("livret", "epargne")
)
_CRYPTO_KEYWORDS = tuple(
    _normalize_text(value)
    for value in ("crypto", "bitcoin", "ethereum", "btc", "eth")
)


def categorize_account(name: str, account_type: str) -> str:
    """Return the business category for a single GnuCash account.

    The classification is intentionally driven by explicit name mapping first.
    A small set of robust secondary rules is applied only for obvious cases.

    Args:
        name: Raw account name.
        account_type: Raw GnuCash account type.

    Returns:
        One of the supported business categories.
    """
    normalized_name = _normalize_text(name)
    _ = account_type.strip().upper()

    if normalized_name in RULES.immobilier:
        return "Immobilier"
    if normalized_name in RULES.livrets:
        return "Livrets"
    if normalized_name in RULES.actions_fonds:
        return "Actions & Fonds"
    if normalized_name in RULES.comptes_bancaires:
        return "Comptes Bancaires"
    if normalized_name in RULES.crypto:
        return "Crypto"

    if any(keyword in normalized_name for keyword in _CRYPTO_KEYWORDS):
        return "Crypto"
    if any(keyword in normalized_name for keyword in _IMMOBILIER_KEYWORDS):
        return "Immobilier"
    if any(keyword in normalized_name for keyword in _LIVRET_KEYWORDS):
        return "Livrets"

    return "Autres"


def _account_to_dict(account: Mapping[str, Any] | Any) -> dict[str, Any]:
    """Convert an account object to a plain dictionary."""
    if isinstance(account, Mapping):
        return dict(account)
    if is_dataclass(account):
        return asdict(account)
    raise TypeError(
        "Each account must be a mapping or a dataclass instance."
    )


def categorize_accounts(
    accounts: Iterable[Mapping[str, Any] | Any],
) -> list[dict[str, Any]]:
    """Enrich accounts with a business category.

    Args:
        accounts: Iterable of account dictionaries or dataclass instances.

    Returns:
        A new list of dictionaries containing the original fields plus
        ``business_category``.
    """
    enriched_accounts: list[dict[str, Any]] = []
    for account in accounts:
        item = _account_to_dict(account)
        name = str(item.get("name", ""))
        account_type = str(item.get("account_type", ""))
        enriched_accounts.append(
            {
                **item,
                "business_category": categorize_account(
                    name=name,
                    account_type=account_type,
                ),
            }
        )
    return enriched_accounts


def categorize_accounts_to_dataframe(
    accounts: Iterable[Mapping[str, Any] | Any],
):
    """Return a pandas DataFrame with the enriched account categories.

    Raises:
        ImportError: If pandas is not installed in the current environment.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - depends on optional install
        raise ImportError(
            "pandas is required for DataFrame output. "
            "Install it with `uv add pandas`."
        ) from exc

    return pd.DataFrame(categorize_accounts(accounts))


EXAMPLE_ACCOUNTS = [
    {"guid": "1", "name": "Apple", "account_type": "STOCK"},
    {"guid": "2", "name": "Crédit Mutuel", "account_type": "BANK"},
    {"guid": "3", "name": "Maison", "account_type": "ASSET"},
    {"guid": "4", "name": "Binance", "account_type": "ASSET"},
    {"guid": "5", "name": "Créances", "account_type": "ASSET"},
]


if __name__ == "__main__":  # pragma: no cover
    for account in categorize_accounts(EXAMPLE_ACCOUNTS):
        print(account)
