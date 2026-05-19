# Phase 7 — Hardening — Evaluation

**Phase goal:** PII safety, cost limits, staging/production gates, production readiness.  
**Implementation plan:** [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md#phase-7--hardening-and-production-readiness)

---

## Test plan

| ID | Test | How to run |
|----|------|------------|
| T7.1 | Unit: PII scrubber redacts emails, phones on fixture text | `pytest tests/safety/test_pii.py` |
| T7.2 | Unit: prompt-injection sample reviews do not change system behavior | `pytest tests/safety/test_injection.py` |
| T7.3 | Run exceeds token budget → graceful failure with clear log | `pytest tests/analysis/test_limits.py` |
| T7.4 | Production checklist completed before first `EMAIL_MODE=send` | Manual checklist artifact |
| T7.5 | Runbook: MCP restart, retry, backfill — dry run by second engineer | Doc review + tabletop |
| T7.6 | Security: no secrets in repo (`gitleaks` or manual scan) | CI / manual |
| T7.7 | Production pilot: one product, one week, real recipients (limited list) | Monitored run |

---

## Exit criteria

- [x] PII scrubbing applied before LLM and before MCP publish (`safety/`, ingest + publish path).
- [x] Staging defaults to draft; production send requires `PULSE_PRODUCTION_SEND_APPROVED`.
- [x] Runbook in [runbook.md](../../runbook.md); checklist in [production-send-checklist.md](../../production-send-checklist.md).
- [x] Cost/token limits logged per run in audit `metrics` (Groq counters from Phase 2).
- [ ] Project definition of done in [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md) satisfied.
- [ ] All phase evals 0–6 signed off.

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | |
| Security/Compliance | | | If required |
| Product owner | | | Production pilot approved |
