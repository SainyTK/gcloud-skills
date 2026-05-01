---
name: gcloud-log
description: >
  Trace and analyze Google Cloud logs for a given service, project, and user email.
  Use when the user asks to check logs, trace errors, debug a service, find requests,
  or investigate incidents in GCP. Triggers: "check logs", "trace logs", "gcloud logs",
  "what happened in service X", "find errors in project Y", "debug Cloud Run", "show me logs".
  User only needs to say service name — project and email auto-resolved from context.json cache.
allowed-tools: Bash(gcloud logging read*), Bash(gcloud auth*), Bash(gcloud projects*), Bash(gcloud run*), Bash(rtk gcloud*), Read(*context.json*)
---

# gcloud-log

Trace GCP logs using local `gcloud` CLI. User provides only service name — resolve everything else from cache.

## Step 0: Load context cache

Always read `.claude/skills/gcloud-log/context.json` first. It contains known accounts, projects, and services with their linked credentials.

```bash
# The cache lives next to this skill file
cat .claude/skills/gcloud-log/context.json
```

Use this to resolve: service name → projectId + account (email). No need to ask user.

## Step 1: Resolve service → project + account

1. Search `services[]` in context.json by `name` (exact or substring match)
2. Get `projectId` and `account` from matched entry
3. If multiple matches (e.g. `api-bff` matches prod and dev), ask user: prod or dev?
4. If no match → fall back to Step 1b

**Step 1b: Cache miss — discover and update**

Service not in cache? Discover it:
```bash
# Check all projects the matched account can access
gcloud run services list --project=PROJECT_ID --account=ACCOUNT --format="value(metadata.name,status.url)"
```

After finding the service, update context.json — add new entry to `services[]` and update `_meta.last_updated`.

## Step 2: Switch account if needed

```bash
gcloud config set account ACCOUNT_EMAIL
```

Only needed if active account differs from required account.

## Step 3: Identify resource type

| Service type | resource.type |
|-------------|---------------|
| Cloud Run | `cloud_run_revision` |
| Cloud Functions | `cloud_function` |
| App Engine | `gae_app` |
| GKE | `k8s_container` |
| Compute Engine | `gce_instance` |
| Cloud SQL | `cloudsql_database` |

All services in current cache are Cloud Run → use `cloud_run_revision`.

## Step 4: Run queries

#### Recent logs (last 1h)
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="SERVICE_NAME"' \
  --project=PROJECT_ID \
  --freshness=1h \
  --limit=50 \
  --format=json
```

#### Errors only
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="SERVICE_NAME" AND severity>=ERROR' \
  --project=PROJECT_ID \
  --freshness=24h \
  --limit=100 \
  --format=json
```

#### User activity (audit logs)
```bash
gcloud logging read \
  'protoPayload.authenticationInfo.principalEmail="USER_EMAIL"' \
  --project=PROJECT_ID \
  --freshness=24h \
  --limit=100 \
  --format=json
```

#### Time window
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="SERVICE_NAME" AND timestamp>="2026-01-01T00:00:00Z" AND timestamp<="2026-01-02T00:00:00Z"' \
  --project=PROJECT_ID \
  --limit=200 \
  --format=json
```

#### Keyword / text search
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="SERVICE_NAME" AND textPayload:"KEYWORD"' \
  --project=PROJECT_ID \
  --freshness=6h \
  --limit=50 \
  --format=json
```

#### HTTP 4xx/5xx errors
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="SERVICE_NAME" AND httpRequest.status>=400' \
  --project=PROJECT_ID \
  --freshness=1h \
  --limit=50 \
  --format=json
```

#### Slow requests
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="SERVICE_NAME" AND httpRequest.latency>"5s"' \
  --project=PROJECT_ID \
  --freshness=1h \
  --limit=50 \
  --format=json
```

#### Trace by request ID
```bash
gcloud logging read \
  'labels."run.googleapis.com/request_id"="REQUEST_ID"' \
  --project=PROJECT_ID \
  --limit=50 \
  --format=json
```

## Step 5: Parse and answer

Extract from JSON logs:
- `timestamp` — when
- `severity` — level
- `textPayload` or `jsonPayload` — message body
- `httpRequest.status`, `httpRequest.latency` — HTTP logs
- `protoPayload.status.message` — audit log errors
- `labels` — trace IDs, revision names

Output format:
- **Summary**: N events/errors in time window, service, project
- **Top issues**: grouped by message with counts
- **Timeline**: key events with timestamps
- **Raw sample**: first few relevant lines if useful

## Cache maintenance

Update context.json when:
- New service discovered during cache-miss lookup → add to `services[]`
- New project accessed → add to `projects[]`
- Account status changes → update `accounts[].status`
- Always update `_meta.last_updated` to today's date

context.json location: `.claude/skills/gcloud-log/context.json`

## Known services (from cache)

**set-gcp-ai-atlas-prod** (account: outsource2799@set.or.th):
`api-bff`, `api-copilot`, `api-doc`, `api-gateway`, `app-atlas`, `langfuse`, `psim-ocr-pipeline`, `psim-pipeline`

**set-gcp-ai-atlas-dev** (account: outsource2799@set.or.th):
`api-bff-dev`, `api-bff-uat`, `api-copilot-dev`, `api-copilot-uat`, `api-doc-dev`, `api-doc-uat`, `api-gateway-dev`, `api-gateway-uat`, `app-atlas-dev`, `app-atlas-uat`, `langfuse`, `psim-ocr-pipeline-dev`, `psim-ocr-pipeline-uat`, `psim-pipeline-dev`, `psim-pipeline-uat`

## Auth troubleshooting

Token expired → tell user to run:
```
! gcloud auth login --account=ACCOUNT_EMAIL
```

Never attempt interactive auth. Never block on auth — surface the error and instruct.

## Notes

- `--format=json` for parsing; `--format=text` for quick human display
- `--freshness`: `1h`, `6h`, `24h`, `7d`, `30d`
- `--limit` max practical: 1000
- Log filter syntax: `AND`, `OR`, `NOT`; `:` for substring, `=` for exact
