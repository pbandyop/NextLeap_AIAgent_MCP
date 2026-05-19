"""Phase 3 — Render: Doc section + email teaser (delivery in later phases)."""

from pulse_agent.phases.phase_03_render.persist import load_rendered
from pulse_agent.phases.phase_03_render.service import render_report

__all__ = ["render_report", "load_rendered"]
