<p align="center">
  <img src="assets/gcloud-skill-wallpaper.png" alt="gcloud auth hero" />
</p>

<h1 align="center">GCloud Agent Skills</h1>

<p align="center">
  <strong>let ai agents take gcloud actions on your behalf.</strong>
</p>

<p align="center">
  <a href="#prerequisites">Prerequisites</a> •
  <a href="#skills">Skills</a> •
  <a href="#permission-mode">Permission Mode</a> •
  <a href="#roadmap">Roadmap</a>
</p>

----

## Prerequisites

- Any of these agents are installed:
  - [Claude Code](https://claude.ai/code)
  - [Codex](https://developers.openai.com/codex/cli)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`) installed and on PATH
- BigQuery CLI (`bq`) installed and on PATH for `gcloud-bq`
- At least one authenticated account: `gcloud auth login`
- Python 3.9+

## Installation

Install the skills for your agent:

Claude Code:

```bash
npx skills add SainyTK/gcloud-skills -a claude-code
```

Codex:

```bash
npx skills add SainyTK/gcloud-skills -a codex
```

## Skills

### gcloud-log

Trace and analyze Cloud Run logs by service name. Auto-resolves project ID and account from a local cache — no need to specify credentials each time.

**Usage:** just say the service name.

```
check logs for backoffice-service
show errors in data-pipeline-dev last 6h
trace slow requests on api-gateway
```

**Cache setup:** Run once (and after adding new accounts/projects):

Claude Code:

```bash
python3 .claude/skills/gcloud-log/refresh-context.py
```

Codex:

```bash
python3 .codex/skills/gcloud-log/refresh-context.py
```

`context.json` is gitignored — never committed. It contains local account, project, and service metadata.

### gcloud-bq

Inspect BigQuery datasets, tables, schemas, sample rows, query jobs, and dry-run cost estimates. Uses read-only `bq` commands by default.

**Usage:** name the BigQuery target or question.

```
show schema for analytics.events
estimate cost for this query in project my-project
list recent BigQuery jobs in my-project
trace BigQuery job bquxjob_123
sample 20 rows from analytics.users
```

**Cache setup:** Run once (and after adding new accounts/projects):

Claude Code:

```bash
python3 .claude/skills/gcloud-bq/refresh-context.py .claude/skills/gcloud-bq/context.json
```

Codex:

```bash
python3 .codex/skills/gcloud-bq/refresh-context.py .codex/skills/gcloud-bq/context.json
```

`context.json` is gitignored — never committed. It contains local account, project, and dataset metadata.

## Permission Mode

This project includes starter permission templates for both agents:

- Claude Code: `.claude/settings.json`
- Codex: `.codex/rules/default.rules`

Use those files as templates when adding new skills. Keep rules narrow: prefer specific read/list/describe commands over broad `gcloud *` access.

Current permissions allow:

- Cloud Run log inspection with `gcloud logging read`
- Cloud Run service discovery with `gcloud run services list/describe`
- Project and auth discovery with `gcloud auth list` and `gcloud projects list/describe`
- BigQuery read-only inspection with `bq ls`, `bq show`, `bq head`, and `bq query`
- Local cache refresh scripts for `gcloud-log` and `gcloud-bq`

For the smoothest default workflow, use one of these two modes. Prefer Don't Ask mode for this project once you trust the repo and GCP target, but use it with caution.

### 1. Auto Mode

Allows the agent to work with project permissions while still using the normal approval flow when needed.

Claude Code:

```bash
claude --permission-mode auto
```

Codex:

```bash
codex
```

### 2. Don't Ask Mode (Recommended)

Lets the agent run without stopping for approvals. Use only in trusted repos and cloud projects.

Claude Code:

```bash
claude --permission-mode dontAsk
```

Codex:

```bash
codex --sandbox workspace-write --ask-for-approval never
```

## Roadmap

- `gcloud-log` — Cloud Run log tracing ✅
- `gcloud-bq` — BigQuery query history, job traces, cost analysis ✅
- `cloudsql` — slow query logs, connection issues
