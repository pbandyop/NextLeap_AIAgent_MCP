import pytest

from pulse_agent.phases.phase_06_e2e.weeks import (
    expand_week_range,
    format_iso_week,
    parse_iso_week,
    parse_week_list,
)


def test_parse_iso_week():
    assert parse_iso_week("2026-W20") == (2026, 20)
    assert format_iso_week(2026, 20) == "2026-W20"


def test_parse_week_list():
    assert parse_week_list("2026-W18, 2026-W19") == ["2026-W18", "2026-W19"]


def test_expand_week_range():
    weeks = expand_week_range("2026-W19", "2026-W20")
    assert "2026-W19" in weeks
    assert "2026-W20" in weeks


def test_invalid_week_raises():
    with pytest.raises(ValueError):
        parse_iso_week("not-a-week")
