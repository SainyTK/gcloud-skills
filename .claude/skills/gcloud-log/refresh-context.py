#!/usr/bin/env python3
"""Rebuilds context.json from existing gcloud credentials."""

import json
import subprocess
import sys
from datetime import date


def run(cmd: list[str]) -> list[str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return [l for l in result.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def tsv(line: str) -> list[str]:
    return line.split("\t")


SCHEDULER_REGIONS = [
    "asia-southeast1",
    "asia-east1",
    "asia-northeast1",
    "us-central1",
    "us-east1",
    "europe-west1",
]


def get_project_timezones(project_id: str, account: str) -> list[dict]:
    """Query Cloud Scheduler jobs to extract schedules and timezones."""
    for region in SCHEDULER_REGIONS:
        lines = run([
            "gcloud", "scheduler", "jobs", "list",
            f"--project={project_id}",
            f"--account={account}",
            f"--location={region}",
            "--format=value(name,schedule,timeZone)",
        ])
        if lines:
            jobs = []
            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 3:
                    jobs.append({
                        "name": parts[0].strip(),
                        "schedule": parts[1].strip(),
                        "timezone": parts[2].strip(),
                    })
            return jobs
    return []


def main(out_path: str) -> None:
    project_context = load_existing_project_context(out_path)
    accounts = []
    projects = []
    services = []
    seen_projects: set[tuple] = set()
    seen_services: set[tuple] = set()

    # Accounts
    print("Discovering accounts...", file=sys.stderr)
    for line in run(["gcloud", "auth", "list", "--format=value(account,status)"]):
        parts = tsv(line)
        email = parts[0].strip()
        status = parts[1].strip().lower().replace("*", "").strip() if len(parts) > 1 else ""
        if email:
            accounts.append({"email": email, "status": status})

    # Projects + services per account
    for acct in accounts:
        email = acct["email"]
        print(f"  [{email}] fetching projects...", file=sys.stderr)
        proj_lines = run([
            "gcloud", "projects", "list",
            f"--account={email}",
            "--format=value(projectId,name)",
        ])
        acct_projects = []
        for line in proj_lines:
            parts = tsv(line)
            pid = parts[0].strip()
            name = parts[1].strip() if len(parts) > 1 else pid
            if not pid or pid.startswith("gen-lang") or pid.startswith("sys-"):
                continue
            key = (pid, email)
            if key not in seen_projects:
                seen_projects.add(key)
                projects.append({"projectId": pid, "name": name, "account": email})
                acct_projects.append(pid)

        for pid in acct_projects:
            print(f"    [{pid}] fetching scheduler jobs...", file=sys.stderr)
            jobs = get_project_timezones(pid, email)
            if jobs:
                # Attach scheduler info back to the project entry
                for p in projects:
                    if p["projectId"] == pid:
                        timezones = list({j["timezone"] for j in jobs if j["timezone"]})
                        p["scheduler_timezone"] = timezones[0] if len(timezones) == 1 else timezones
                        p["scheduler_jobs"] = jobs
                        break

        for pid in acct_projects:
            svc_lines = run([
                "gcloud", "run", "services", "list",
                f"--project={pid}",
                f"--account={email}",
                "--format=value(metadata.name,status.url)",
            ])
            for line in svc_lines:
                parts = tsv(line)
                sname = parts[0].strip()
                surl = parts[1].strip() if len(parts) > 1 else ""
                if not sname:
                    continue
                key = (sname, pid)
                if key not in seen_services:
                    seen_services.add(key)
                    services.append({
                        "name": sname,
                        "projectId": pid,
                        "account": email,
                        "url": surl,
                        "type": "cloud_run",
                    })

    out = {
        "_meta": {
            "last_updated": date.today().isoformat(),
            "note": "Auto-generated. Re-run to refresh accounts/projects/services. Edit project_context manually — it is preserved across refreshes.",
        },
        "project_context": project_context,
        "accounts": accounts,
        "projects": projects,
        "services": services,
    }

    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Written: {out_path}", file=sys.stderr)
    print(f"  accounts: {len(accounts)}", file=sys.stderr)
    print(f"  projects: {len(projects)}", file=sys.stderr)
    print(f"  services: {len(services)}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "context.json")
