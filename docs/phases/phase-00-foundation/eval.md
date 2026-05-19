# Phase 0 — Foundation — Evaluation

**Phase goal:** Runnable shell, config, MCP client smoke test, audit skeleton.  
**Implementation plan:** [phase-wiseimplementationplan.md](../../phase-wiseimplementationplan.md#phase-0--foundation)

---

## Test plan

| ID | Test | How to run |
|----|------|------------|
| T0.1 | Unit: config loads valid `products.yaml` and `mcp_servers.yaml` | `pytest tests/test_config.py` |
| T0.2 | Unit: `RunContext` builds `idempotency_key` = `pulse:{product}:{iso_week}` | `pytest tests/test_run_context.py` |
| T0.3 | Integration: MCP client connects to Docs server and lists tools | `pytest tests/integration/test_mcp_docs.py -m integration` |
| T0.4 | Integration: MCP client connects to Gmail server and lists tools | `pytest tests/integration/test_mcp_gmail.py -m integration` |
| T0.5 | CLI: `pulse run --product groww --week 2026-W20 --dry-run` exits 0, writes audit stub | Manual / `pytest tests/test_cli_dry_run.py` |
| T0.6 | No Google REST imports in `src/pulse_agent` | `rg "googleapiclient|google.oauth2" src/` → no matches |

**Integration tests** require MCP servers running locally per `config/mcp_servers.yaml` (document setup in README when added).

---

## Exit criteria

- [ ] Repository layout matches [architecture.md](../../architecture.md) §4.
- [ ] At least one product entry exists in `config/products.yaml`.
- [ ] MCP Docs and Gmail servers reachable; `tools/list` returns non-empty tool sets.
- [ ] Dry-run creates `runs/pulse:groww:2026-W20.json` (or equivalent) with `status: stub` or `dry_run`.
- [ ] CI runs unit tests without MCP; integration tests marked and optional/skippable.
- [ ] Phase 0 sign-off recorded in audit or PR description.

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | |
| Reviewer | | | |
