# NextLeap AI Agent MCP — Weekly Product Review Pulse

Single **Pulse Agent** that ingests public App Store and Google Play reviews, and (in later phases) delivers insights via **Google Docs** and **Gmail MCP servers**.

## Documentation

- [Problem statement](docs/ProblemStatement.md)
- [Architecture](docs/architecture.md)
- [Phase-wise plan](docs/phase-wiseimplementationplan.md)
- [Decisions](docs/decision.md)

## Requirements

- Python 3.11+
- Node.js (optional, for MCP servers via `npx`)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

Edit `.env` and set `GROQ_API_KEY` from [Groq Console](https://console.groq.com/keys). The CLI loads `.env` automatically on each run.

## Run

**Phase 0 — foundation only (no ingest, no MCP):**

```bash
pulse run --product groww --week 2026-W20 --dry-run --skip-ingest
```

**Phase 1 — ingest reviews (dry-run skips MCP smoke):**

```bash
pulse run --product groww --week 2026-W20 --dry-run
```

**Phase 2 — analyze reviews (uses stub LLM without `GROQ_API_KEY` on dry-run):**

```bash
pulse run --product groww --week 2026-W20 --dry-run --skip-ingest --stub-llm
```

With Groq (set `GROQ_API_KEY`):

```bash
pulse run --product groww --week 2026-W20 --dry-run --skip-ingest
```

Artifacts:

- `data/runs/pulse_groww_2026-W20/reviews.json` — **1,216** normalized reviews (5,500 fetched; see [architecture §6.1](docs/architecture.md#61-phase-2-analysis-strategy-data--llm))
- `data/runs/pulse_groww_2026-W20/pulse_report.json` — themes, quotes, actions
- `data/runs/pulse_groww_2026-W20/run_audit.json`
- `runs/pulse_groww_2026-W20.json` (legacy audit path)

Override fetch volume: `pulse run --product groww --week 2026-W20 --dry-run --play-count 5000`

Optional clustering deps: `pip install -e ".[analysis]"`

## Tests

```bash
pytest tests/phase_00 tests/phase_01 -q
```

MCP integration (requires running MCP servers):

```bash
pytest tests/integration -m integration
```

## Project layout

```text
config/                 # products.yaml, mcp_servers.yaml
data/runs/              # per-run artifacts (gitignored)
docs/phases/            # eval.md per phase
src/pulse_agent/
  phases/
    phase_00_foundation/
    phase_01_ingestion/
    phase_02_analysis/   # stub
    ...
tests/
  phase_00/
  phase_01/
  fixtures/
```

## MCP servers

Configure `config/mcp_servers.yaml`. OAuth credentials belong in the MCP server environment, not this repo. Update server commands to match your installed Docs/Gmail MCP packages.
