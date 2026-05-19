# Phase-wise Implementation Plan — Single Pulse Agent (MCP)

One **Pulse Agent** is built incrementally. Each phase adds capabilities to the same codebase and run loop; we do not spin up separate agents per phase.

**Related docs**

| Doc | Purpose |
|-----|---------|
| [architecture.md](./architecture.md) | Modules, MCP boundaries, idempotency |
| [ProblemStatement.md](./ProblemStatement.md) | Business requirements |
| [decision.md](./decision.md) | Recorded tech/business choices |
| [phases/phase-0X-*/eval.md](./phases/) | Tests and exit criteria per phase |

---

## Overview

| Phase | Name | Outcome |
|-------|------|---------|
| 0 | Foundation | Repo, config, run context, audit skeleton, MCP client smoke test |
| 1 | Ingestion | App Store + Play reviews in normalized store |
| 2 | Analysis | Clusters, LLM themes, validated quotes, action ideas |
| 3 | Render | Doc section + email teaser payloads (no delivery) |
| 4 | Docs MCP | Append idempotent section; heading link for email |
| 5 | Gmail MCP | Draft/send teaser with deep link; email idempotency |
| 6 | E2E orchestration | Full CLI, scheduling hooks, run audit, all products |
| 7 | Hardening | PII, cost limits, staging gates, production readiness |

```text
Phase 0 ──► 1 ──► 2 ──► 3 ──► 4 ──► 5 ──► 6 ──► 7
          ingest  analyze render  Docs  Gmail  E2E   ops
```

---

## Phase 0 — Foundation

**Goal:** Runnable project shell and MCP host wiring without business logic.

**Deliverables**

- Project layout per [architecture.md](./architecture.md) (`src/pulse_agent/`, `config/`, `tests/`).
- `RunContext`, config loading (`products.yaml`, `mcp_servers.yaml`).
- CLI stub: `pulse run --product <id> --week <iso> --dry-run`.
- `mcp_client`: connect to Docs + Gmail MCP servers, `tools/list`, noop or health tool call.
- Audit logger writing `runs/{idempotency_key}.json` (stub fields).

**Eval:** [phases/phase-00-foundation/eval.md](./phases/phase-00-foundation/eval.md)

---

## Phase 1 — Ingestion

**Goal:** Deterministic fetch and normalize reviews for one product over a configurable window.

**Deliverables**

- App Store RSS fetcher + parser.
- Google Play scraper (or chosen library) with rate limits.
- Normalized `Review` model, dedupe by `review_id`, date filter (8–12 weeks).
- Persist raw/normalized snapshot under `data/runs/<idempotency_key>/reviews.json` for replay.
- Orchestrator step `ingest_reviews()`; dry-run prints counts only.
- Per-product fetch caps in `config/products.yaml` (`play_fetch_count`, `app_store_max_pages`); CLI overrides `--play-count`, `--app-store-max-pages`.

**Groww reference ingest (`pulse:groww:2026-W20`)**

| Stage | Count |
|-------|------:|
| App Store + Play fetched | 5,500 |
| After dedupe / window | 5,500 |
| After content filter (normalized) | **1,216** |
| Config | `play_fetch_count: 5000`, `app_store_max_pages: 10` |

**Eval:** [phases/phase-01-ingestion/eval.md](./phases/phase-01-ingestion/eval.md)

---

## Phase 2 — Analysis

**Goal:** Themes, quotes, and actions grounded in ingested text.

**LLM:** [Groq](https://console.groq.com/) chat API (OpenAI-compatible). Default model `llama-3.3-70b-versatile` via `GROQ_API_KEY` / `GROQ_MODEL` in `.env`. Embeddings remain a separate step (local or other provider)—**Groq is not used for vectors or clustering.**

**Strategy (why not “summarize all reviews” in one Groq call)**

Normalized Groww data (~1,216 reviews after bulk ingest) showed:

- ~22% of raw reviews pass the content filter; most drops are reviews under 7 words.
- Critical reviews (1–3★) are fewer but longer and more actionable than generic 5★ praise.
- Sending all reviews to Groq once would be ~40k tokens and risks generic themes.

So Phase 2 uses: **sentiment split → cluster in code → Groq per cluster (8–9 calls)**. See [architecture §6.1–6.1.2](./architecture.md#61-phase-2-analysis-strategy-data--llm).

**Deliverables**

- Embedding pipeline + clustering (UMAP + HDBSCAN or documented fallback).
- **Groq client** + structured prompts: per-cluster theme label, summary, action ideas (JSON schema output).
- **Two-stage synthesis:** cluster in code → Groq names/summarizes each cluster; avoid single-shot “summarize all reviews” unless review count &lt; fallback threshold.
- Quote validator: every quote substring must exist in a source review `title` or `body`.
- `PulseReport` artifact saved to run directory.
- Configurable caps: max reviews, max clusters, max Groq tokens per run / per cluster (see rate-limit table below).
- **Groq rate limiter:** sequential chat calls with inter-request delay, per-run request/token counters, daily token budget from audit rollup, 429 backoff, skip LLM when `PulseReport` already exists (unless `--force-analyze`).
- Document data-shaping and quota rules in [architecture.md §6.1](./architecture.md#61-phase-2-analysis-strategy-data--llm)–[§6.1.2](./architecture.md#612-how-summaries-and-themes-are-produced-groqs-role) (validated against bulk `pulse:groww:2026-W20` ingest).
- Implemented in `src/pulse_agent/phases/phase_02_analysis/`; artifact `pulse_report.json`.

**Groq quotas (`llama-3.3-70b-versatile`) — plan calls to stay under**

| Limit | Value | Phase 2 rule |
|-------|-------|----------------|
| Requests / minute | 30 | Serialize calls; `GROQ_INTER_REQUEST_DELAY_MS` default 2500. |
| Requests / day | 1,000 | Default ≤ 10 Groq calls per product run. |
| Tokens / minute | 12,000 | Target ≤ 900 tokens/completion; ≤ 9k tokens/run. |
| Tokens / day | 100,000 | `GROQ_DAILY_TOKEN_BUDGET` default 80k; fail fast when exceeded. |

**Call budget per product run (default)**

| Path | Groq calls | Notes |
|------|------------|-------|
| Critical bucket (≤ 50 reviews, prompt &lt; 4k tokens) | 1 | Small products only; not used at Groww bulk scale. |
| Critical fallback (Groww: 571 critical) | **≤ 3** | HDBSCAN → top clusters by size; default path for `pulse:groww:2026-W20`. |
| Positive bucket (cluster → top-N) | ≤ 5 | Never send all 645 positive reviews in one prompt. |
| Quote polish | 0 | Code-first quotes only in v1. |
| Executive rollup | 0–1 | Optional; skip first if near caps. |
| **Typical total** | **8–9** | ~7–9k tokens/run for Groww-scale data (1,216 reviews). |

**Data strategy (pre-LLM, validated on Groww `pulse:groww:2026-W20`)**

| Observation | Phase 2 handling |
|-------------|------------------|
| 5,500 fetched → **1,216** after content filter | Analyze only normalized corpus; replay from `reviews.json`. |
| **645** positive / **571** critical after sentiment split | Critical: cluster + ≤3 Groq calls; positive: ≤5 per-cluster calls (§6.1.1). |
| ~44% of kept reviews &lt; 15 words | Themes from clusters, not individual micro-reviews. |
| ~504 reviews at 1–2★; longer than 4–5★ | Oversample low ratings in cluster exemplars sent to Groq; sort themes with pain points first in report. |
| ~40k tokens if all 1,216 reviews sent | **Do not** monolith either bucket; use capped cluster path (§6.1.1). |
| Keyword hints (trading, UI, support, charges) | Use as sanity check on cluster labels, not as primary taxonomy. |
| Re-runs / CI | Load cached `PulseReport`; no duplicate Groq spend unless `--force-analyze`. |
| Bulk ingest for ≥1k normalized | `play_fetch_count: 5000` on Groww; App Store RSS capped ~500/page×10. |

**Eval:** [phases/phase-02-analysis/eval.md](./phases/phase-02-analysis/eval.md)

---

## Phase 3 — Render

**Goal:** Human-ready Doc block and email teaser from `PulseReport` (no MCP writes).

**Deliverables**

- Docs section template: title, period, themes, quotes, actions, “who this helps.”
- Stable section heading format: `{Product} — Weekly Pulse — {iso_week}`.
- Hidden idempotency anchor in section metadata.
- Gmail teaser: subject line, bullet summary, placeholder link (filled in Phase 4).
- Golden-file tests for one product fixture.

**Eval:** [phases/phase-03-render/eval.md](./phases/phase-03-render/eval.md)

**Implementation (done):** `src/pulse_agent/phases/phase_03_render/` — `doc_section.py`, `email_teaser.py`, `heading.py`, `service.py`, `persist.py`; artifacts `doc_section.txt`, `email_teaser.json`, `render_manifest.json`; CLI `--skip-render`, `--force-render`; tests in `tests/render/` with golden files under `tests/fixtures/golden/phase_03/`. Phase 4 will POST `doc_section.content` to the workspace HTTP server ([NextLeap_MCP_Server_Gmail_GDocs](https://github.com/pbandyop/NextLeap_MCP_Server_Gmail_GDocs) `POST /append_to_doc`).

---

## Phase 4 — Google Docs MCP delivery

**Goal:** Append weekly section via Docs MCP only; idempotent re-runs.

**Deliverables**

- `delivery.docs`: typed wrappers for chosen MCP tools (see [decision.md](./decision.md)).
- Resolve/create per-product pulse Doc.
- Append section; retrieve heading URL for Gmail.
- Pre-append check for anchor `pulse:{product}:{iso_week}`.
- Audit fields: `doc_id`, `section_heading`, `section_url`.

**Eval:** [phases/phase-04-docs-mcp/eval.md](./phases/phase-04-docs-mcp/eval.md)

**Implementation (done):** `src/pulse_agent/delivery/docs.py` (mapper), `src/pulse_agent/phases/phase_04_docs_mcp/` (HTTP client, `deliver_docs`, `docs_delivery.json`); CLI `--skip-docs`, `--force-docs`; env `GOOGLE_MCP_BASE_URL`, `PULSE_DOC_ID_{PRODUCT}`.

---

## Phase 5 — Gmail MCP delivery

**Goal:** Draft or send stakeholder email via Gmail MCP only; idempotent re-runs.

**Deliverables**

- `delivery.gmail`: draft and send tools.
- Inject real Doc deep link from Phase 4.
- `EMAIL_MODE=draft|send` from env.
- Idempotency via `X-Pulse-Run-Id` or equivalent (document in decision log).
- Audit fields: `gmail_message_id`, `mode`.

**Eval:** [phases/phase-05-gmail-mcp/eval.md](./phases/phase-05-gmail-mcp/eval.md)

**Implementation (done):** `src/pulse_agent/delivery/gmail.py`, `src/pulse_agent/phases/phase_05_gmail_mcp/`; `POST /create_email_draft`; injects Phase 4 `section_url`; `PULSE_EMAIL_TO` / `PULSE_EMAIL_TO_{PRODUCT}`; `EMAIL_MODE=draft` (send requires MCP server extension); `gmail_delivery.json`; CLI `--skip-gmail`, `--force-gmail`.

---

## Phase 6 — End-to-end orchestration

**Goal:** Single command runs full pipeline for any configured product and ISO week.

**Deliverables**

- Wired orchestrator: ingest → analyze → render → docs → gmail → audit.
- CLI: `--dry-run`, `--skip-email`, `--skip-docs`, `--week`, `--product`.
- Backfill script/flag for historical ISO weeks.
- Cron documentation (e.g. Monday 09:00 IST per product).
- All five initial products in `products.yaml`.
- Exit codes and partial-failure behavior per architecture.

**Eval:** [phases/phase-06-e2e-orchestration/eval.md](./phases/phase-06-e2e-orchestration/eval.md)

**Implementation (done):** `phase_06_e2e/pipeline.py` (full graph, exit 0/1/2), `backfill`, `run-all`, `workspace_smoke`; CLI `pulse run-all`, `pulse backfill`, `--skip-email`; [scheduling.md](./scheduling.md).

---

## Phase 7 — Hardening and production readiness

**Goal:** Safe, cost-bounded, stakeholder-ready operation.

**Deliverables**

- PII scrubber integrated pre-LLM and pre-MCP.
- Prompt-injection hardening in analysis prompts.
- Staging vs production config profiles.
- Production send checklist (manual gate first time).
- Runbook: retry, backfill, MCP server restart.
- Optional: metrics hook (duration, review count, cost estimate).

**Eval:** [phases/phase-07-hardening/eval.md](./phases/phase-07-hardening/eval.md)

**Implementation (done):** `safety/` (PII + injection), `phase_07_hardening/gates.py`, audit `metrics`; [runbook.md](./runbook.md), [production-send-checklist.md](./production-send-checklist.md), `config/environments.yaml`.

---

## Cross-phase practices

- **Decision log:** Any MCP server choice, model choice, or scope change → [decision.md](./decision.md).
- **No phase skip:** Exit criteria in `eval.md` must pass before starting the next phase.
- **Single agent:** New behavior extends `pulse_agent` orchestrator; no second agent repo.
- **Fixtures:** Maintain `tests/fixtures/` for reviews and expected report snippets from Phase 1 onward.

---

## Suggested timeline (indicative)

| Phase | Duration (guide) |
|-------|------------------|
| 0 | 2–3 days |
| 1 | 3–5 days |
| 2 | 5–7 days |
| 3 | 2–3 days |
| 4 | 3–5 days |
| 5 | 2–4 days |
| 6 | 3–4 days |
| 7 | 3–5 days |

Adjust based on MCP server maturity and API access.

---

## Definition of done (project)

- [ ] All phase `eval.md` checklists signed off.
- [ ] One successful production-like run per initial product (at least staging).
- [ ] Re-run same `(product, iso_week)` produces no duplicate Doc section or email.
- [ ] [ProblemStatement.md](./ProblemStatement.md) success criteria met.
- [ ] No Google REST credentials or clients in the Pulse Agent repository.
