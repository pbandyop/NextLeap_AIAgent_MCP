# Production send checklist

Complete before first `EMAIL_MODE=send` in `PULSE_ENV=production`.

## Staging validation

- [ ] Full `pulse run` for each product in staging (`PULSE_ENV=staging`, draft email only)
- [ ] Google Doc section readable; anchor `<!-- pulse:product:week -->` present
- [ ] Gmail draft link opens correct Doc `section_url`
- [ ] Re-run same `(product, iso_week)` → no duplicate Doc section or draft (idempotency)
- [ ] PII spot-check: no raw emails/phones in Doc or draft body

## Configuration

- [ ] `PULSE_EMAIL_TO` (or per-product overrides) verified with stakeholders
- [ ] Per-product `PULSE_DOC_ID_*` points to correct shared Doc
- [ ] Railway MCP server health OK
- [ ] Secrets only in env / secret store (not in git)

## Production gate

- [ ] Stakeholder sign-off on sample Groww pulse (and other products as needed)
- [ ] Cron / schedule documented in [scheduling.md](./scheduling.md)
- [ ] On-call knows [runbook.md](./runbook.md) retry steps

## Enable send (when MCP server supports it)

```env
PULSE_ENV=production
EMAIL_MODE=send
PULSE_PRODUCTION_SEND_APPROVED=true
```

Until the workspace HTTP server implements send, keep `EMAIL_MODE=draft` and send manually from Gmail.

## Sign-off

| Role | Name | Date |
|------|------|------|
| Engineering | | |
| Product owner | | |
