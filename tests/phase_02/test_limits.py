import json
from datetime import date
from pathlib import Path

from pulse_agent.models.review import Review, ReviewCorpus, ReviewSource
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_02_analysis.config import AnalysisLimits
from pulse_agent.phases.phase_02_analysis.service import analyze_reviews


def _review(i: int) -> Review:
    return Review(
        source=ReviewSource.PLAY_STORE,
        review_id=f"r{i}",
        rating=5 if i % 2 == 0 else 2,
        title="Title",
        body="This review has enough English words to pass the content filter easily.",
        review_date=date(2026, 5, 1),
    )


def test_truncates_when_over_max_reviews(tmp_path):
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
    )
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    corpus = ReviewCorpus(reviews=[_review(i) for i in range(20)])
    limits = AnalysisLimits(
        max_reviews=5,
        max_clusters_positive=2,
        max_clusters_critical=1,
        min_themes=1,
    )
    report = analyze_reviews(
        ctx,
        corpus,
        limits=limits,
        force_stub_llm=True,
        force_analyze=True,
    )
    assert report.stats.positive_review_count + report.stats.critical_review_count <= 5


def test_skips_groq_when_cached(tmp_path):
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
    )
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    cached = {
        "idempotency_key": ctx.idempotency_key,
        "themes": [
            {
                "cluster_id": "critical_0",
                "label": "Cached",
                "summary": "Cached summary.",
                "sentiment": "critical",
                "review_count": 1,
                "actions": ["Act"],
            }
        ],
        "quotes": [],
        "metadata": {},
        "stats": {"groq_requests": 0, "theme_count": 1},
    }
    path = ctx.run_dir / "pulse_report.json"
    path.write_text(json.dumps(cached), encoding="utf-8")

    corpus = ReviewCorpus(reviews=[_review(0)])
    report = analyze_reviews(ctx, corpus, force_stub_llm=True, force_analyze=False)
    assert report.themes[0].label == "Cached"
