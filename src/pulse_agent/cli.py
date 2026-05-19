from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from pulse_agent.models.run import RunContext
from pulse_agent.orchestrator import find_project_root, run_pipeline
from pulse_agent.phases.phase_06_e2e.backfill import resolve_backfill_weeks, run_backfill
from pulse_agent.phases.phase_06_e2e.run_all import run_all_products
from pulse_agent.phases.phase_06_e2e.weeks import current_iso_week


def load_dotenv_file(project_root: Path) -> None:
    env_path = project_root / ".env"
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except ImportError:
        pass


def _add_pipeline_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ingest/analyze/render only; skip Docs/Gmail MCP delivery",
    )
    parser.add_argument("--skip-mcp", action="store_true", help="Skip workspace MCP health check")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip Phase 1 ingestion")
    parser.add_argument("--skip-analyze", action="store_true", help="Skip Phase 2 analysis")
    parser.add_argument(
        "--force-analyze",
        action="store_true",
        help="Re-run Groq analysis even if pulse_report.json exists",
    )
    parser.add_argument("--skip-render", action="store_true", help="Skip Phase 3 render")
    parser.add_argument(
        "--force-render",
        action="store_true",
        help="Re-render doc section and email teaser even if cached",
    )
    parser.add_argument("--skip-docs", action="store_true", help="Skip Phase 4 Google Docs delivery")
    parser.add_argument(
        "--force-docs",
        action="store_true",
        help="Re-append to Google Doc even if docs_delivery.json exists",
    )
    parser.add_argument("--skip-gmail", action="store_true", help="Skip Phase 5 Gmail delivery")
    parser.add_argument(
        "--skip-email",
        action="store_true",
        help="Alias for --skip-gmail",
    )
    parser.add_argument(
        "--force-gmail",
        action="store_true",
        help="Re-create Gmail draft even if gmail_delivery.json exists",
    )
    parser.add_argument("--stub-llm", action="store_true", help="Use stub LLM (no Groq API calls)")
    parser.add_argument("--play-count", type=int, default=None, help="Override Play fetch count")
    parser.add_argument(
        "--app-store-max-pages",
        type=int,
        default=None,
        help="Override App Store RSS pages",
    )
    parser.add_argument("--project-root", type=str, default=None, help="Repository root")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")


def _build_run_context(args: argparse.Namespace, root: Path) -> RunContext:
    if not args.product:
        raise SystemExit("--product is required")
    week = args.week or current_iso_week()
    skip_gmail = args.skip_gmail or getattr(args, "skip_email", False)
    return RunContext(
        product_id=args.product,
        iso_week=week,
        window_weeks=10,
        dry_run=args.dry_run,
        skip_mcp=args.skip_mcp or args.dry_run,
        skip_ingest=args.skip_ingest,
        skip_analyze=args.skip_analyze,
        force_analyze=args.force_analyze,
        skip_render=args.skip_render,
        force_render=args.force_render,
        skip_docs=args.skip_docs,
        force_docs=args.force_docs,
        skip_gmail=skip_gmail,
        force_gmail=args.force_gmail,
        force_stub_llm=args.stub_llm,
        play_count=args.play_count,
        app_store_max_pages=args.app_store_max_pages,
        project_root=root,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pulse",
        description="Weekly Product Review Pulse — single MCP agent",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Full pipeline for one product and ISO week")
    run.add_argument("--product", required=True, help="Product id from config/products.yaml")
    run.add_argument(
        "--week",
        help="ISO week label, e.g. 2026-W20 (default: current ISO week)",
    )
    _add_pipeline_flags(run)
    run.set_defaults(command="run")

    run_all = sub.add_parser("run-all", help="Full pipeline for every product in config")
    run_all.add_argument("--week", help="ISO week (default: current)")
    _add_pipeline_flags(run_all)
    run_all.set_defaults(command="run-all")

    backfill = sub.add_parser("backfill", help="Run pipeline for multiple ISO weeks")
    backfill.add_argument("--product", required=True)
    backfill.add_argument(
        "--weeks",
        help="Comma-separated ISO weeks, e.g. 2026-W18,2026-W19",
    )
    backfill.add_argument("--from-week", help="Start ISO week (inclusive)")
    backfill.add_argument("--to-week", help="End ISO week (inclusive)")
    _add_pipeline_flags(backfill)
    backfill.set_defaults(command="backfill")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    root = find_project_root()
    if args.project_root:
        root = Path(args.project_root).resolve()
    load_dotenv_file(root)

    if args.command == "run":
        return run_pipeline(_build_run_context(args, root))

    if args.command == "run-all":
        week = args.week or current_iso_week()
        ctx = RunContext(
            product_id="groww",
            iso_week=week,
            window_weeks=10,
            dry_run=args.dry_run,
            skip_mcp=args.skip_mcp or args.dry_run,
            skip_ingest=args.skip_ingest,
            skip_analyze=args.skip_analyze,
            force_analyze=args.force_analyze,
            skip_render=args.skip_render,
            force_render=args.force_render,
            skip_docs=args.skip_docs,
            force_docs=args.force_docs,
            skip_gmail=args.skip_gmail or getattr(args, "skip_email", False),
            force_gmail=args.force_gmail,
            force_stub_llm=args.stub_llm,
            play_count=args.play_count,
            app_store_max_pages=args.app_store_max_pages,
            project_root=root,
        )
        return run_all_products(ctx)

    if args.command == "backfill":
        weeks = resolve_backfill_weeks(
            weeks=args.weeks,
            from_week=args.from_week,
            to_week=args.to_week,
        )
        ctx = _build_run_context(args, root)
        return run_backfill(product_id=args.product, weeks=weeks, base_ctx=ctx)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
