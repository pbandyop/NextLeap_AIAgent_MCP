import json

from pulse_agent.phases.phase_01_ingestion.app_store import (
    parse_app_store_json,
    parse_app_store_xml,
)


def test_parse_app_store_xml_fixture(fixtures_dir):
    xml_text = (fixtures_dir / "app_store_reviews.xml").read_text(encoding="utf-8")
    reviews = parse_app_store_xml(xml_text, "1404871703")
    assert len(reviews) == 3  # includes duplicate id; dedupe in normalize step
    assert reviews[0].review_id == "review-1001"
    assert reviews[0].rating == 5
    assert "beginners" in reviews[0].title.lower()


def test_parse_app_store_json_minimal():
    payload = {
        "feed": {
            "entry": [
                {
                    "im:rating": {"label": "4"},
                    "id": {"label": "json-review-1"},
                    "title": {"label": "Nice"},
                    "content": {"label": "Works well."},
                    "updated": {"label": "2026-05-01T00:00:00-07:00"},
                }
            ]
        }
    }
    reviews = parse_app_store_json(payload, "123")
    assert len(reviews) == 1
    assert reviews[0].review_id == "json-review-1"
