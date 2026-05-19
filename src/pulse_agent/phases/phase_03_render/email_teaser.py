from __future__ import annotations

import html

from pulse_agent.config.loader import ProductConfig
from pulse_agent.models.report import PulseReport
from pulse_agent.phases.phase_03_render.config import RenderLimits

DOC_LINK_PLACEHOLDER = "{{DOC_LINK}}"


def build_email_teaser(
    report: PulseReport,
    product: ProductConfig,
    *,
    iso_week: str,
    review_count: int,
    limits: RenderLimits | None = None,
) -> tuple[str, str, str]:
    """Returns (subject, body_plain, body_html)."""
    limits = limits or RenderLimits.from_env()
    theme_count = len(report.themes)
    critical = [t for t in report.themes if t.sentiment == "critical"]
    positive = [t for t in report.themes if t.sentiment == "positive"]

    subject = (
        f"{product.display_name} Weekly Pulse — {iso_week} "
        f"({theme_count} themes, {review_count} reviews)"
    )

    plain_lines = [
        f"Weekly app-store pulse for {product.display_name} ({iso_week}).",
        f"Based on {review_count} filtered reviews.",
        "",
        "Top critical themes:",
    ]
    for theme in critical[:3]:
        plain_lines.append(f"  • {theme.label} ({theme.review_count} reviews)")
    plain_lines.append("")
    plain_lines.append("Top positive themes:")
    for theme in positive[:3]:
        plain_lines.append(f"  • {theme.label} ({theme.review_count} reviews)")
    plain_lines.extend(
        [
            "",
            f"Full report: {DOC_LINK_PLACEHOLDER}",
            "",
            "— Pulse Agent (automated)",
        ]
    )
    body_plain = _truncate_teaser("\n".join(plain_lines), limits)

    html_parts = [
        f"<p>Weekly app-store pulse for <strong>{html.escape(product.display_name)}</strong> "
        f"({html.escape(iso_week)}).</p>",
        f"<p>Based on <strong>{review_count}</strong> filtered reviews.</p>",
        "<p><strong>Top critical themes:</strong></p><ul>",
    ]
    for theme in critical[:3]:
        html_parts.append(
            f"<li>{html.escape(theme.label)} ({theme.review_count} reviews)</li>"
        )
    html_parts.append("</ul><p><strong>Top positive themes:</strong></p><ul>")
    for theme in positive[:3]:
        html_parts.append(
            f"<li>{html.escape(theme.label)} ({theme.review_count} reviews)</li>"
        )
    html_parts.append(
        f'</ul><p><a href="{DOC_LINK_PLACEHOLDER}">Read full report in Google Docs</a></p>'
        "<p><em>Pulse Agent (automated)</em></p>"
    )
    body_html = _truncate_teaser("".join(html_parts), limits, is_html=True)

    return subject, body_plain, body_html


def _truncate_teaser(text: str, limits: RenderLimits, *, is_html: bool = False) -> str:
    if not is_html:
        lines = text.splitlines()
        if len(lines) > limits.email_max_lines:
            lines = lines[: limits.email_max_lines]
            lines.append("…")
        text = "\n".join(lines)
    words = text.split()
    if len(words) > limits.email_max_words:
        text = " ".join(words[: limits.email_max_words]) + " …"
    return text
