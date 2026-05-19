import pytest

from pulse_agent.phases.phase_02_analysis.parser import LlmParseError, parse_theme_response


def test_parse_theme_json():
    raw = '{"label": "Login issues", "summary": "Users report auth failures.", "actions": ["Fix OTP"]}'
    parsed = parse_theme_response(raw)
    assert parsed["label"] == "Login issues"
    assert "auth" in parsed["summary"]
    assert parsed["actions"] == ["Fix OTP"]


def test_parse_theme_from_fenced_json():
    raw = '```json\n{"label": "Fees", "summary": "High charges.", "actions": ["Review pricing"]}\n```'
    parsed = parse_theme_response(raw)
    assert parsed["label"] == "Fees"


def test_parse_theme_requires_label():
    with pytest.raises(LlmParseError):
        parse_theme_response('{"summary": "missing label", "actions": []}')
