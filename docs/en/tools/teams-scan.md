# Teams Scan Process

This guide explains how to use the `tools/teams` scanner to export Teams structure, channel messages/replies, and optional files into JSON.

## 1) Install

```bash
cd tools/teams
pip install -r requirements.txt
```

## 2) List Joined Teams

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --list-teams
```

## 3) Scan Teams + Channels Structure Only

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py -o analyses/teams-structure.json
```

## 4) Include Channel Messages and Reply Threads

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --message-limit 50 --reply-limit 50 -o analyses/teams-messages.json
```

## 5) Skip Reply Threads

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --skip-channel-replies -o analyses/teams-no-replies.json
```

## 6) Download Channel Files and Include in JSON

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --download-channel-files --max-channel-files 25 -o analyses/teams-full-scan.json
```

## 7) Operator Notes

- First run requires Microsoft interactive authentication.
- Prefer Chrome by setting `BROWSER=google-chrome`.
- Start with low limits to validate permissions and scope.
- Save outputs under `tools/teams/analyses/`.

## 8) Target a Specific Team, Channel, or Chat Text

### Filter by team name

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "OVES All" -o analyses/team-filtered.json
```

### Filter by channel name within a team

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "OVES All" --channel-name "General" -o analyses/channel-filtered.json
```

### Search for chat messages containing specific text

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "OVES All" --channel-name "General" --include-channel-messages --message-contains "warranty" -o analyses/message-search.json
```
