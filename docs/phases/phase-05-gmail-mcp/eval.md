# Phase 5 — Gmail MCP — Evaluation

**Phase goal:** Draft or send teaser email via Gmail MCP with Doc deep link; idempotent.  
**Implementation plan:** [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md#phase-5--gmail-mcp-delivery)

---

## Test plan

| ID | Test | How to run |
|----|------|------------|
| T5.1 | Unit: email mapper includes `section_url` from Phase 4 result | `pytest tests/delivery/test_gmail_mapper.py` |
| T5.2 | Integration: `EMAIL_MODE=draft` creates draft | `pytest tests/integration/test_gmail_draft.py -m integration` |
| T5.3 | Integration: re-run same week → no duplicate draft/send | Run twice, verify idempotency |
| T5.4 | Integration: `EMAIL_MODE=send` to test inbox (staging only) | Manual gate |
| T5.5 | Header `X-Pulse-Run-Id` present (if ADR-006) | Inspect draft in Gmail |
| T5.6 | Audit: `gmail_message_id`, `mode` recorded | `pytest tests/test_audit_gmail.py` |

---

## Exit criteria

- [x] Draft mode works in staging for one product + week (`EMAIL_MODE=draft`, `POST /create_email_draft`).
- [x] Email contains teaser bullets and working Doc link (`section_url` replaces `{{DOC_LINK}}`).
- [x] Idempotent re-run does not create duplicate messages (`gmail_delivery.json`).
- [x] Production send gated — `EMAIL_MODE=send` raises until MCP server supports send.
- [x] No direct Gmail API client in agent codebase.
- [ ] Stakeholder test inbox confirms formatting (mobile + desktop spot check).

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | |
| Stakeholder | | | Link + readability |
