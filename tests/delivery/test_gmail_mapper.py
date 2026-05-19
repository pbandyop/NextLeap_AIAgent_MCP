from pulse_agent.delivery.gmail import (
    PULSE_RUN_ID_HEADER,
    inject_doc_link,
    map_render_to_gmail_payload,
)
from pulse_agent.models.delivery import DocsDeliveryResult
from pulse_agent.phases.phase_03_render.email_teaser import DOC_LINK_PLACEHOLDER


def test_inject_doc_link_replaces_placeholder(rendered_groww):
    url = "https://docs.google.com/document/d/abc/edit"
    body = inject_doc_link(rendered_groww.email_teaser.body_plain, url)
    assert DOC_LINK_PLACEHOLDER not in body
    assert url in body


def test_map_render_includes_section_url_and_run_id(rendered_groww):
    docs = DocsDeliveryResult(
        doc_id="abc",
        section_heading="Groww — Weekly Pulse — 2026-W20",
        section_url="https://docs.google.com/document/d/abc/edit#heading=x",
        anchor="<!-- pulse:groww:2026-W20 -->",
        idempotency_key="pulse:groww:2026-W20",
        status="success",
    )
    payload = map_render_to_gmail_payload(
        rendered_groww,
        docs,
        to="pm@example.com",
        idempotency_key="pulse:groww:2026-W20",
        run_id="run-uuid-1",
    )
    assert payload.to == "pm@example.com"
    assert docs.section_url in payload.body
    assert PULSE_RUN_ID_HEADER in payload.body
    assert "pulse:groww:2026-W20" in payload.body
    assert "run-uuid-1" in payload.body
    assert payload.subject == rendered_groww.email_teaser.subject
