from pulse_agent.delivery.docs import (
    AppendToDocPayload,
    build_section_url,
    map_render_to_append_payload,
)


def test_map_render_to_append_payload(rendered_groww, groww_product):
    payload = map_render_to_append_payload(rendered_groww, groww_product.google_doc_id)
    assert isinstance(payload, AppendToDocPayload)
    assert payload.doc_id == "test-doc-id-abc123"
    assert payload.content == rendered_groww.doc_section.content
    assert "<!-- pulse:groww:2026-W20 -->" in payload.content
    assert "Groww — Weekly Pulse — 2026-W20" in payload.content


def test_build_section_url():
    url = build_section_url("abc123", "Groww — Weekly Pulse — 2026-W20")
    assert url.startswith("https://docs.google.com/document/d/abc123/edit")
    assert "#heading=" in url
