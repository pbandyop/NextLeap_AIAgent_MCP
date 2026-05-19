# Decision Log

Record **tech and business decisions** here so the team does not re-debate settled choices. Add a new entry at the top (newest first).

**Template**

```markdown
## ADR-NNN — Title (YYYY-MM-DD)

**Status:** Proposed | Accepted | Superseded by ADR-XXX

**Context:** What problem or fork we faced.

**Decision:** What we chose.

**Consequences:** Tradeoffs, follow-ups, owners.
```

---

## ADR-001 — Single Pulse Agent, not multi-agent (2026-05-16)

**Status:** Accepted

**Context:** The weekly pulse could be split into separate services (ingest, summarize, deliver) or multiple LLM agents.

**Decision:** One **Pulse Agent** process with a fixed phase graph (`orchestrator`) and internal modules. One run ID and one audit trail per `(product, iso_week)`. LLM is used inside Analyze/Render steps, not as separate autonomous agents.

**Consequences:** Simpler ops and testing; less flexible ad-hoc replanning. Revisit only if requirements demand dynamic tool selection beyond MCP Docs/Gmail.

---

## ADR-002 — Google Workspace via MCP only (2026-05-16)

**Status:** Accepted

**Context:** Docs and Gmail could be integrated with in-process Google REST clients.

**Decision:** All Doc writes and Gmail send/draft go through **Google Docs MCP** and **Gmail MCP** servers. OAuth and quotas live in MCP server config, not in this repo.

**Consequences:** Depends on MCP server availability and tool schemas; agent must map render output to MCP tools. Clear security boundary.

**Follow-up:** Record chosen MCP server implementations and exact tool names once selected (ADR-003).

---

## ADR-003 — MCP server selection: workspace HTTP server (2026-05-18)

**Status:** Accepted

**Context:** Need concrete Docs and Gmail delivery with OAuth outside the Pulse agent repo.

**Decision:** Use deployed **[NextLeap_MCP_Server_Gmail_GDocs](https://github.com/pbandyop/NextLeap_MCP_Server_Gmail_GDocs)** over **HTTP** (Railway: `https://saksham-mcp-server-production-b243.up.railway.app/`). Config key `google_workspace` in `config/mcp_servers.yaml`; override base URL with `GOOGLE_MCP_BASE_URL`.

| Tool | HTTP | Request body | Response |
|------|------|--------------|----------|
| Health | `GET /` | — | `{ message, credentials_ready, token_configured, ... }` |
| `append_to_doc` | `POST /append_to_doc` | `{ "doc_id": str, "content": str }` | `{ "status": "success", "message", "document_id" }` |
| `create_email_draft` | `POST /create_email_draft` | `{ "to", "subject", "body" }` | (Phase 5) |

Per-product Doc ID: `PULSE_DOC_ID_{PRODUCT}` env or `google_doc_id` in `products.yaml`. Agent builds `section_url` as `https://docs.google.com/document/d/{doc_id}/edit` (+ optional heading fragment). Idempotency: local `docs_delivery.json` keyed by `pulse:{product}:{iso_week}` and anchor comment (server has no read API).

**Consequences:** Phase 0 stdio `npx` servers remain for optional smoke only. No `googleapiclient` in this repo. Duplicate append possible if `--force-docs` without server-side dedupe.

**Gmail (Phase 5):** `POST /create_email_draft` with `{ "to", "subject", "body" }` (plain text). Recipient from `PULSE_EMAIL_TO` or `PULSE_EMAIL_TO_{PRODUCT}`. Idempotency: local `gmail_delivery.json` + footer line `X-Pulse-Run-Id: pulse:{product}:{iso_week}` in body (MCP server does not set SMTP headers). `EMAIL_MODE=send` not implemented on HTTP server yet — use `draft` and send manually from Gmail.

---

## ADR-004 — Orchestration style: fixed phase graph first (2026-05-16)

**Status:** Accepted

**Context:** Could use an LLM planner to decide steps each run.

**Decision:** **Fixed phase graph** for v1 (ingest → analyze → render → docs → gmail). LLM only for content synthesis, not step ordering.

**Consequences:** Predictable tests and evals; easier idempotency. LLM orchestration may be reconsidered in a future ADR.

---

## ADR-005 — Email default in non-production (2026-05-16)

**Status:** Accepted

**Context:** Risk of accidental stakeholder email during development.

**Decision:** Non-production environments default `EMAIL_MODE=draft`. Production send requires explicit env flag and checklist (Phase 7).

**Consequences:** Stakeholders may need manual “send draft” until production gate is cleared.

---

## ADR-006 — Idempotency keys (2026-05-16)

**Status:** Accepted

**Context:** Weekly cron and backfill must not duplicate artifacts.

**Decision:** Primary key: `pulse:{product_id}:{iso_week}`. Doc sections use matching hidden anchor; Gmail uses `X-Pulse-Run-Id` header (or equivalent supported by Gmail MCP).

**Consequences:** Requires MCP tools or pre-checks that can detect existing section/message.

---

## ADR-007 — Initial product set (2026-05-16)

**Status:** Accepted

**Context:** Which fintech apps to support at launch.

**Decision:** INDMoney, Groww, PowerUp Money, Wealth Monitor, Kuvera — per [ProblemStatement.md](./ProblemStatement.md).

**Consequences:** Five doc templates and store IDs in `products.yaml`; Play/App Store identifiers must be verified per product in Phase 1.

---

## ADR-008 — Clustering stack (2026-05-17)

**Status:** Accepted

**Context:** Need thematic grouping of reviews at scale.

**Decision:** Primary path: `sentence-transformers` (`all-MiniLM-L6-v2`) → UMAP → HDBSCAN. Fallback when optional deps unavailable or clustering fails: TF-IDF + scikit-learn KMeans. Sentiment buckets (4–5★ vs 1–3★) clustered separately before Groq labeling.

**Consequences:** Optional `[analysis]` extra in `pyproject.toml` for UMAP/HDBSCAN/sentence-transformers; core path uses numpy + scikit-learn only.

---

## ADR-009 — LLM provider: Groq for Phase 2 analysis (2026-05-17)

**Status:** Accepted

**Context:** Theme naming, cluster summaries, and action ideas need a fast, cost-effective chat API. Embeddings/clustering are a separate concern (ADR-008).

**Decision:** Use **Groq** OpenAI-compatible chat API for all Phase 2 LLM calls.

| Setting | Value |
|---------|--------|
| Provider | Groq (`https://api.groq.com/openai/v1`) |
| Default model | `llama-3.3-70b-versatile` |
| Env | `GROQ_API_KEY`, optional `GROQ_MODEL` |
| Temperature | Low (0–0.3) for structured theme JSON |
| Call pattern | Per-cluster prompts after embedding/HDBSCAN; not full-corpus unless review count &lt; 40 |

Embeddings: **not** Groq—use local `sentence-transformers` or a dedicated embedding API.

**Consequences:** Fast iteration and low latency; rate limits apply on Groq free/paid tiers (see architecture §6.1.1). Quote validation remains mandatory (Groq does not replace substring checks). Groww reference corpus (`pulse:groww:2026-W20`): **1,216** normalized reviews → **8–9** Groq calls/run (3 critical clusters + 5 positive), not full-corpus.
