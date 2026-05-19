from __future__ import annotations

import json
from pathlib import Path

import pytest

from pulse_agent.config.loader import ProductConfig
from pulse_agent.models.report import PulseReport
from pulse_agent.phases.phase_02_analysis.persist import load_report
from pulse_agent.phases.phase_03_render.config import RenderLimits


@pytest.fixture
def groww_product() -> ProductConfig:
    return ProductConfig(
        product_id="groww",
        display_name="Groww",
        app_store_id="1404871703",
        play_package="com.nextbillion.groww",
        doc_title_template="Weekly Review Pulse — Groww",
        window_weeks=10,
        recipients=["pm@example.com"],
    )


@pytest.fixture
def groww_report(project_root: Path) -> PulseReport:
    fixture = project_root / "tests" / "fixtures" / "pulse_report_groww.json"
    report = load_report(fixture)
    assert report is not None
    return report


@pytest.fixture
def render_limits() -> RenderLimits:
    return RenderLimits(
        email_max_lines=15,
        email_max_words=500,
        max_actions_per_theme=4,
        max_quotes_in_doc=8,
    )


@pytest.fixture
def golden_dir(project_root: Path) -> Path:
    return project_root / "tests" / "fixtures" / "golden" / "phase_03"
