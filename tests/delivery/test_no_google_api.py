from pathlib import Path


def test_no_google_api_client_in_agent_src(project_root: Path):
    src = project_root / "src" / "pulse_agent"
    forbidden = ("googleapiclient", "docs.v1", "google.oauth2")
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{needle!r} found in {path.relative_to(project_root)}"
