# Forms links in Teams channels (scan + Teams MCP)

!!! warning "This page is not the Forms responses MCP"

    To read or summarize **real Microsoft Forms submissions** from **Cursor** via the **Forms API**, use **[Forms responses MCP](forms-responses-mcp.md)** (repo path `tools/forms-mcp`).

    **This page** only covers exporting or previewing **Teams channel posts** when **Microsoft Forms URLs or instructions appear in a channel**, using **Teams Scan** or **Teams MCP**. It does **not** pull the full Forms response store; for raw submissions use Forms export, Power Automate, or Graph Forms APIs (subject to tenant policy).

## 1) When to use

- Forms links, instructions, or discussion happen in a dedicated Teams channel
- You want to export posts whose body includes a Microsoft Forms URL (optionally including reply threads)

## 2) Install

Same as [Teams Scan](teams-scan.md), from `tools/teams` (use a virtual environment if your OS blocks global `pip`):

```bash
cd tools/teams
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 3) Recommended: keep only posts that contain Forms links

Use `scan-teams-graph.py` with `--forms-links-only` to keep parent messages whose body contains `forms.office.com` or `forms.microsoft.com` (you may combine with `--message-contains`; both filters apply to the parent message):

```bash
BROWSER=google-chrome .venv/bin/python scripts/scan-teams-graph.py \
  --team-name "Your team name" \
  --channel-name "Your channel name" \
  --include-channel-messages \
  --forms-links-only \
  --message-limit 100 \
  --reply-limit 30 \
  -o analyses/channel-forms-posts.json
```

Smaller test first:

```bash
BROWSER=google-chrome .venv/bin/python scripts/scan-teams-graph.py \
  --team-name "Your team name" \
  --channel-name "Your channel name" \
  --include-channel-messages \
  --forms-links-only \
  --message-limit 20 \
  --reply-limit 10 \
  -o analyses/channel-forms-posts-sample.json
```

## 4) Same channel from an MCP client

1. Start `tools/teams-mcp` as described in [Teams MCP](teams-mcp.md) and sign in.
2. Use `list_joined_teams` and `list_team_channels` to obtain `team_id` and `channel_id`.
3. Call `list_channel_messages`, then filter `body_preview` for `forms.office.com` or `forms.microsoft.com` (optionally combine with keyword search).

## 5) Limits

| Capability | Notes |
|------------|--------|
| Channel posts and replies | Exported as JSON (Teams scan) or returned as previews (MCP) |
| Full Forms response store | **Out of scope** here; use [Forms responses MCP](forms-responses-mcp.md) or export / Graph |

## 6) See also

- [Forms responses MCP](forms-responses-mcp.md)
- [Teams Scan](teams-scan.md)
- [Teams MCP](teams-mcp.md)
