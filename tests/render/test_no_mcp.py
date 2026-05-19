from pathlib import Path


def test_render_module_has_no_mcp_imports(project_root: Path):
    render_dir = project_root / "src" / "pulse_agent" / "phases" / "phase_03_render"
    forbidden = ("from pulse_agent.mcp", "import mcp", "McpClient", "run_mcp")
    for path in render_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{needle!r} found in {path.name}"
