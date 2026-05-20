#!/usr/bin/env python3
"""Rebuilds gcloud-bq context.json from local gcloud/bq access."""

import json
import subprocess
import sys
from datetime import date


def run(cmd: list[str]) -> list[str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        return [line for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def run_text(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        return result.stdout
    except Exception:
        return ""


def tsv(line: str) -> list[str]:
    return line.split("\t")


def main(out_path: str) -> None:
    accounts = []
    projects = []
    datasets = []
    seen_projects: set[tuple[str, str]] = set()
    seen_datasets: set[tuple[str, str]] = set()

    print("Discovering accounts...", file=sys.stderr)
    for line in run(["gcloud", "auth", "list", "--format=value(account,status)"]):
        parts = tsv(line)
        email = parts[0].strip()
        status = parts[1].strip().lower().replace("*", "").strip() if len(parts) > 1 else ""
        if email:
            accounts.append({"email": email, "status": status})

    for account in accounts:
        email = account["email"]
        print(f"  [{email}] fetching projects...", file=sys.stderr)
        project_lines = run([
            "gcloud",
            "projects",
            "list",
            f"--account={email}",
            "--format=value(projectId,name)",
        ])

        account_projects = []
        for line in project_lines:
            parts = tsv(line)
            project_id = parts[0].strip()
            name = parts[1].strip() if len(parts) > 1 else project_id
            if not project_id or project_id.startswith("gen-lang") or project_id.startswith("sys-"):
                continue
            key = (project_id, email)
            if key in seen_projects:
                continue
            seen_projects.add(key)
            projects.append({"projectId": project_id, "name": name, "account": email})
            account_projects.append(project_id)

        for project_id in account_projects:
            print(f"    [{project_id}] fetching datasets...", file=sys.stderr)
            dataset_json = run_text([
                "bq",
                "--format=prettyjson",
                "ls",
                f"--project_id={project_id}",
                "--max_results=1000",
            ])
            try:
                dataset_items = json.loads(dataset_json) if dataset_json.strip() else []
            except json.JSONDecodeError:
                dataset_items = []
            for item in dataset_items:
                dataset_ref = item.get("datasetReference", {})
                dataset_id = dataset_ref.get("datasetId", "").strip()
                if not dataset_id:
                    continue
                key = (project_id, dataset_id)
                if key in seen_datasets:
                    continue
                seen_datasets.add(key)
                datasets.append({
                    "projectId": project_id,
                    "datasetId": dataset_id,
                    "account": email,
                })

    out = {
        "_meta": {
            "last_updated": date.today().isoformat(),
            "note": "Auto-generated. Re-run to refresh BigQuery accounts, projects, and datasets.",
        },
        "accounts": accounts,
        "projects": projects,
        "datasets": datasets,
    }

    with open(out_path, "w") as handle:
        json.dump(out, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Written: {out_path}", file=sys.stderr)
    print(f"  accounts: {len(accounts)}", file=sys.stderr)
    print(f"  projects: {len(projects)}", file=sys.stderr)
    print(f"  datasets: {len(datasets)}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "context.json")
