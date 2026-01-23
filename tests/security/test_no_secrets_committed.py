"""Basic regression tests to avoid committing common secret files.

These tests are not a substitute for proper secret scanning, but they prevent
accidental check-ins of typical local credential artifacts.
"""

from __future__ import annotations

from pathlib import Path


def test_no_google_oauth_client_secret_files_committed() -> None:
    """Ensure common Google OAuth credential filenames are not committed."""
    repo_root = Path(__file__).resolve().parents[2]
    forbidden = [
        *repo_root.glob("**/client_secret*.json"),
        *repo_root.glob("**/*client_secret*.json"),
        *repo_root.glob("**/credentials*.json"),
        *repo_root.glob("**/*credentials*.json"),
        *repo_root.glob("**/*service_account*.json"),
    ]
    forbidden = [path for path in forbidden if path.is_file()]
    assert forbidden == []


def test_no_obvious_token_prefixes_in_tracked_text_files() -> None:
    """Reject a small set of high-signal token prefixes in the repo."""
    repo_root = Path(__file__).resolve().parents[2]
    token_prefixes = (
        "GOCSPX-",
    )
    candidates = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if path == Path(__file__).resolve():
            continue
        if path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".sqlite"}:
            continue
        if ".git" in path.parts or ".venv" in path.parts or ".uv-cache" in path.parts:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(prefix in content for prefix in token_prefixes):
            candidates.append(path)
    assert candidates == []
