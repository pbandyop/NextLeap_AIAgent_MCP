import os

import pytest

from pulse_agent.config.loader import load_config
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_03_render.persist import load_rendered
from pulse_agent.phases.phase_04_docs_mcp.service import DocsDeliveryError, deliver_docs


@pytest.mark.integration
def test_docs_append_live(project_root):
    doc_id = os.environ.get("PULSE_DOC_ID_GROWW", "").strip()
    if not doc_id:
        pytest.skip("Set PULSE_DOC_ID_GROWW for live Docs integration test")

    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=project_root,
    )
    rendered = load_rendered(ctx)
    if rendered is None:
        pytest.skip("No render artifacts; run Phase 3 first")

    config = load_config(project_root)
    product = config.get_product("groww")

    result = deliver_docs(ctx, rendered, product, config, force_deliver=False)
    assert result.status == "success"
    assert result.doc_id == doc_id
    assert result.section_url


@pytest.mark.integration
def test_docs_append_idempotent_second_run(project_root):
    doc_id = os.environ.get("PULSE_DOC_ID_GROWW", "").strip()
    if not doc_id:
        pytest.skip("Set PULSE_DOC_ID_GROWW for live Docs integration test")

    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=project_root,
    )
    rendered = load_rendered(ctx)
    if rendered is None:
        pytest.skip("No render artifacts")

    config = load_config(project_root)
    product = config.get_product("groww")

    first = deliver_docs(ctx, rendered, product, config, force_deliver=False)
    second = deliver_docs(ctx, rendered, product, config, force_deliver=False)
    assert second.doc_id == first.doc_id
    assert second.section_url == first.section_url
