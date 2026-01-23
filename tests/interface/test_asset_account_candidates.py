"""Tests for asset account selection helpers in the Streamlit adapter."""

from src.application.use_cases.get_cashflow_asset_selection import (
    build_cashflow_asset_selection,
)
from src.domain.models.accounts import AccountDTO


def test_asset_account_candidates_detects_root_not_at_top_level():
    accounts = [
        AccountDTO(
            guid="root",
            name="Root Account",
            account_type="ROOT",
            commodity_guid=None,
            parent_guid=None,
        ),
        AccountDTO(
            guid="assets",
            name="Actif",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid="root",
        ),
        AccountDTO(
            guid="bank",
            name="Banque",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid="assets",
        ),
        AccountDTO(
            guid="cash",
            name="Espèces",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid="assets",
        ),
    ]
    selection = build_cashflow_asset_selection(accounts, asset_root_name="Actif")
    assert list(selection.candidate_guids) == ["bank", "cash"]
    assert selection.display_name_by_guid["bank"] == "Actif:Banque"
    assert selection.display_name_by_guid["cash"] == "Actif:Espèces"


def test_default_selected_asset_guids_excludes_receivables_and_investments_subtrees():
    accounts = [
        AccountDTO(
            guid="root",
            name="Actif",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid=None,
        ),
        AccountDTO(
            guid="a",
            name="Banque",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid="root",
        ),
        AccountDTO(
            guid="b",
            name="Créances",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid="root",
        ),
        AccountDTO(
            guid="c",
            name="Client X",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid="b",
        ),
        AccountDTO(
            guid="d",
            name="Investissements",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid="root",
        ),
        AccountDTO(
            guid="e",
            name="ETF",
            account_type="ASSET",
            commodity_guid=None,
            parent_guid="d",
        ),
    ]
    selection = build_cashflow_asset_selection(accounts, asset_root_name="Actif")
    assert list(selection.default_selected_guids) == ["a"]
