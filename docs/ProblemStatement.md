# Problem Statement

## Weekly Product Review Pulse

Product, support, and leadership teams at fintech companies need a repeatable view of what customers say in public app-store reviews—not a one-off spreadsheet or manual copy-paste each week. We are building an **automated weekly “pulse”** that ingests reviews, clusters and summarizes them with an LLM, and **delivers** a one-page insight report to stakeholders through **Google Workspace**.

**Supported products (initial):** INDMoney, Groww, PowerUp Money, Wealth Monitor, Kuvera.

---

## Core integration model: MCP, not Google APIs in the agent

Delivery to Google Docs and Gmail is **not** implemented with embedded Google REST clients, OAuth tokens, or API calls inside the pulse agent. Instead, the agent acts as an **MCP host** (client) and invokes **dedicated MCP servers** that own Google authentication and Workspace operations:

| Concern | Approach |
|--------|----------|
| App Store / Play review data | Ingestion modules (RSS, scraper, etc.)—outside Google |
| Clustering, themes, quotes, actions | LLM + embeddings pipeline—inside the agent |
| Report and email **content** | Structured rendering in the agent (ready for MCP tool payloads) |
| **Writing to Google Docs** | **Google Docs MCP server** only |
| **Sending Gmail** | **Gmail MCP server** only |

**Model Context Protocol (MCP)** standardizes how the agent discovers and calls tools (e.g. append a section to a document, create or send a message). OAuth secrets, refresh tokens, and Google API quotas live in the **MCP servers’ configuration**, not in the pulse codebase. The agent orchestrates the weekly run and passes rendered content to MCP tools; it does not call the Docs or Gmail REST APIs directly.

This project is explicitly an **MCP-based agent** (`NextLeap_AIAgent_MCP`): Google Workspace is integrated **through MCP servers**, which is the architectural constraint for the entire problem—not an optional transport layer.

---

## Objective

Give stakeholders a **weekly snapshot** of store-review voice: top themes, representative quotes (grounded in real review text), and actionable ideas—archived in a living Google Doc and announced by email with a link to the canonical section.

---

## What the system does

1. **Ingest** public reviews from the last 8–12 weeks (configurable) per product from:
   - **Apple App Store** (e.g. iTunes customer-reviews RSS)
   - **Google Play** (scraper-based)
2. **Analyze** feedback with embeddings and density-based clustering (e.g. UMAP + HDBSCAN), then use an LLM to name themes, pull verbatim quotes, and propose actions—with validation so quotes must appear in source review text.
3. **Render** a concise one-page narrative: top themes, quotes, action ideas, and a short “who this helps” section.
4. **Deliver** only via MCP:
   - **Google Docs MCP** — Append each week’s report as a new dated section to one running document per product (e.g. *Weekly Review Pulse — Groww*). The Doc is the system of record and preserves history.
   - **Gmail MCP** — Send a short stakeholder email with a deep link to the new section in that Doc (heading link). The email teases the pulse; the Doc holds the full report.

```text
[Reviews: App Store + Play] → [Cluster + LLM] → [Report renderer]
                                                      ↓
                              Google Docs MCP  ←  MCP host (agent)
                              Gmail MCP      ←
```

---

## Modular responsibilities

| Layer | Responsibility |
|-------|----------------|
| Data retrieval | Ingestion (App Store + Play Store) |
| Reasoning | Clustering + LLM summarization |
| Output generation | Report body + email teaser (structured for Docs MCP; HTML/text for Gmail MCP) |
| Human-visible delivery | **MCP tools only** → Google Docs MCP + Gmail MCP |

---

## Key requirements

- **MCP-only Google delivery:** Append to the shared Google Doc and send (or draft) Gmail **only** through the respective MCP servers’ tools (e.g. document batch update, draft/create/send as defined in server tool schemas and `docs/architecture.md`).
- **Weekly cadence:** Once per product per week (e.g. scheduled Monday morning IST), with a CLI for backfill of any ISO week.
- **Idempotent runs:** Re-running the same product + ISO week must not duplicate Doc sections or emails—stable section anchors in the Doc and run-scoped idempotency for Gmail (see architecture).
- **Auditable:** Each run records MCP/delivery identifiers (e.g. doc heading, message ids) and metadata for “what was sent when, for which week?”
- **Safety and quality:** PII scrubbing before LLM and before publishing; reviews treated as data, not instructions; cost/token limits per run.

---

## Non-goals (explicit)

- Calling **Google Docs or Gmail REST APIs** from the pulse agent (all Workspace writes go through MCP).
- A generic Google Workspace product beyond pulse needs (Docs append + Gmail send/draft via MCP).
- Real-time streaming analytics or a BI dashboard (the running Google Doc is the living artifact).
- Social sources (Twitter, Reddit, etc.) in initial scope.
- Storing Google OAuth credentials in the agent repository—they belong in MCP server configuration.

---

## Who this helps

| Audience | Value |
|----------|--------|
| Product | Prioritize roadmap from recurring themes |
| Support | Spot repeating complaints and quality issues |
| Leadership | Fast health snapshot tied to customer voice |

---

## Sample output (illustrative)

**Groww — Weekly Review Pulse**  
*Period: Last 8–12 weeks (rolling window)*

**Top themes**

- App performance & bugs — Lag, crashes during trading hours; login/session timeouts.
- Customer support friction — Slow responses; unresolved tickets.
- UX & feature gaps — Confusing navigation for portfolio insights; missing advanced analytics.

**Real user quotes**

- “The app freezes exactly when the market opens, very frustrating.”
- “Support takes days to reply and doesn’t solve the issue.”
- “Good for beginners but lacks detailed analysis tools.”

**Action ideas**

- Stabilize peak-time performance — Scale infra during market hours; improve crash visibility.
- Improve support SLA visibility — Expected response time in-app; ticket status tracking.
- Enhance power-user features — Advanced portfolio analytics; clearer investments navigation.

---

## What this solves

Roadmap alignment for product, issue clustering for support, and a leadership-friendly snapshot—**automated**, **archived in Google Docs via the Docs MCP server**, and **announced by email via the Gmail MCP server** with a link back to the canonical section.

---

## Delivery expectations (stakeholder-facing)

- Each run adds one clearly labeled section to the product’s pulse Google Doc (dated / week-labeled), created through **Google Docs MCP**.
- The email is a brief teaser (e.g. top themes as bullets) plus a “Read full report” link to that section, sent through **Gmail MCP**.
- Development/staging may default to draft-only email until explicit confirmation to send, per implementation plan.

---

## Success criteria (high level)

- End-to-end run produces a grounded one-page pulse (themes, validated quotes, actions) for a configured product and window.
- Doc and email outcomes are idempotent per product + week and achieved **only via MCP servers**, not direct Google API usage in the agent.
- Architecture and implementation plan traceability: every requirement above maps to modules, MCP server tool usage, and phased exit criteria in [architecture.md](./architecture.md), [phase-wiseimplementationplan.md](./phase-wiseimplementationplan.md), and [phases/](./phases/).
