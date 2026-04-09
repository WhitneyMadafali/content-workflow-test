# Teams MCP Guide

This page explains how to run the `tools/teams-mcp` MCP server to access Teams channels and chats.

## 1) Start From Zero (No Local Repo Yet)

### Prerequisites

- `git` installed
- `python3` and `pip` installed
- Microsoft 365 account with Teams access

### Clone the repository

```bash
git clone https://github.com/ovesorg/content-workflow.git
cd content-workflow
```

## 2) Install

```bash
cd tools/teams-mcp
pip install -r requirements.txt
```

## 3) Start MCP Server

```bash
BROWSER=google-chrome python server.py
```

The first run triggers Microsoft interactive authentication.

## 4) Connect in Your MCP Client

Configure the MCP server command as:

```bash
python tools/teams-mcp/server.py
```

If you want to force Chrome:

```bash
BROWSER=google-chrome python tools/teams-mcp/server.py
```

## 5) Exposed MCP Tools

- `list_joined_teams`: list Teams available to the user
- `list_team_channels`: list channels for a Team
- `list_channel_messages`: read channel messages (optionally with replies)
- `list_chats`: list personal/group/meeting chats
- `list_chat_messages`: read messages in one chat
- `search_chat_messages`: keyword search across chats

## 6) Typical Use Cases

- Targeted lookup by Team/channel
- Keyword search for discussions by any text
- Structured JSON message feed for downstream workflows
