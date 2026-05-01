# cc-app/gcloud

Personal Claude Code skills for Google Cloud Platform.

## Skills

### gcloud-log

Trace and analyze Cloud Run logs by service name. Auto-resolves project ID and account from a local cache — no need to specify credentials each time.

**Usage:** just say the service name.

```
check logs for api-copilot
show errors in psim-pipeline last 6h
trace slow requests on api-gateway
```

**Cache setup:** On first use, copy the template and fill in your credentials:

```bash
cp .claude/skills/gcloud-log/context.json.example .claude/skills/gcloud-log/context.json
```

`context.json` is gitignored — never committed.

## Roadmap

- `gcloud-log` — Cloud Run log tracing ✅
- `bigquery` — query history, job traces, cost analysis
- `cloudsql` — slow query logs, connection issues
