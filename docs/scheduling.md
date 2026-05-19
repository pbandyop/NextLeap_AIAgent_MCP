# Weekly pulse scheduling (cron)

## Recommended schedule

Run **one full pipeline per product** each Monday after the prior ISO week closes.

| Setting | Value |
|---------|--------|
| Timezone | **Asia/Kolkata (IST)** |
| Time | **09:00 IST** (adjust per stakeholder preference) |
| Day | **Monday** |
| Command | `pulse run --product <id> --week <previous-iso-week>` |

Example for the week ending Sunday night (run Monday morning):

```bash
pulse run --product groww --week 2026-W20
```

Or all products:

```bash
pulse run-all --week 2026-W20
```

## Linux cron example

```cron
# Monday 09:00 IST — Groww weekly pulse (previous ISO week computed in script)
0 9 * * 1 cd /opt/pulse-agent && /usr/bin/pulse run --product groww --week $(date -d 'last week' +%G-W%V) >> /var/log/pulse-groww.log 2>&1
```

On Windows Task Scheduler, use PowerShell and `pulse run` with an explicit `--week` label.

## Environment

- `PULSE_ENV=staging` → `EMAIL_MODE` forced to **draft**
- `PULSE_ENV=production` → draft by default; **send** only with `PULSE_PRODUCTION_SEND_APPROVED=true`

## Failure alerting

| Exit code | Meaning | Action |
|-----------|---------|--------|
| `0` | Success | None |
| `2` | Partial (Docs ok, Gmail failed) | Retry: `pulse run --product X --week Y --skip-ingest --skip-analyze --skip-render --skip-docs` |
| `1` | Fatal | Check logs, MCP health, `docs/runbook.md` |

Monitor `data/runs/pulse_<product>_<week>/run_audit.json` for `status`, `errors`, and `metrics.duration_seconds`.
