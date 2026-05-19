from pulse_agent.phases.phase_03_render.heading import section_heading


def test_section_heading_format():
    assert section_heading("Groww", "2026-W20") == "Groww — Weekly Pulse — 2026-W20"
