# Pulse Agent — Operations runbook

## Health checks

**Workspace MCP server (Docs + Gmail):**

```bash
curl https://saksham-mcp-server-production-b243.up.railway.app/
```

Expect `credentials_ready: true` and `token_configured: true`.

**Agent smoke (no delivery):**

```bash
pulse run --product groww --week 2026-W20 --dry-run --stub-llm
```

## Full weekly run

```bash
pulse run --product groww --week 2026-W20
```

Artifacts: `data/runs/pulse_groww_2026-W20/`

| File | Purpose |
|------|---------|
| `reviews.json` | Normalized corpus |
| `pulse_report.json` | Themes and quotes |
| `doc_section.txt` | Doc append payload |
| `docs_delivery.json` | Doc id + section URL |
| `gmail_delivery.json` | Draft id + recipient |
| `run_audit.json` | Full audit + metrics |

## Retry after partial failure (exit code 2)

Docs succeeded but Gmail failed:

```bash
pulse run --product groww --week 2026-W20 \
  --skip-ingest --skip-analyze --skip-render --skip-docs
```

## Backfill missed weeks

```bash
pulse backfill --product groww --from-week 2026-W18 --to-week 2026-W20
# or
pulse backfill --product groww --weeks 2026-W18,2026-W19
```

## MCP server restart (Railway)

1. Open Railway project for [NextLeap_MCP_Server_Gmail_GDocs](https://github.com/pbandyop/NextLeap_MCP_Server_Gmail_GDocs).
2. Verify `GOOGLE_CREDENTIALS_JSON`, `GOOGLE_TOKEN_JSON`, `AUTO_APPROVE=true`.
3. Redeploy; confirm `GET /` health.
4. Re-run delivery phase only if needed.

## OAuth errors

`deleted_client` or `invalid_grant` → regenerate OAuth desktop credentials, run `python auth.py` locally, update Railway env vars.

## Production email send

1. Complete [production-send-checklist.md](./production-send-checklist.md).
2. Set `PULSE_ENV=production`, `EMAIL_MODE=send`, `PULSE_PRODUCTION_SEND_APPROVED=true`.
3. Note: HTTP MCP server currently supports **draft** only; send from Gmail UI until send API is added.

## Configuration reference

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Phase 2 analysis |
| `GOOGLE_DOC_ID` / `PULSE_DOC_ID_*` | Target Google Doc |
| `PULSE_EMAIL_TO` | Gmail draft recipient |
| `GOOGLE_MCP_BASE_URL` | Workspace server URL |
| `PULSE_ENV` | `dev` \| `staging` \| `production` |
| `EMAIL_MODE` | `draft` \| `send` (gated) |

See [scheduling.md](./scheduling.md) for cron setup.
