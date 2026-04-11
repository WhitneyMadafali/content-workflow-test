#!/usr/bin/env bash
# Scan a Teams channel for Microsoft Forms links, then summarize responses (Forms API).
# Usage (from anywhere):
#   bash /path/to/content-workflow/tools/forms-mcp/scan_channel_forms_summary.sh "Team display name" "Channel name"
# First time or to pick your account, set SCAN_SELECT_ACCOUNT=1

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TEAM="${1:?Usage: $0 <team-display-name> <channel-display-name>}"
CHANNEL="${2:?}"
OUT="${REPO_ROOT}/tools/teams/analyses/channel-forms-latest.json"
export BROWSER="${BROWSER:-google-chrome}"

mkdir -p "$(dirname "$OUT")"

SCAN_ARGS=(
  scripts/scan-teams-graph.py
  --team-name "$TEAM"
  --channel-name "$CHANNEL"
  --include-channel-messages
  --forms-links-only
  --message-limit 50
  -o "$OUT"
)
if [[ "${SCAN_SELECT_ACCOUNT:-}" == "1" ]]; then
  SCAN_ARGS+=(--select-account)
fi

cd "${REPO_ROOT}/tools/teams"
./.venv/bin/python "${SCAN_ARGS[@]}"

cd "${REPO_ROOT}/tools/forms-mcp"
# Default: --brief (no huge JSON). Set FULL_JSON=1 for complete payload.
if [[ "${FULL_JSON:-}" == "1" ]]; then
  ./.venv/bin/python summarize_from_teams_export.py "$OUT"
else
  ./.venv/bin/python summarize_from_teams_export.py --brief "$OUT"
fi
