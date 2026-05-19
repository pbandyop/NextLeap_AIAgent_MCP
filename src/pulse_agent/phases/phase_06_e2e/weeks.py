from __future__ import annotations

import re
from datetime import date, timedelta

ISO_WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$", re.IGNORECASE)


def parse_iso_week(label: str) -> tuple[int, int]:
    match = ISO_WEEK_RE.match(label.strip())
    if not match:
        raise ValueError(f"Invalid ISO week label: {label!r} (expected e.g. 2026-W20)")
    return int(match.group(1)), int(match.group(2))


def format_iso_week(year: int, week: int) -> str:
    if week < 1 or week > 53:
        raise ValueError(f"ISO week number out of range: {week}")
    return f"{year}-W{week:02d}"


def current_iso_week(reference: date | None = None) -> str:
    ref = reference or date.today()
    iso = ref.isocalendar()
    return format_iso_week(iso.year, iso.week)


def parse_week_list(spec: str) -> list[str]:
    """Comma-separated ISO weeks, e.g. '2026-W18,2026-W19'."""
    weeks: list[str] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        y, w = parse_iso_week(part)
        weeks.append(format_iso_week(y, w))
    if not weeks:
        raise ValueError("No ISO weeks provided")
    return weeks


def expand_week_range(from_week: str, to_week: str) -> list[str]:
    y1, w1 = parse_iso_week(from_week)
    y2, w2 = parse_iso_week(to_week)
    start = date.fromisocalendar(y1, w1, 1)
    end = date.fromisocalendar(y2, w2, 1)
    if end < start:
        raise ValueError(f"from_week {from_week} is after to_week {to_week}")

    weeks: list[str] = []
    current = start
    while current <= end:
        iso = current.isocalendar()
        label = format_iso_week(iso.year, iso.week)
        if not weeks or weeks[-1] != label:
            weeks.append(label)
        current += timedelta(days=7)
    return weeks
