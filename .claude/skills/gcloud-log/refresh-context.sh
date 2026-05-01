#!/usr/bin/env bash
# Rebuilds context.json from existing gcloud credentials.
# Run this whenever you add new accounts, projects, or services.
# Output: .claude/skills/gcloud-log/context.json (gitignored)

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/refresh-context.py" "$SCRIPT_DIR/context.json"
