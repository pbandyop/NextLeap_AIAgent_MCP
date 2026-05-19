# Phase 3 — Render — Evaluation

**Phase goal:** Doc section and email teaser payloads without MCP delivery.  
**Implementation plan:** [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md#phase-3--render)

---

## Test plan

| ID | Test | How to run |
|----|------|------------|
| T3.1 | Golden file: Doc section markdown/HTML matches snapshot | `pytest tests/render/test_doc_section.py` |
| T3.2 | Golden file: Gmail teaser subject + body | `pytest tests/render/test_email_teaser.py` |
| T3.3 | Unit: section heading format `{Product} — Weekly Pulse — {iso_week}` | `pytest tests/render/test_heading.py` |
| T3.4 | Unit: idempotency anchor embedded in section | `pytest tests/render/test_anchor.py` |
| T3.5 | Snapshot update process documented (if intentional change) | PR review |

**Fixtures:** `tests/fixtures/pulse_report_groww.json` derived from Phase 2 sample.

---

## Exit criteria

- [x] Rendered Doc block includes: period, themes, quotes, actions, audience blurb per [ProblemStatement.md](../../ProblemStatement.md).
- [x] Email teaser ≤ agreed length (e.g. 15 lines / 500 words) — threshold in config.
- [x] Stable heading and anchor for Phase 4 idempotency.
- [x] No MCP calls in render module (no `pulse_agent.mcp` imports under `phase_03_render/`).
- [ ] Product owner informal review: sample output readable in &lt; 2 minutes.

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | |
| Product/Stakeholder | | | Sample readability |
