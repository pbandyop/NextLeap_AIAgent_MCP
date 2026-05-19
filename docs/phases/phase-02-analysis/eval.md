# Phase 2 — Analysis — Evaluation

**Phase goal:** Clusters, LLM themes, validated quotes, action ideas → `PulseReport`.  
**Implementation plan:** [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md#phase-2--analysis)

---

## Test plan

| ID | Test | How to run |
|----|------|------------|
| T2.1 | Unit: embedding + clustering on synthetic fixture reviews | `pytest tests/analysis/test_clustering.py` |
| T2.2 | Unit: quote validator rejects hallucinated substring | `pytest tests/analysis/test_quote_validation.py` |
| T2.3 | Unit: LLM output parser (themes, actions) on mocked response | `pytest tests/analysis/test_llm_parser.py` |
| T2.4 | Integration: full analyze on Phase 1 fixture `reviews.json` | `pytest tests/analysis/test_analyze_integration.py` |
| T2.5 | Property: every quote in report exists in source review bodies | Automated in T2.2/T2.4 |
| T2.6 | Cost guard: run aborts or truncates when review count &gt; configured max | `pytest tests/analysis/test_limits.py` |

**Optional live test:** `pytest -m live_llm` with API key in env (not in CI by default).

---

## Exit criteria

- [ ] `PulseReport` artifact saved per run with ≥ 3 themes (or documented minimum when data sparse).
- [ ] 100% of published quotes pass substring validation against ingested reviews.
- [ ] Action ideas present and tied to themes (structured output, not free-form only).
- [ ] ADR for clustering stack and LLM model marked **Accepted** in [decision.md](../../decision.md).
- [ ] Token/cost limits documented in config and enforced in test T2.6.
- [ ] Analysis step runnable via orchestrator after ingest on dry-run path (no MCP).

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | |
| Reviewer | | | |
