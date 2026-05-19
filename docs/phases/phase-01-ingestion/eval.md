# Phase 1 — Ingestion — Evaluation

**Phase goal:** Fetch and normalize App Store + Play reviews for a configurable window.  
**Implementation plan:** [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md#phase-1--ingestion)

---

## Test plan

| ID | Test | How to run |
|----|------|------------|
| T1.1 | Unit: App Store RSS parser on fixture XML | `pytest tests/ingestion/test_app_store.py` |
| T1.2 | Unit: Play scraper/parser on fixture HTML/JSON | `pytest tests/ingestion/test_play_store.py` |
| T1.3 | Unit: dedupe by `review_id`; date window filter | `pytest tests/ingestion/test_normalize.py` |
| T1.4 | Integration: live fetch one product (small window) — optional | `pytest -m live_ingestion` |
| T1.5 | Orchestrator: `ingest_reviews()` writes `reviews.json` under run dir | `pytest tests/test_ingest_step.py` |
| T1.6 | Dry-run CLI prints `review_count` by source | Manual |

**Fixtures:** `tests/fixtures/app_store_reviews.xml`, `tests/fixtures/play_reviews.json` (committed, no PII).

---

## Exit criteria

- [ ] Normalized schema matches [architecture.md](../../architecture.md) §6 `Review`.
- [ ] One product (e.g. Groww) ingests ≥ N reviews (define N in run, e.g. 50) from at least one store in staging/live test.
- [ ] Duplicate fetches do not inflate count (dedupe verified).
- [ ] Reviews outside 8–12 week window excluded when configured.
- [ ] Run artifact `data/runs/<idempotency_key>/reviews.json` reproducible from CLI.
- [ ] Store IDs for all five products documented or verified in [decision.md](../../decision.md).

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | |
| Reviewer | | | |
