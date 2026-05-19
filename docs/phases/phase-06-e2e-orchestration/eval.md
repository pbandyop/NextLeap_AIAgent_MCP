# Phase 6 — E2E Orchestration — Evaluation

**Phase goal:** Single CLI runs full pipeline for any configured product and ISO week.  
**Implementation plan:** [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md#phase-6--end-to-end-orchestration)

---

## Test plan

| ID | Test | How to run |
|----|------|------------|
| T6.1 | E2E staging: full run one product (draft email) | `pulse run --product groww --week 2026-W20` |
| T6.2 | E2E: `--dry-run` skips MCP; still produces report artifacts | CLI + assert files |
| T6.3 | E2E: `--skip-email` / `--skip-docs` flags | CLI |
| T6.4 | Backfill: two different ISO weeks same product | Two runs, two Doc sections |
| T6.5 | All five products: config valid + smoke ingest (can be parallel script) | `pytest tests/test_all_products_config.py` |
| T6.6 | Exit codes: success `0`, fatal `1`, partial `2` (if implemented) | `pytest tests/test_exit_codes.py` |
| T6.7 | Cron doc exists: schedule, timezone IST, failure alerting note | Doc review |

---

## Exit criteria

- [ ] One full successful run per initial product in staging (Docs + draft email minimum).
- [x] Orchestrator order fixed: ingest → analyze → render → docs → gmail → audit.
- [x] Run audit answers: what, when, which week, delivery ids (+ `metrics`).
- [x] Backfill procedure documented for missed weeks (`pulse backfill`, [runbook.md](../../runbook.md)).
- [x] Partial failure behavior defined (doc ok, mail fail → exit `2`).
- [x] Weekly cadence mapped to [scheduling.md](../../scheduling.md).

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | |
| Ops/Owner | | | Schedule agreed |
