from __future__ import annotations

from pulse_agent.config.loader import ProductConfig
from pulse_agent.models.report import PulseReport, Theme, ValidatedQuote
from pulse_agent.phases.phase_03_render.config import RenderLimits
from pulse_agent.phases.phase_03_render.heading import section_anchor, section_heading


def build_doc_section(
    report: PulseReport,
    product: ProductConfig,
    *,
    iso_week: str,
    review_count: int,
    limits: RenderLimits | None = None,
) -> tuple[str, str, str]:
    """
    Returns (heading, anchor, content) for Google Docs append.
    Content is plain text suitable for POST /append_to_doc on the workspace server.
    """
    limits = limits or RenderLimits.from_env()
    product_id = str(report.metadata.get("product_id") or product.product_id)
    heading = section_heading(product.display_name, iso_week)
    anchor = section_anchor(product_id, iso_week)

    quotes_by_cluster: dict[str, list[ValidatedQuote]] = {}
    for quote in report.quotes[: limits.max_quotes_in_doc]:
        quotes_by_cluster.setdefault(quote.cluster_id, []).append(quote)

    lines: list[str] = [
        anchor,
        "",
        heading,
        "=" * len(heading),
        "",
        f"Period: {iso_week}",
        f"Reviews analyzed: {review_count}",
        f"Themes identified: {len(report.themes)}",
        "",
        "Who this helps",
        "-----------",
        "Product managers prioritizing roadmap items, support leads tracking recurring issues,",
        "and leadership scanning weekly sentiment without reading raw app-store feeds.",
        "",
    ]

    critical = [t for t in report.themes if t.sentiment == "critical"]
    positive = [t for t in report.themes if t.sentiment == "positive"]

    if critical:
        lines.extend(_theme_block("Critical themes (action priority)", critical, quotes_by_cluster, limits))
    if positive:
        lines.extend(_theme_block("Positive themes", positive, quotes_by_cluster, limits))

    lines.extend(_rollup_actions(report.themes, limits))
    content = "\n".join(lines).strip() + "\n"
    return heading, anchor, content


def _theme_block(
    title: str,
    themes: list[Theme],
    quotes_by_cluster: dict[str, list[ValidatedQuote]],
    limits: RenderLimits,
) -> list[str]:
    out = [title, "-" * len(title), ""]
    for theme in themes:
        out.append(f"## {theme.label} ({theme.review_count} reviews)")
        out.append(theme.summary.strip())
        out.append("")
        out.append("Suggested actions:")
        for action in theme.actions[: limits.max_actions_per_theme]:
            out.append(f"  • {action}")
        cluster_quotes = quotes_by_cluster.get(theme.cluster_id, [])
        if cluster_quotes:
            out.append("")
            out.append("Representative quote:")
            q = cluster_quotes[0]
            out.append(f'  "{q.text}" ({q.rating}★, {q.source})')
        out.append("")
    return out


def _rollup_actions(themes: list[Theme], limits: RenderLimits) -> list[str]:
    seen: set[str] = set()
    rolled: list[str] = []
    for theme in themes:
        for action in theme.actions:
            key = action.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            rolled.append(action)
            if len(rolled) >= 10:
                break
        if len(rolled) >= 10:
            break
    lines = ["Top suggested actions (deduplicated)", "--------------------------------", ""]
    for item in rolled:
        lines.append(f"  • {item}")
    lines.append("")
    return lines
