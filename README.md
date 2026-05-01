# cc-app/gcloud

Claude Code skills for Google Cloud Platform.

## Skills

### gcloud-log

Trace and analyze Cloud Run logs by service name. Auto-resolves project ID and account from a local cache — no need to specify credentials each time.

**Usage:** just say the service name.

```
check logs for api-copilot
show errors in psim-pipeline last 6h
trace slow requests on api-gateway
```

**Cache setup:** Run once (and after adding new accounts/projects):

```bash
python3 .claude/skills/gcloud-log/refresh-context.py
```

`context.json` is gitignored — never committed.

## Roadmap

- `gcloud-log` — Cloud Run log tracing ✅
- `bigquery` — query history, job traces, cost analysis
- `cloudsql` — slow query logs, connection issues
