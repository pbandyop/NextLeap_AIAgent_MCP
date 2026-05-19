import json
from datetime import date
from unittest.mock import patch

from pulse_agent.config.loader import load_config
from pulse_agent.models.review import Review, ReviewSource
from pulse_agent.models.run import RunContext
from pulse_agent.orchestrator import run_pipeline


def _review(rid: str, source: ReviewSource) -> Review:
    return Review(
        source=source,
        review_id=rid,
        rating=4,
        title="Title",
        body="This is a long enough English review body for normalization filters.",
        review_date=date(2026, 4, 1),
    )


def test_ingest_step_writes_reviews_json(project_root, tmp_path):
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        dry_run=True,
        skip_mcp=True,
        project_root=project_root,
    )
    app = [_review("a1", ReviewSource.APP_STORE)]
    play = [_review("p1", ReviewSource.PLAY_STORE)]

    with (
        patch(
            "pulse_agent.phases.phase_01_ingestion.service.fetch_app_store_reviews",
            return_value=app,
        ),
        patch(
            "pulse_agent.phases.phase_01_ingestion.service.fetch_play_store_reviews",
            return_value=play,
        ),
    ):
        code = run_pipeline(ctx, load_config(project_root))

    assert code == 0
    assert ctx.reviews_path.is_file()
    data = json.loads(ctx.reviews_path.read_text(encoding="utf-8"))
    assert len(data["reviews"]) == 2
    assert data["stats"]["after_content_filter"] == 2
