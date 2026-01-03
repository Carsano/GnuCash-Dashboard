"""Tests for asset account selection helpers in the Streamlit adapter."""

from src.adapters.interface.streamlit.app import _asset_account_candidates
from src.adapters.interface.streamlit.app import _default_selected_asset_guids
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
    candidates, labels = _asset_account_candidates(accounts, asset_root_name="Actif")
    assert candidates == ["bank", "cash"]
    assert labels["bank"] == "Actif:Banque"
    assert labels["cash"] == "Actif:Espèces"


def test_default_selected_asset_guids_excludes_receivables_subtree():
    asset_candidates = ["a", "b", "c"]
    display = {
        "a": "Actif:Banque",
        "b": "Actif:Créances",
        "c": "Actif:Créances:Client X",
    }
    selected = _default_selected_asset_guids(
        asset_candidates,
        display,
        asset_root_name="Actif",
    )
    assert selected == ["a"]
