# Phase 4 — Google Docs MCP — Evaluation

**Phase goal:** Append idempotent weekly section via Docs MCP only.  
**Implementation plan:** [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md#phase-4--google-docs-mcp-delivery)

---

## Test plan

| ID | Test | How to run |
|----|------|------------|
| T4.1 | Unit: map `PulseReport` + render output to MCP tool arguments (mocked) | `pytest tests/delivery/test_docs_mapper.py` |
| T4.2 | Integration: append section to test Doc | `pytest tests/integration/test_docs_append.py -m integration` |
| T4.3 | Integration: re-run same `idempotency_key` → no second section | Same as T4.2, run twice |
| T4.4 | Integration: returned `section_url` opens correct heading (manual) | Checklist in test notes |
| T4.5 | Audit: run JSON contains `doc_id`, `section_heading`, `section_url` | `pytest tests/test_audit_docs.py` |
| T4.6 | No direct Google API client in agent | `rg "googleapiclient|docs\.v1" src/` → no matches |

**Prerequisites:** ADR-003 MCP server **Accepted**; test Doc ID in staging config.

---

## Exit criteria

- [x] First run appends section with correct heading and visible content.
- [x] Second run with same `(product, iso_week)` is no-op or returns existing section (idempotent via `docs_delivery.json`).
- [x] Deep link / heading URL suitable for Gmail Phase 5 (`section_url` in audit + `docs_delivery.json`).
- [x] Tool names and payloads documented in [decision.md](../../decision.md) (ADR-003).
- [x] Failure path: MCP down → run fails with non-zero exit; audit `status: failed` with error detail.

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | |
| Reviewer | | | |
