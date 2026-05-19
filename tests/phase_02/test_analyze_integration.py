import json
import shutil
from pathlib import Path

from pulse_agent.models.review import ReviewCorpus
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_02_analysis.config import AnalysisLimits
from pulse_agent.phases.phase_02_analysis.quotes import validate_report_quotes
from pulse_agent.phases.phase_02_analysis.service import analyze_reviews


def test_analyze_fixture_corpus(project_root, tmp_path):
    fixture = project_root / "tests" / "fixtures" / "reviews_corpus_small.json"
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
    )
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixture, ctx.reviews_path)

    corpus = ReviewCorpus.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
    limits = AnalysisLimits(
        max_clusters_positive=2,
        max_clusters_critical=2,
        min_themes=2,
    )
    report = analyze_reviews(
        ctx,
        corpus,
        limits=limits,
        force_stub_llm=True,
        force_analyze=True,
    )

    assert len(report.themes) >= 2
    assert ctx.pulse_report_path.is_file()
    reviews_by_id = {r.review_id: r for r in corpus.reviews}
    assert validate_report_quotes(report.quotes, reviews_by_id) == []
    critical = [t for t in report.themes if t.sentiment == "critical"]
    positive = [t for t in report.themes if t.sentiment == "positive"]
    assert critical
    assert positive


def test_analyze_groww_reviews_json_when_present(project_root, tmp_path):
    source = project_root / "data" / "runs" / "pulse_groww_2026-W20" / "reviews.json"
    if not source.is_file():
        return

    corpus = ReviewCorpus.from_dict(json.loads(source.read_text(encoding="utf-8")))
    if len(corpus.reviews) < 50:
        return  # skip when run dir has a tiny fixture corpus

    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
    )
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, ctx.reviews_path)
    limits = AnalysisLimits(
        max_reviews=120,
        max_clusters_positive=3,
        max_clusters_critical=3,
        min_themes=3,
    )
    report = analyze_reviews(
        ctx,
        corpus,
        limits=limits,
        force_stub_llm=True,
        force_analyze=True,
    )
    assert len(report.themes) >= 3
    reviews_by_id = {r.review_id: r for r in corpus.reviews[: limits.max_reviews]}
    assert validate_report_quotes(report.quotes, reviews_by_id) == []
