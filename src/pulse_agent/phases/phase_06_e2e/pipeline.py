from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from pulse_agent.audit.logger import RunAudit, save_audit
from pulse_agent.config.loader import AppConfig, load_config
from pulse_agent.models.run import RunContext, RunStatus
from pulse_agent.phases.phase_01_ingestion.normalize import count_by_source
from pulse_agent.phases.phase_01_ingestion.service import (
    IngestionError,
    ingest_reviews,
    persist_corpus,
)
from pulse_agent.phases.phase_02_analysis.persist import (
    load_corpus_from_run,
    load_report_from_run,
)
from pulse_agent.phases.phase_02_analysis.service import AnalysisError, analyze_reviews
from pulse_agent.phases.phase_03_render.persist import load_rendered
from pulse_agent.phases.phase_03_render.service import (
    RenderError,
    render_report,
    review_count_for_render,
)
from pulse_agent.phases.phase_04_docs_mcp.service import DocsDeliveryError, deliver_docs
from pulse_agent.phases.phase_05_gmail_mcp.service import (
    GmailDeliveryError,
    deliver_gmail,
    load_docs_for_gmail,
)
from pulse_agent.phases.phase_06_e2e.exit_codes import EXIT_FATAL, EXIT_PARTIAL, EXIT_SUCCESS
from pulse_agent.phases.phase_06_e2e.workspace_smoke import run_workspace_smoke
from pulse_agent.phases.phase_07_hardening.gates import ProductionGateError
from pulse_agent.phases.phase_07_hardening.metrics import finalize_audit
from pulse_agent.safety.corpus import scrub_rendered_for_publish

logger = logging.getLogger(__name__)


def run_pipeline(ctx: RunContext, config: AppConfig | None = None) -> int:
    """
    Full E2E pipeline: ingest → analyze → render → docs → gmail → audit.
    Exit codes: 0 success, 1 fatal, 2 partial (docs ok, gmail failed).
    """
    started_at = datetime.now(timezone.utc)
    config = config or load_config(ctx.project_root)
    product = config.get_product(ctx.product_id)
    ctx.window_weeks = product.window_weeks

    audit = RunAudit.stub_for(ctx, dry_run=ctx.dry_run)
    audit.status = RunStatus.RUNNING
    audit.phases_completed.append("bootstrap")

    corpus = None
    report = None
    rendered_delivery = None
    docs_result = None
    docs_delivered = False

    try:
        if not ctx.skip_ingest:
            audit.phases_completed.append("phase_01_ingestion")
            corpus = ingest_reviews(
                ctx,
                product,
                play_count=ctx.play_count,
                app_store_max_pages=ctx.app_store_max_pages,
            )
            persist_corpus(ctx, corpus)
            by_source = count_by_source(corpus.reviews)
            audit.ingest = {
                **corpus.stats.to_dict(),
                "review_count": corpus.stats.after_content_filter,
                "by_source": by_source,
            }
            logger.info(
                "Ingest complete: %s reviews after filters",
                corpus.stats.after_content_filter,
            )
            print(
                f"review_count={corpus.stats.after_content_filter} "
                f"app_store={by_source.get('app_store', 0)} "
                f"play_store={by_source.get('play_store', 0)}"
            )
        else:
            audit.phases_completed.append("phase_01_ingestion_skipped")

        if not ctx.skip_analyze:
            audit.phases_completed.append("phase_02_analysis")
            if corpus is None:
                corpus = load_corpus_from_run(ctx)
            force_stub = ctx.force_stub_llm or (
                ctx.dry_run and not os.environ.get("GROQ_API_KEY")
            )
            report = analyze_reviews(
                ctx,
                corpus,
                force_stub_llm=force_stub,
                force_analyze=ctx.force_analyze,
            )
            audit.analysis = {
                **report.stats.to_dict(),
                "theme_count": len(report.themes),
                "quote_count": len(report.quotes),
            }
            print(
                f"theme_count={len(report.themes)} "
                f"quote_count={len(report.quotes)} "
                f"groq_requests={report.stats.groq_requests}"
            )
        else:
            audit.phases_completed.append("phase_02_analysis_skipped")

        if not ctx.skip_render:
            audit.phases_completed.append("phase_03_render")
            if report is None:
                report = load_report_from_run(ctx)
            if report is None:
                raise RenderError(
                    f"No pulse report at {ctx.pulse_report_path}; run analysis first"
                )
            corpus_review_count = None
            if corpus is not None:
                corpus_review_count = corpus.stats.after_content_filter
            elif ctx.reviews_path.is_file():
                corpus = load_corpus_from_run(ctx)
                corpus_review_count = corpus.stats.after_content_filter
            rendered_delivery = render_report(
                ctx,
                report,
                product,
                review_count=review_count_for_render(report, corpus_review_count),
                force_render=ctx.force_render,
            )
            audit.render = {
                "heading": rendered_delivery.doc_section.heading,
                "anchor": rendered_delivery.doc_section.anchor,
                "email_subject": rendered_delivery.email_teaser.subject,
                "doc_section_path": str(ctx.doc_section_path),
                "email_teaser_path": str(ctx.email_teaser_path),
                "theme_count": rendered_delivery.theme_count,
                "review_count": rendered_delivery.review_count,
            }
            print(f"render_heading={rendered_delivery.doc_section.heading!r}")
        else:
            audit.phases_completed.append("phase_03_render_skipped")

        publish_payload = rendered_delivery
        if publish_payload is not None:
            publish_payload = scrub_rendered_for_publish(publish_payload)

        if not ctx.skip_docs and not ctx.dry_run:
            audit.phases_completed.append("phase_04_docs_mcp")
            if publish_payload is None:
                publish_payload = scrub_rendered_for_publish(load_rendered(ctx))
            if publish_payload is None:
                raise DocsDeliveryError("No render artifacts; run render first")
            docs_result = deliver_docs(
                ctx,
                publish_payload,
                product,
                config,
                force_deliver=ctx.force_docs,
            )
            audit.delivery["docs"] = docs_result.to_dict()
            docs_delivered = True
            print(f"docs_delivered doc_id={docs_result.doc_id}")
        elif ctx.dry_run:
            audit.phases_completed.append("phase_04_docs_skipped_dry_run")
        else:
            audit.phases_completed.append("phase_04_docs_skipped")

        if not ctx.skip_gmail and not ctx.dry_run:
            audit.phases_completed.append("phase_05_gmail_mcp")
            try:
                if publish_payload is None:
                    publish_payload = scrub_rendered_for_publish(load_rendered(ctx))
                if publish_payload is None:
                    raise GmailDeliveryError("No render artifacts")
                if docs_result is None:
                    docs_result = load_docs_for_gmail(ctx)
                gmail_result = deliver_gmail(
                    ctx,
                    publish_payload,
                    docs_result,
                    product,
                    config,
                    force_deliver=ctx.force_gmail,
                )
                audit.delivery["gmail"] = gmail_result.to_dict()
                print(
                    f"gmail_delivered mode={gmail_result.mode} to={gmail_result.to} "
                    f"draft_id={gmail_result.gmail_draft_id}"
                )
            except GmailDeliveryError as exc:
                audit.errors.append(str(exc))
                if docs_delivered:
                    finalize_audit(
                        audit, ctx, config, started_at=started_at, exit_code=EXIT_PARTIAL
                    )
                    save_audit(ctx, audit)
                    logger.error("Partial failure (docs ok, gmail failed): %s", exc)
                    return EXIT_PARTIAL
                raise
        elif ctx.dry_run:
            audit.phases_completed.append("phase_05_gmail_skipped_dry_run")
        else:
            audit.phases_completed.append("phase_05_gmail_skipped")

        if not ctx.skip_mcp and not ctx.dry_run:
            audit.phases_completed.append("phase_06_workspace_smoke")
            smoke = run_workspace_smoke(config)
            audit.mcp_smoke = [r.to_dict() for r in smoke]
            if not all(r.ok for r in smoke):
                audit.errors.append("Workspace MCP smoke failed")
                finalize_audit(
                    audit, ctx, config, started_at=started_at, exit_code=EXIT_FATAL
                )
                save_audit(ctx, audit)
                return EXIT_FATAL
        elif ctx.dry_run:
            audit.phases_completed.append("phase_06_workspace_smoke_skipped_dry_run")
        else:
            audit.phases_completed.append("phase_06_workspace_smoke_skipped")

        finalize_audit(audit, ctx, config, started_at=started_at, exit_code=EXIT_SUCCESS)
        save_audit(ctx, audit)
        return EXIT_SUCCESS

    except (
        IngestionError,
        AnalysisError,
        RenderError,
        DocsDeliveryError,
        GmailDeliveryError,
        ProductionGateError,
    ) as exc:
        logger.error("Pipeline failed: %s", exc)
        audit.errors.append(str(exc))
        finalize_audit(audit, ctx, config, started_at=started_at, exit_code=EXIT_FATAL)
        save_audit(ctx, audit)
        return EXIT_FATAL
    except KeyError as exc:
        logger.error("Config error: %s", exc)
        audit.errors.append(str(exc))
        finalize_audit(audit, ctx, config, started_at=started_at, exit_code=EXIT_FATAL)
        save_audit(ctx, audit)
        return EXIT_FATAL
    except Exception as exc:
        logger.exception("Run failed: %s", exc)
        audit.errors.append(str(exc))
        finalize_audit(audit, ctx, config, started_at=started_at, exit_code=EXIT_FATAL)
        save_audit(ctx, audit)
        return EXIT_FATAL
