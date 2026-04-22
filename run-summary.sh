#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEAMS_DIR="$ROOT_DIR/tools/teams"
TEAMS_PY="$TEAMS_DIR/.venv/bin/python"

echo "Teams Channel Summary Wizard"
echo "----------------------------"

if [[ ! -x "$TEAMS_PY" ]]; then
  echo "Setup not complete."
  echo "Run this once first:"
  echo "cd \"$ROOT_DIR\" && python3 -m venv tools/teams/.venv && tools/teams/.venv/bin/pip install -r tools/teams/requirements.txt"
  exit 1
fi

BROWSER="${BROWSER:-google-chrome}" "$TEAMS_PY" - <<'PY'
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

# Heredoc sends script source on stdin, so switch prompts to real terminal input.
try:
    sys.stdin = open("/dev/tty")
except Exception:
    pass

def read_number(prompt: str, low: int, high: int) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw.isdigit():
            print("Please enter a valid number.")
            continue
        val = int(raw)
        if low <= val <= high:
            return val
        print(f"Please enter a number between {low} and {high}.")

def parse_date(raw: str, end: bool = False):
    raw = raw.strip()
    if not raw:
        return None
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if end:
            dt = dt.replace(hour=23, minute=59, second=59)
        return dt
    except Exception:
        return None

script = Path("tools/teams/scripts/scan-teams-graph.py").resolve()
spec = importlib.util.spec_from_file_location("scan_teams_graph", script)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)
scanner = module.TeamsScanner()

force_select = input("Show Microsoft account picker? (y/N): ").strip().lower() == "y"
if not scanner.authenticate(force_select_account=force_select):
    raise SystemExit("Microsoft sign-in failed.")

teams = scanner.list_joined_teams()
if not teams:
    raise SystemExit("No teams found for this account.")

print("\nChoose a team:")
for i, t in enumerate(teams, start=1):
    print(f"  {i}) {t.get('displayName')}")
team_idx = read_number("Enter team number: ", 1, len(teams)) - 1
team = teams[team_idx]
team_id = str(team.get("id") or "")
team_name = str(team.get("displayName") or "")

channels = scanner.list_team_channels(team_id)
if not channels:
    raise SystemExit("No channels found for this team.")

print(f"\nChoose a channel in {team_name}:")
for i, c in enumerate(channels, start=1):
    print(f"  {i}) {c.get('displayName')}")
channel_idx = read_number("Enter channel number: ", 1, len(channels)) - 1
channel = channels[channel_idx]
channel_id = str(channel.get("id") or "")
channel_name = str(channel.get("displayName") or "")

print("\nOptional date range (press Enter to skip):")
print("Format: YYYY-MM-DD")
from_raw = input("Date from: ")
to_raw = input("Date to: ")
date_from = parse_date(from_raw, end=False)
date_to = parse_date(to_raw, end=True)
if from_raw.strip() and not date_from:
    raise SystemExit("Invalid Date from. Use YYYY-MM-DD.")
if to_raw.strip() and not date_to:
    raise SystemExit("Invalid Date to. Use YYYY-MM-DD.")
if date_from and date_to and date_from > date_to:
    raise SystemExit("Date from must be before Date to.")

message_limit = 50
reply_limit = 30
raw_messages = scanner.list_channel_messages(team_id, channel_id, message_limit)
if raw_messages is None:
    raise SystemExit("Could not load channel messages from Microsoft Graph. Please try again.")
items = []
for msg in raw_messages:
    created_raw = msg.get("createdDateTime")
    created = None
    if created_raw:
        try:
            created = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
        except Exception:
            created = None
    preview = scanner._strip_html((msg.get("body") or {}).get("content", ""))[:500]
    items.append(
        {
            "from": scanner._sender_display_name(msg) or "Unknown",
            "created": created,
            "created_raw": created_raw or "",
            "body_preview": preview,
        }
    )
    msg_id = msg.get("id")
    if msg_id:
        replies = scanner.list_channel_message_replies(team_id, channel_id, msg_id, reply_limit)
        for rep in replies:
            rep_created_raw = rep.get("createdDateTime")
            rep_created = None
            if rep_created_raw:
                try:
                    rep_created = datetime.fromisoformat(str(rep_created_raw).replace("Z", "+00:00"))
                except Exception:
                    rep_created = None
            rep_preview = scanner._strip_html((rep.get("body") or {}).get("content", ""))[:500]
            items.append(
                {
                    "from": scanner._sender_display_name(rep) or "Unknown",
                    "created": rep_created,
                    "created_raw": rep_created_raw or "",
                    "body_preview": rep_preview,
                }
            )

if date_from or date_to:
    filtered = []
    for i in items:
        dt = i.get("created")
        if dt is None:
            continue
        if date_from and dt < date_from:
            continue
        if date_to and dt > date_to:
            continue
        filtered.append(i)
    items = filtered

if not items:
    raise SystemExit("No messages found for the selected channel and date range.")

senders = sorted({str(i.get("from") or "Unknown") for i in items}, key=str.lower)
print("\nChoose a person:")
print("  0) Everyone")
for i, sender in enumerate(senders, start=1):
    print(f"  {i}) {sender}")
sender_idx = read_number("Enter person number: ", 0, len(senders))
selected_sender = "" if sender_idx == 0 else senders[sender_idx - 1]

if selected_sender:
    items = [i for i in items if str(i.get("from") or "") == selected_sender]
    if not items:
        raise SystemExit("No messages found for that person in the selected date range.")

confirm = input("\nGenerate summary now? (Y/n): ").strip().lower()
if confirm == "n":
    raise SystemExit("Cancelled.")

dates = sorted({(i.get("created") or datetime.now(timezone.utc)).date().isoformat() for i in items})
print("\n================ Summary ================")
print(f"Team: {team_name}")
print(f"Channel: {channel_name}")
print(f"Person: {selected_sender or 'Everyone'}")
print(f"Date from: {from_raw.strip() or 'Any'}")
print(f"Date to: {to_raw.strip() or 'Any'}")
print(f"Messages: {len(items)}")
print(f"Days active: {len(dates)}")

print("\nTop participants:")
counts = {}
for i in items:
    sender = str(i.get("from") or "Unknown")
    counts[sender] = counts.get(sender, 0) + 1
for idx, (sender, count) in enumerate(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5], start=1):
    print(f"  {idx}. {sender}: {count}")

print("\nEvidence (first 8 messages):")
for idx, i in enumerate(items[:8], start=1):
    txt = (i.get("body_preview") or "").strip().replace("\n", " ")
    if len(txt) > 220:
        txt = txt[:219].rstrip() + "..."
    print(f"  {idx}. [{i.get('from')}] {txt}")
print("========================================")
PY
