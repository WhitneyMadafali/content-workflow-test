# OVES Teams Tools

Standalone tooling for Microsoft Teams scanning and export via Microsoft Graph API.

## Features

- Scan Team-backed groups and joined Teams
- Enumerate channels for each Team
- Export channel messages and reply threads to JSON
- Optionally download channel files and include file analysis in JSON

## Installation

```bash
cd tools/teams
pip install -r requirements.txt
```

## Usage

### Scan Teams + Channels Only

```bash
python scripts/scan-teams-graph.py -o analyses/teams-structure.json
```

### Include Channel Messages and Replies

```bash
python scripts/scan-teams-graph.py \
  --include-channel-messages \
  --message-limit 50 \
  --reply-limit 50 \
  -o analyses/teams-messages.json
```

### Include Channel Files

```bash
python scripts/scan-teams-graph.py \
  --include-channel-messages \
  --download-channel-files \
  --max-channel-files 25 \
  -o analyses/teams-full-scan.json
```

### Skip Reply Threads

```bash
python scripts/scan-teams-graph.py \
  --include-channel-messages \
  --skip-channel-replies \
  -o analyses/teams-no-replies.json
```

### List Joined Teams

```bash
python scripts/scan-teams-graph.py --list-teams
```

### Target a Specific Team/Channel and Search Chat Text

```bash
python scripts/scan-teams-graph.py \
  --team-name "OVES All" \
  --channel-name "General" \
  --include-channel-messages \
  --message-contains "warranty" \
  -o analyses/message-search.json
```

## Output and Session Files

- JSON output path is controlled with `-o/--output`
- Downloaded files are cached under `.teams-session/`
- Auth tokens are cached in `.teams_token_cache.json`

## Required Graph Permissions

- `User.Read`
- `Group.Read.All`
- `Team.ReadBasic.All`
- `Channel.ReadBasic.All`
- `ChannelMessage.Read.All`
- `Files.Read.All`
- `Sites.Read.All`
