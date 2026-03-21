"""Tests for account categorization helpers."""

from dataclasses import dataclass

from src.domain.services.account_categorization import (
    categorize_account,
    categorize_accounts,
)


@dataclass(frozen=True)
class _Account:
    guid: str
    name: str
    account_type: str


def test_categorize_account_uses_explicit_mapping() -> None:
    assert categorize_account("Apple", "STOCK") == "Actions & Fonds"
    assert categorize_account("Maison", "ASSET") == "Immobilier"
    assert categorize_account("Crédit Mutuel", "BANK") == "Comptes Bancaires"
    assert categorize_account("Binance", "ASSET") == "Crypto"
    assert categorize_account("LDD", "ASSET") == "Livrets"
    assert categorize_account("PER Swisslife", "ASSET") == "Actions & Fonds"
    assert categorize_account("AV Linxea", "ASSET") == "Actions & Fonds"
    assert categorize_account("PEG Schmidt", "ASSET") == "Actions & Fonds"
    assert categorize_account("Avances fournisseurs", "ASSET") == "Autres"


def test_categorize_account_normalizes_accents_case_and_spaces() -> None:
    assert (
        categorize_account("  credit mutuel  ", "BANK")
        == "Comptes Bancaires"
    )
    assert (
        categorize_account("compte d'epargne", "BANK")
        == "Livrets"
    )
    assert (
        categorize_account("av cedit mutuel", "ASSET")
        == "Actions & Fonds"
    )


def test_categorize_account_falls_back_to_autres() -> None:
    assert categorize_account("Créances", "ASSET") == "Autres"
    assert categorize_account("Frais pro", "ASSET") == "Autres"


def test_categorize_accounts_accepts_dicts_and_dataclasses() -> None:
    accounts = [
        {"guid": "1", "name": "Apple", "account_type": "STOCK"},
        _Account(guid="2", name="Maison", account_type="ASSET"),
    ]

    result = categorize_accounts(accounts)

    assert result == [
        {
            "guid": "1",
            "name": "Apple",
            "account_type": "STOCK",
            "business_category": "Actions & Fonds",
        },
        {
            "guid": "2",
            "name": "Maison",
            "account_type": "ASSET",
            "business_category": "Immobilier",
        },
    ]
