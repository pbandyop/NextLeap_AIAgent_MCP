import json

from pulse_agent.phases.phase_01_ingestion.play_store import parse_play_store_records


def test_parse_play_store_fixture(fixtures_dir):
    records = json.loads((fixtures_dir / "play_reviews.json").read_text(encoding="utf-8"))
    reviews = parse_play_store_records(records)
    assert len(reviews) == 3
    assert reviews[0].review_id == "play-2001"
    assert reviews[1].rating == 1
