# Teams MCP Server

MCP server for Microsoft Teams channels and chats.

## Features

- List joined Teams
- List channels in a Team
- Read channel messages and replies
- List chats and chat messages
- Search chat messages by keyword

## Install

```bash
cd tools/teams-mcp
pip install -r requirements.txt
```

## Run

```bash
python server.py
```

The server uses Microsoft interactive authentication (MSAL) on first run.
Set browser explicitly if needed:

```bash
BROWSER=google-chrome python server.py
```

## Exposed MCP Tools

- `list_joined_teams(name_contains?, limit?)`
- `list_team_channels(team_id, name_contains?, limit?)`
- `list_channel_messages(team_id, channel_id, limit?, contains_text?, include_replies?, reply_limit?)`
- `list_chats(topic_contains?, limit?)`
- `list_chat_messages(chat_id, limit?, contains_text?)`
- `search_chat_messages(contains_text, chats_limit?, messages_per_chat?)`

## Notes

- `list_chat_messages` and chat search use Graph chat limits (`$top <= 50`) to avoid API errors.
- The server reuses the Teams scanner auth flow and token cache from `tools/teams`.
- This implementation is a stdio MCP server with JSON-RPC framing (`Content-Length`), so it can be connected directly from MCP clients.
