"""Tests for the cashflow Sankey presentation module."""

from decimal import Decimal

from src.adapters.interface.streamlit.sankey_cashflow import (
    DEFICIT_LABEL,
    MIDDLE_LABEL,
    SAVINGS_LABEL,
    SankeyState,
    build_sankey_model,
    level_key,
    parse_account_path,
)
from src.domain.models.finance import (
    CashflowItem, CashflowSummary, CashflowView
)


def _view(
    *,
    incoming: list[CashflowItem],
    outgoing: list[CashflowItem],
    total_in: Decimal,
    total_out: Decimal,
) -> CashflowView:
    return CashflowView(
        summary=CashflowSummary(
            total_in=total_in,
            total_out=total_out,
            currency_code="EUR",
        ),
        incoming=incoming,
        outgoing=outgoing,
    )


def test_parse_account_path_and_level_key():
    parts = parse_account_path("Actif:Banque:Courant")
    assert parts == ["Actif", "Banque", "Courant"]
    assert level_key(parts, 1) == "Actif"
    assert level_key(parts, 2) == "Actif:Banque"
    assert level_key(parts, 99) == "Actif:Banque:Courant"
    assert level_key([], 2) == ""


def test_disambiguation_same_label_left_and_right_keeps_distinct_keys():
    view = _view(
        incoming=[
            CashflowItem(
                account_full_name="Passif:Cartes", amount=Decimal("5")
                ),
        ],
        outgoing=[
            CashflowItem(
                account_full_name="Passif:Charges", amount=Decimal("5")
            ),
        ],
        total_in=Decimal("5"),
        total_out=Decimal("5"),
    )
    model = build_sankey_model(view, SankeyState())
    assert "Passif" in model.node_labels
    assert "L:Passif" in model.node_keys
    assert "R:Passif" in model.node_keys


def test_drilldown_right_focus_level_2_groups_outgoing():
    view = _view(
        incoming=[],
        outgoing=[
            CashflowItem(
                account_full_name="Dépenses:Logement:Loyer",
                amount=Decimal("50"),
            ),
            CashflowItem(
                account_full_name="Dépenses:Alimentation",
                amount=Decimal("20"),
            ),
        ],
        total_in=Decimal("0"),
        total_out=Decimal("70"),
    )
    state = SankeyState(right_focus={"Dépenses": 2})
    model = build_sankey_model(view, state)
    idx_logement = model.node_labels.index("Dépenses:Logement")
    idx_alim = model.node_labels.index("Dépenses:Alimentation")
    assert idx_logement < idx_alim


def test_positive_difference_adds_savings_node_and_link():
    view = _view(
        incoming=[
            CashflowItem(
                account_full_name="Revenus:Salaire",
                amount=Decimal("100"),
            )
        ],
        outgoing=[
            CashflowItem(
                account_full_name="Dépenses:Courses",
                amount=Decimal("80"),
            )
        ],
        total_in=Decimal("100"),
        total_out=Decimal("80"),
    )
    model = build_sankey_model(view, SankeyState())
    savings_index = model.node_labels.index(SAVINGS_LABEL)
    middle_index = model.node_labels.index(MIDDLE_LABEL)
    assert any(
        link.source == middle_index
        and link.target == savings_index
        and link.value == Decimal("20")
        for link in model.links
    )


def test_negative_difference_deficit_link_only_when_allowed():
    view = _view(
        incoming=[],
        outgoing=[
            CashflowItem(
                account_full_name="Dépenses:Courses",
                amount=Decimal("100"),
            )
        ],
        total_in=Decimal("80"),
        total_out=Decimal("100"),
    )

    model_no_deficit = build_sankey_model(view, SankeyState())
    assert DEFICIT_LABEL not in model_no_deficit.node_labels

    model_with_deficit = build_sankey_model(
        view,
        SankeyState(allow_negative_diff=True),
    )
    deficit_index = model_with_deficit.node_labels.index(DEFICIT_LABEL)
    middle_index = model_with_deficit.node_labels.index(MIDDLE_LABEL)
    assert any(
        link.source == deficit_index
        and link.target == middle_index
        and link.value == Decimal("20")
        for link in model_with_deficit.links
    )
