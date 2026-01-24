"""Cashflow page renderer for the Streamlit dashboard."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.adapters.interface.streamlit.sankey_cashflow import (
    SankeyState,
    build_plotly_figure,
    build_sankey_model,
)
from src.adapters.interface.streamlit.shared import (
    format_currency,
    get_date_inputs,
    load_cashflow_asset_selection,
    load_cashflow_view,
)
from src.application.use_cases.get_cashflow import CashflowView


def _render_cashflow_summary(view: CashflowView) -> None:
    """Render cashflow totals with colored difference."""
    summary = view.summary
    incoming_col, outgoing_col, diff_col = st.columns(3)
    incoming_col.metric(
        "Entrées",
        format_currency(summary.total_in, summary.currency_code),
    )
    outgoing_col.metric(
        "Sorties",
        format_currency(summary.total_out, summary.currency_code),
    )
    diff = summary.difference
    diff_color = "#2e7d32" if diff >= 0 else "#c62828"
    diff_col.markdown(
        "<div style='font-size:0.9rem;color:#98a2b3'>"
        "Différence</div>"
        f"<div style='font-size:1.35rem;font-weight:600;color:{diff_color}'>"
        f"{format_currency(diff, summary.currency_code)}</div>",
        unsafe_allow_html=True,
    )


def _render_cashflow_details(view: CashflowView) -> None:
    """Render cashflow incoming and outgoing tables."""
    incoming_data = [
        {
            "Compte": item.account_full_name,
            "Montant": format_currency(item.amount, view.summary.currency_code),
        }
        for item in view.incoming
    ]
    outgoing_data = [
        {
            "Compte": item.account_full_name,
            "Montant": format_currency(item.amount, view.summary.currency_code),
        }
        for item in view.outgoing
    ]
    incoming_col, outgoing_col = st.columns(2)
    with incoming_col:
        st.markdown("#### Entrants")
        if incoming_data:
            st.dataframe(
                incoming_data,
                width="stretch",
                hide_index=True,
                height=360,
            )
        else:
            st.caption("Aucun flux entrant sur la période.")
    with outgoing_col:
        st.markdown("#### Sortants")
        if outgoing_data:
            st.dataframe(
                outgoing_data,
                width="stretch",
                hide_index=True,
                height=360,
            )
        else:
            st.caption("Aucun flux sortant sur la période.")


def _render_asset_account_selector(
    *,
    analytics_schema_version: int,
    selection_key: str,
) -> tuple[str, tuple[str, ...]]:
    """Render the asset account selector UI.

    Args:
        analytics_schema_version: Cache-buster that increments after a sync.
        selection_key: Session key used to store selected GUIDs.

    Returns:
        Tuple of (asset_root_name, selected_asset_guids).
    """
    with st.expander("Sélection des comptes Actifs", expanded=False):
        asset_root_key = "cashflow_asset_root_name"
        asset_root_name = st.text_input(
            "Racine des comptes Actifs",
            key=asset_root_key,
            value="Actif",
            help="Doit correspondre au nom du compte racine (ex: Actif).",
        ).strip() or "Actif"

        selection = load_cashflow_asset_selection(
            asset_root_name,
            schema_version=analytics_schema_version,
        )
        asset_candidates = list(selection.candidate_guids)
        display_name_by_guid = selection.display_name_by_guid
        if not asset_candidates:
            st.warning(
                f"Aucun compte trouvé sous la racine « {asset_root_name} ». "
                "Vérifie le nom (ou lance la mise à jour analytics)."
            )
            return asset_root_name, tuple()

        asset_candidate_set = set(asset_candidates)
        if selection_key not in st.session_state:
            st.session_state[selection_key] = list(selection.default_selected_guids)
        else:
            current = [
                guid
                for guid in st.session_state[selection_key]
                if guid in asset_candidate_set
            ]
            if len(current) != len(st.session_state[selection_key]):
                st.session_state[selection_key] = current

        actions = st.columns([1, 1, 3])
        if actions[0].button(
            "Tout sélectionner",
            key="cashflow_assets_select_all",
            disabled=not asset_candidates,
        ):
            st.session_state[selection_key] = list(asset_candidates)
            st.session_state.pop("cashflow_sankey_signature", None)
            st.session_state.pop("cashflow_sankey_model", None)
            st.session_state.pop("cashflow_sankey_fig", None)
            st.rerun()
        if actions[1].button(
            "Tout désélectionner",
            key="cashflow_assets_select_none",
            disabled=not bool(st.session_state[selection_key]),
        ):
            st.session_state[selection_key] = []
            st.session_state.pop("cashflow_sankey_signature", None)
            st.session_state.pop("cashflow_sankey_model", None)
            st.session_state.pop("cashflow_sankey_fig", None)
            st.rerun()

        st.markdown("#### Comptes Actifs utilisés")
        selected_guids: list[str] = list(st.session_state[selection_key])
        selected_set = set(selected_guids)

        left_panel, right_panel = st.columns(2)
        with left_panel:
            st.caption(f"Disponibles: {len(asset_candidates) - len(selected_guids)}")
            available_query = st.text_input(
                "Filtrer (disponibles)",
                value="",
                key="cashflow_assets_filter_available",
            ).strip().lower()
            available_guids = [
                guid
                for guid in asset_candidates
                if guid not in selected_set
                and (
                    not available_query
                    or available_query
                    in display_name_by_guid.get(guid, guid).lower()
                )
            ]
            available_labels = [
                display_name_by_guid.get(guid, guid) for guid in available_guids
            ]
            available_choice = st.selectbox(
                "Compte à ajouter",
                options=["—"] + available_labels,
                index=0,
                key="cashflow_assets_available_choice",
            )
            add_cols = st.columns([1, 1])
            if add_cols[0].button(
                "Ajouter",
                key="cashflow_assets_add_one",
                disabled=available_choice == "—",
            ):
                guid_to_add = available_guids[available_labels.index(available_choice)]
                st.session_state[selection_key] = [*selected_guids, guid_to_add]
                st.session_state.pop("cashflow_sankey_signature", None)
                st.session_state.pop("cashflow_sankey_model", None)
                st.session_state.pop("cashflow_sankey_fig", None)
                st.rerun()
            if add_cols[1].button(
                "Ajouter tout (filtré)",
                key="cashflow_assets_add_all_filtered",
                disabled=not available_guids,
            ):
                st.session_state[selection_key] = [*selected_guids, *available_guids]
                st.session_state.pop("cashflow_sankey_signature", None)
                st.session_state.pop("cashflow_sankey_model", None)
                st.session_state.pop("cashflow_sankey_fig", None)
                st.rerun()

        with right_panel:
            st.caption(f"Sélectionnés: {len(selected_guids)}")
            selected_query = st.text_input(
                "Filtrer (sélectionnés)",
                value="",
                key="cashflow_assets_filter_selected",
            ).strip().lower()
            selected_filtered = [
                guid
                for guid in selected_guids
                if (
                    not selected_query
                    or selected_query in display_name_by_guid.get(guid, guid).lower()
                )
            ]
            selected_labels = [
                display_name_by_guid.get(guid, guid) for guid in selected_filtered
            ]
            selected_choice = st.selectbox(
                "Compte à retirer",
                options=["—"] + selected_labels,
                index=0,
                key="cashflow_assets_selected_choice",
            )
            remove_cols = st.columns([1, 1])
            if remove_cols[0].button(
                "Retirer",
                key="cashflow_assets_remove_one",
                disabled=selected_choice == "—",
            ):
                guid_to_remove = selected_filtered[selected_labels.index(selected_choice)]
                st.session_state[selection_key] = [
                    guid for guid in selected_guids if guid != guid_to_remove
                ]
                st.session_state.pop("cashflow_sankey_signature", None)
                st.session_state.pop("cashflow_sankey_model", None)
                st.session_state.pop("cashflow_sankey_fig", None)
                st.rerun()
            if remove_cols[1].button(
                "Retirer tout (filtré)",
                key="cashflow_assets_remove_all_filtered",
                disabled=not selected_filtered,
            ):
                remove_set = set(selected_filtered)
                st.session_state[selection_key] = [
                    guid for guid in selected_guids if guid not in remove_set
                ]
                st.session_state.pop("cashflow_sankey_signature", None)
                st.session_state.pop("cashflow_sankey_model", None)
                st.session_state.pop("cashflow_sankey_fig", None)
                st.rerun()

    return asset_root_name, tuple(st.session_state.get(selection_key, []))


def render_cashflow_page(*, analytics_schema_version: int) -> None:
    """Render the cashflow page.

    Args:
        analytics_schema_version: Cache-buster that increments after a sync.
    """
    today = date.today()
    start_date, end_date = get_date_inputs(today, key_prefix="cashflow")

    selection_key = "cashflow_selected_asset_guids"
    _, selected_asset_guids = _render_asset_account_selector(
        analytics_schema_version=analytics_schema_version,
        selection_key=selection_key,
    )
    if not selected_asset_guids:
        st.info("Aucun compte Actif sélectionné : aucun flux à afficher.")
        return

    view = load_cashflow_view(
        start_date,
        end_date,
        asset_account_guids=selected_asset_guids,
        schema_version=analytics_schema_version,
    )
    st.subheader("Synthèse")
    _render_cashflow_summary(view)

    st.subheader("Cashflow Sankey")
    show_sankey = st.toggle(
        "Afficher la visualisation Sankey (peut ralentir si très dense)",
        value=False,
        key="cashflow_show_sankey",
    )
    if show_sankey:
        allow_negative_diff = st.toggle(
            "Afficher le déficit si la différence est négative",
            value=bool(st.session_state.get("cashflow_sankey_allow_negative", False)),
            key="cashflow_sankey_allow_negative",
        )
        if view.summary.difference < 0 and not allow_negative_diff:
            st.warning(
                "La différence est négative sur la période, mais le nœud "
                "« Déficit » est désactivé."
            )

        sankey_state = SankeyState(allow_negative_diff=allow_negative_diff)
        desired_signature = (
            start_date,
            end_date,
            selected_asset_guids,
            sankey_state.allow_negative_diff,
        )
        signature_key = "cashflow_sankey_signature"
        model_key = "cashflow_sankey_model"
        fig_key = "cashflow_sankey_fig"

        last_signature = st.session_state.get(signature_key)
        needs_refresh = last_signature != desired_signature
        has_cached = fig_key in st.session_state and model_key in st.session_state

        refresh_col, hint_col = st.columns([1, 3])
        with refresh_col:
            refresh_clicked = st.button(
                "Rafraîchir Sankey",
                key="cashflow_sankey_refresh",
                type="primary" if (not has_cached or needs_refresh) else "secondary",
            )
        with hint_col:
            if needs_refresh and has_cached:
                st.info(
                    "Le Sankey n'est pas à jour pour ces paramètres. "
                    "Clique « Rafraîchir Sankey » pour recalculer."
                )

        if not has_cached or refresh_clicked:
            with st.spinner("Construction du Sankey…"):
                model = build_sankey_model(view, sankey_state)
                fig = build_plotly_figure(model)
            st.session_state[signature_key] = desired_signature
            st.session_state[model_key] = model
            st.session_state[fig_key] = fig
        else:
            fig = st.session_state[fig_key]
        st.plotly_chart(fig, width="stretch")

    st.subheader("Détails")
    _render_cashflow_details(view)
