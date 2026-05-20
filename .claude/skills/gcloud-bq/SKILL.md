---
name: gcloud-bq
description: >
  Inspect and analyze Google BigQuery projects, datasets, tables, query jobs, and
  query cost using the local bq CLI. Use when the user asks about BigQuery data,
  query history, schemas, row samples, job traces, dry-run estimates, bytes billed,
  or cost/debug analysis. Triggers: "bigquery", "bq", "query history", "job trace",
  "schema for table", "sample rows", "estimate query cost", "bytes processed".
  User can provide a project, dataset, table, SQL, or job id; project/account may
  be resolved from context.json cache.
allowed-tools: Bash(bq ls*), Bash(bq show*), Bash(bq head*), Bash(bq query*), Bash(gcloud auth*), Bash(gcloud projects*), Bash(rtk bq*), Bash(rtk gcloud*), Read(*context.json*)
---

# gcloud-bq

Inspect BigQuery safely using local `bq` CLI. Default posture is read-only:
list, show, head, dry-run, and capped SELECT queries. Do not mutate data or IAM.

## Step 0: Load context cache

Always read `.claude/skills/gcloud-bq/context.json` first. It contains known
accounts, projects, and discovered BigQuery datasets.

```bash
cat .claude/skills/gcloud-bq/context.json
```

Use this to resolve: project name/id or dataset name -> projectId + account.
If the cache is missing or stale, refresh it:

```bash
python3 .claude/skills/gcloud-bq/refresh-context.py .claude/skills/gcloud-bq/context.json
```

## Step 1: Resolve target

1. If user gives full table id `project.dataset.table`, use that project.
2. If user gives `dataset.table`, search `datasets[]` in context.json.
3. If user gives only project name/id, search `projects[]`.
4. If multiple matches, ask the user which project/dataset.
5. If no match, list accessible projects/datasets and update context.json.

Project id matters for billing and access. Prefer explicit project from the user
when present; otherwise use the cache.

## Step 2: Switch account if needed

```bash
gcloud config set account ACCOUNT_EMAIL
```

Only needed if the active account differs from the resolved account.

## Safety rules

- Read-only commands only: `bq ls`, `bq show`, `bq head`, `bq query`.
- Never run: `bq rm`, `bq mk`, `bq load`, `bq extract`, `bq update`, `bq cp`,
  `bq set-iam-policy`, `bq add-iam-policy-binding`, or `bq remove-iam-policy-binding`.
- For ad hoc SQL, dry-run first unless the user explicitly asks to execute.
- For execution, use Standard SQL, cap rows, and cap billing:
  `--use_legacy_sql=false --max_rows=100 --maximum_bytes_billed=1000000000`.
- Do not use destination tables unless explicitly requested and separately approved.
- Prefer aggregate/count/schema queries over raw row dumps when data may be sensitive.

## Format guidance

For machine-readable inspection, use `--format=prettyjson` on `bq show`. For
lists, default table output is usually readable; add `--format=prettyjson` only
when parsing is needed.

## Common workflows

### List datasets in a project

```bash
bq ls --project_id=PROJECT_ID --max_results=1000
```

### List tables in a dataset

```bash
bq ls --project_id=PROJECT_ID DATASET_ID
```

### Show table metadata and schema

```bash
bq show --project_id=PROJECT_ID --format=prettyjson DATASET_ID.TABLE_ID
```

Schema only:

```bash
bq show --project_id=PROJECT_ID --schema --format=prettyjson DATASET_ID.TABLE_ID
```

### Sample rows

```bash
bq head --project_id=PROJECT_ID --max_rows=20 DATASET_ID.TABLE_ID
```

Prefer selecting non-sensitive fields:

```bash
bq head --project_id=PROJECT_ID --max_rows=20 --selected_fields=field1,field2 DATASET_ID.TABLE_ID
```

### Dry-run a query for cost

```bash
bq query \
  --project_id=PROJECT_ID \
  --use_legacy_sql=false \
  --dry_run \
  'SELECT COUNT(*) FROM `PROJECT_ID.DATASET_ID.TABLE_ID`'
```

Report bytes processed from the dry-run output. Estimate on-demand cost only as
an approximation: TiB scanned * current BigQuery price. If exact pricing matters,
tell the user to confirm pricing for their edition/region/reservation.

### Execute a capped query

```bash
bq query \
  --project_id=PROJECT_ID \
  --use_legacy_sql=false \
  --max_rows=100 \
  --maximum_bytes_billed=1000000000 \
  'SELECT col1, COUNT(*) AS n FROM `PROJECT_ID.DATASET_ID.TABLE_ID` GROUP BY col1 ORDER BY n DESC LIMIT 100'
```

### List recent jobs

```bash
bq ls \
  --project_id=PROJECT_ID \
  --jobs \
  --all \
  --max_results=50
```

Filter running or failed jobs:

```bash
bq ls \
  --project_id=PROJECT_ID \
  --jobs \
  --all \
  --filter='states:RUNNING,PENDING,DONE' \
  --max_results=100
```

### Show job details

```bash
bq show --project_id=PROJECT_ID --job --format=prettyjson JOB_ID
```

If the job is location-scoped, include location:

```bash
bq show --project_id=PROJECT_ID --location=LOCATION --job --format=prettyjson JOB_ID
```

Extract:
- `status.state`
- `status.errorResult` and `status.errors`
- `statistics.creationTime`, `startTime`, `endTime`
- `statistics.query.totalBytesProcessed`
- `statistics.query.totalBytesBilled`
- `statistics.query.statementType`
- `configuration.query.query`

### Read query job results

```bash
bq head --project_id=PROJECT_ID --job --max_rows=100 JOB_ID
```

## Cache maintenance

Update context.json when:
- New project is discovered -> add to `projects[]`
- New dataset is discovered -> add to `datasets[]`
- Account status changes -> update `accounts[].status`
- Always update `_meta.last_updated` to today's date

context.json location: `.claude/skills/gcloud-bq/context.json`

Refresh cache:

```bash
python3 .claude/skills/gcloud-bq/refresh-context.py .claude/skills/gcloud-bq/context.json
```

## Auth troubleshooting

Token expired -> tell user to run:

```bash
gcloud auth login --account=ACCOUNT_EMAIL
```

Never attempt interactive auth. Surface the exact error and the account/project
that failed.

## Answer format

- **Target**: project, dataset/table/job, account used
- **Finding**: concise answer first
- **Evidence**: command output summary, key rows/fields/job stats
- **Cost**: bytes processed/billed when relevant
- **Next step**: only if another command is needed
