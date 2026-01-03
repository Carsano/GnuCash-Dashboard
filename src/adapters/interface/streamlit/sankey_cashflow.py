"""Cashflow Sankey presentation logic for the Streamlit UI.

This module contains pure, testable transformations from a ``CashflowView``
produced by ``GetCashflowUseCase`` to a Sankey model and Plotly figure.

The UI is responsible for:
    - loading the ``CashflowView`` (no IO here),
    - persisting ``SankeyState`` in ``st.session_state``,
    - applying click events to update the state.

The Sankey layout is fixed to three columns:
    Entrées -> Actifs sélectionnés -> Sorties
with optional nodes for difference handling:
    - ``Épargne / Excédent`` when the cashflow difference is positive,
    - ``Déficit`` (optional) when the difference is negative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal
from typing import TYPE_CHECKING

from src.domain.models.finance import CashflowItem, CashflowView

if TYPE_CHECKING:  # pragma: no cover
    import plotly.graph_objects as go


LEFT_PREFIX = "L:"
MIDDLE_PREFIX = "M:"
RIGHT_PREFIX = "R:"

MIDDLE_LABEL = "Actifs sélectionnés"
SAVINGS_LABEL = "Épargne / Excédent"
DEFICIT_LABEL = "Déficit"

MIDDLE_KEY = f"{MIDDLE_PREFIX}ASSETS"
SAVINGS_KEY = f"{RIGHT_PREFIX}SAVINGS"
DEFICIT_KEY = f"{LEFT_PREFIX}DEFICIT"


@dataclass
class SankeyState:
    """Drill-down state for the cashflow Sankey.

    Attributes:
        left_level_default: Default depth for incoming accounts.
        right_level_default: Default depth for outgoing accounts.
        left_focus: Map root -> current depth for the left side.
        right_focus: Map root -> current depth for the right side.
        allow_negative_diff: If true, show a "Déficit" node for negative
            differences and link it into the middle node.
        last_clicked_side: Side ("L"/"R") of the last clicked node.
        last_clicked_root: Root (level-1 account name) of the last click.
    """

    left_level_default: int = 1
    right_level_default: int = 1
    left_focus: dict[str, int] = field(default_factory=dict)
    right_focus: dict[str, int] = field(default_factory=dict)
    allow_negative_diff: bool = False
    last_clicked_side: Literal["L", "R"] | None = None
    last_clicked_root: str | None = None

    def reset_all(self) -> None:
        """Reset all drill-down state."""
        self.left_focus.clear()
        self.right_focus.clear()
        self.last_clicked_side = None
        self.last_clicked_root = None

    def reset_last_branch(self) -> None:
        """Reset only the last clicked branch (if any)."""
        if not self.last_clicked_side or not self.last_clicked_root:
            return
        if self.last_clicked_side == "L":
            self.left_focus.pop(self.last_clicked_root, None)
        else:
            self.right_focus.pop(self.last_clicked_root, None)


@dataclass(frozen=True)
class SankeyLink:
    """Sankey link edge."""

    source: int
    target: int
    value: Decimal


@dataclass(frozen=True)
class SankeyModel:
    """Model used by the UI to render a Sankey with stable indices."""

    node_labels: list[str]
    node_keys: list[str]
    links: list[SankeyLink]
    key_by_index: dict[int, str]
    side_by_key: dict[str, Literal["L", "M", "R"]]
    root_by_key: dict[str, str | None]
    max_depth_left_by_root: dict[str, int]
    max_depth_right_by_root: dict[str, int]


def parse_account_path(account_full_name: str) -> list[str]:
    """Split a GnuCash account full name into parts.

    Args:
        account_full_name: Full account name, usually delimited by ":".

    Returns:
        List of non-empty path parts.
    """
    parts = [part.strip() for part in account_full_name.split(":")]
    return [part for part in parts if part]


def level_key(parts: list[str], n: int) -> str:
    """Return the path key for a given depth.

    Args:
        parts: Path parts (already split).
        n: Desired depth (1-based).

    Returns:
        Joined account key up to depth ``n`` (clamped).
    """
    if not parts:
        return ""
    depth = max(1, min(n, len(parts)))
    return ":".join(parts[:depth])


def _group_items_by_level(
    *,
    items: list[CashflowItem],
    focus_by_root: dict[str, int],
    default_level: int,
) -> tuple[list[tuple[str, Decimal, str]], dict[str, int]]:
    order: list[str] = []
    totals: dict[str, Decimal] = {}
    root_by_group: dict[str, str] = {}
    max_depth_by_root: dict[str, int] = {}

    for item in items:
        parts = parse_account_path(item.account_full_name)
        if not parts:
            continue
        root = parts[0]
        max_depth_by_root[root] = max(
            max_depth_by_root.get(root, 0),
            len(parts),
        )
        requested_depth = focus_by_root.get(root, default_level)
        group = level_key(parts, requested_depth)
        if group not in totals:
            order.append(group)
            totals[group] = item.amount
            root_by_group[group] = root
        else:
            totals[group] += item.amount

    grouped = [(group, totals[group], root_by_group[group]) for group in order]
    return grouped, max_depth_by_root


def _add_node(
    *,
    node_keys: list[str],
    node_labels: list[str],
    side_by_key: dict[str, Literal["L", "M", "R"]],
    root_by_key: dict[str, str | None],
    key: str,
    label: str,
    side: Literal["L", "M", "R"],
    root: str | None,
) -> int:
    if key in side_by_key:
        return node_keys.index(key)
    node_keys.append(key)
    node_labels.append(label)
    side_by_key[key] = side
    root_by_key[key] = root
    return len(node_keys) - 1


def build_sankey_model(view: CashflowView, state: SankeyState) -> SankeyModel:
    """Build a stable Sankey model from a cashflow view.

    Args:
        view: Cashflow view produced by the use case.
        state: Drill-down state controlling grouping depth.

    Returns:
        SankeyModel: Nodes, links, and metadata for click decoding.
    """
    incoming_grouped, max_depth_left_by_root = _group_items_by_level(
        items=view.incoming,
        focus_by_root=state.left_focus,
        default_level=state.left_level_default,
    )
    outgoing_grouped, max_depth_right_by_root = _group_items_by_level(
        items=view.outgoing,
        focus_by_root=state.right_focus,
        default_level=state.right_level_default,
    )

    node_labels: list[str] = []
    node_keys: list[str] = []
    side_by_key: dict[str, Literal["L", "M", "R"]] = {}
    root_by_key: dict[str, str | None] = {}

    left_index_by_group: dict[str, int] = {}
    right_index_by_group: dict[str, int] = {}

    for group, _amount, root in incoming_grouped:
        key = f"{LEFT_PREFIX}{group}"
        left_index_by_group[group] = _add_node(
            node_keys=node_keys,
            node_labels=node_labels,
            side_by_key=side_by_key,
            root_by_key=root_by_key,
            key=key,
            label=group,
            side="L",
            root=root,
        )

    middle_index = _add_node(
        node_keys=node_keys,
        node_labels=node_labels,
        side_by_key=side_by_key,
        root_by_key=root_by_key,
        key=MIDDLE_KEY,
        label=MIDDLE_LABEL,
        side="M",
        root=None,
    )

    for group, _amount, root in outgoing_grouped:
        key = f"{RIGHT_PREFIX}{group}"
        right_index_by_group[group] = _add_node(
            node_keys=node_keys,
            node_labels=node_labels,
            side_by_key=side_by_key,
            root_by_key=root_by_key,
            key=key,
            label=group,
            side="R",
            root=root,
        )

    diff = view.summary.difference
    savings_index: int | None = None
    deficit_index: int | None = None
    if diff > 0:
        savings_index = _add_node(
            node_keys=node_keys,
            node_labels=node_labels,
            side_by_key=side_by_key,
            root_by_key=root_by_key,
            key=SAVINGS_KEY,
            label=SAVINGS_LABEL,
            side="R",
            root=None,
        )
    if diff < 0 and state.allow_negative_diff:
        deficit_index = _add_node(
            node_keys=node_keys,
            node_labels=node_labels,
            side_by_key=side_by_key,
            root_by_key=root_by_key,
            key=DEFICIT_KEY,
            label=DEFICIT_LABEL,
            side="L",
            root=None,
        )

    links: list[SankeyLink] = []
    for group, amount, _root in incoming_grouped:
        source = left_index_by_group[group]
        links.append(SankeyLink(
            source=source, target=middle_index, value=amount))
    for group, amount, _root in outgoing_grouped:
        target = right_index_by_group[group]
        links.append(SankeyLink(
            source=middle_index, target=target, value=amount))
    if savings_index is not None:
        links.append(
            SankeyLink(source=middle_index, target=savings_index, value=diff)
        )
    if deficit_index is not None:
        links.append(
            SankeyLink(
                source=deficit_index,
                target=middle_index,
                value=abs(diff),
            )
        )

    key_by_index = {idx: key for idx, key in enumerate(node_keys)}

    return SankeyModel(
        node_labels=node_labels,
        node_keys=node_keys,
        links=links,
        key_by_index=key_by_index,
        side_by_key=side_by_key,
        root_by_key=root_by_key,
        max_depth_left_by_root=max_depth_left_by_root,
        max_depth_right_by_root=max_depth_right_by_root,
    )


def build_plotly_figure(model: SankeyModel) -> "go.Figure":
    """Build a Plotly Sankey figure from a Sankey model.

    Args:
        model: Precomputed Sankey model.

    Returns:
        Plotly figure ready to be displayed in Streamlit.
    """
    node_x: list[float] = []
    node_y: list[float] = []
    left_count = 0
    right_count = 0
    for key in model.node_keys:
        side = model.side_by_key.get(key, "M")
        if side == "L":
            left_count += 1
        elif side == "R":
            right_count += 1

    left_seen = 0
    right_seen = 0
    for key in model.node_keys:
        side = model.side_by_key.get(key, "M")
        if side == "L":
            node_x.append(0.02)
            y = (left_seen + 1) / (left_count + 1) if left_count else 0.5
            node_y.append(y)
            left_seen += 1
        elif side == "R":
            node_x.append(0.98)
            y = (right_seen + 1) / (right_count + 1) if right_count else 0.5
            node_y.append(y)
            right_seen += 1
        else:
            node_x.append(0.5)
            node_y.append(0.5)

    sources = [link.source for link in model.links]
    targets = [link.target for link in model.links]
    values = [float(link.value) for link in model.links]

    import plotly.graph_objects as go

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=10,
                    thickness=12,
                    label=model.node_labels,
                    x=node_x,
                    y=node_y,
                    line=dict(color="rgba(0,0,0,0.25)", width=0.5),
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                ),
                textfont=dict(size=12),
            )
        ]
    )
    fig.update_layout(
        margin=dict(l=8, r=8, t=8, b=8),
        height=680,
    )
    return fig


def apply_click(
    *,
    state: SankeyState,
    model: SankeyModel,
    node_index: int,
) -> bool:
    """Update a Sankey state based on a clicked node.

    Args:
        state: State to mutate.
        model: Model containing click metadata.
        node_index: Clicked node index.

    Returns:
        True if the state changed, otherwise False.
    """
    internal_key = model.key_by_index.get(node_index)
    if not internal_key:
        return False
    side = model.side_by_key.get(internal_key)
    root = model.root_by_key.get(internal_key)
    if side not in {"L", "R"} or not root:
        return False

    focus = state.left_focus if side == "L" else state.right_focus
    default_level = (
        state.left_level_default if side == "L" else state.right_level_default
    )
    current_level = focus.get(root, default_level)
    max_depth_by_root = (
        model.max_depth_left_by_root
        if side == "L"
        else model.max_depth_right_by_root
    )
    max_depth = max_depth_by_root.get(root, current_level)
    if current_level >= max_depth:
        state.last_clicked_side = side
        state.last_clicked_root = root
        return False

    focus[root] = current_level + 1
    state.last_clicked_side = side
    state.last_clicked_root = root
    return True
