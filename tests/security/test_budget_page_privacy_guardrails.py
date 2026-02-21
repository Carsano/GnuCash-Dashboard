"""Security/privacy guardrails for Budget page implementation."""

from __future__ import annotations

from pathlib import Path


def test_budget_page_has_no_external_http_endpoints_or_telemetry_hooks() -> None:
    budget_renderer = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "adapters"
        / "interface"
        / "streamlit"
        / "page_renderers"
        / "budget.py"
    )
    content = budget_renderer.read_text(encoding="utf-8")

    forbidden_markers = (
        "http://",
        "https://",
        "fetch(",
        "XMLHttpRequest",
        "google-analytics",
        "segment",
        "mixpanel",
        "sentry.io",
    )
    assert not any(marker in content for marker in forbidden_markers)
