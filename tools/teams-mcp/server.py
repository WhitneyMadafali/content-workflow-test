#!/usr/bin/env python3
"""
Dependency-light MCP server for Microsoft Teams channels and chats.

Implements enough of MCP over stdio JSON-RPC to support:
- initialize
- tools/list
- tools/call
- ping
"""

import importlib.util
import json
import sys
import traceback
import difflib
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_scanner_class():
    scan_script = Path(__file__).resolve().parents[1] / "teams" / "scripts" / "scan-teams-graph.py"
    spec = importlib.util.spec_from_file_location("scan_teams_graph", scan_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Teams scanner from {scan_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TeamsScanner


TeamsScanner = _load_scanner_class()


class ScannerState:
    scanner: Optional[Any] = None

    @classmethod
    def get(cls):
        if cls.scanner is None:
            scanner = TeamsScanner()
            scanner.SCOPES = list(dict.fromkeys(scanner.SCOPES + ["Chat.Read", "Chat.ReadBasic"]))
            if not scanner.authenticate():
                raise RuntimeError("Microsoft authentication failed")
            cls.scanner = scanner
        return cls.scanner


def _msg_preview(scanner: Any, payload: Dict[str, Any]) -> str:
    return scanner._strip_html((payload.get("body") or {}).get("content", ""))[:500]


def _sender(scanner: Any, payload: Dict[str, Any]) -> Optional[str]:
    return scanner._sender_display_name(payload)


def _contains(haystack: Optional[str], needle: Optional[str]) -> bool:
    if not needle:
        return True
    if not haystack:
        return False

    raw_h = haystack.lower()
    raw_n = needle.lower()
    if raw_n in raw_h:
        return True

    def norm(value: str) -> str:
        out = []
        for char in value.lower():
            cat = unicodedata.category(char)
            if cat.startswith("L") or cat.startswith("N"):
                out.append(char)
            else:
                out.append(" ")
        return re.sub(r"\s+", " ", "".join(out)).strip()

    norm_h = norm(haystack)
    norm_n = norm(needle)
    if not norm_n:
        return True
    if norm_n in norm_h:
        return True

    compact_h = norm_h.replace(" ", "")
    compact_n = norm_n.replace(" ", "")
    if compact_n and compact_n in compact_h:
        return True

    if len(compact_h) <= 80:
        if difflib.SequenceMatcher(None, compact_h, compact_n).ratio() >= 0.82:
            return True

    if len(compact_n) >= 4 and len(compact_h) > len(compact_n):
        win = len(compact_n)
        step = max(1, win // 3)
        pos = 0
        while pos < len(compact_h):
            segment = compact_h[pos:pos + win]
            if not segment:
                break
            if difflib.SequenceMatcher(None, segment, compact_n).ratio() >= 0.82:
                return True
            pos += step

    return False


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def tool_list_joined_teams(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    scanner = ScannerState.get()
    name_contains = args.get("name_contains")
    limit = _clamp(int(args.get("limit", 100)), 1, 500)
    teams = scanner.list_joined_teams()
    if name_contains:
        teams = [team for team in teams if _contains(team.get("displayName"), name_contains)]
    return teams[:limit]


def tool_list_team_channels(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    scanner = ScannerState.get()
    team_id = args["team_id"]
    name_contains = args.get("name_contains")
    limit = _clamp(int(args.get("limit", 200)), 1, 200)
    channels = scanner.list_team_channels(team_id)
    if name_contains:
        channels = [channel for channel in channels if _contains(channel.get("displayName"), name_contains)]
    return channels[:limit]


def tool_list_channel_messages(args: Dict[str, Any]) -> Dict[str, Any]:
    scanner = ScannerState.get()
    team_id = args["team_id"]
    channel_id = args["channel_id"]
    limit = _clamp(int(args.get("limit", 50)), 1, 200)
    contains_text = args.get("contains_text")
    include_replies = bool(args.get("include_replies", True))
    reply_limit = _clamp(int(args.get("reply_limit", 20)), 1, 200)
    messages = scanner.list_channel_messages(team_id, channel_id, limit)

    out_messages: List[Dict[str, Any]] = []
    replies_total = 0
    for message in messages:
        preview = _msg_preview(scanner, message)
        if contains_text and not _contains(preview, contains_text):
            continue
        row = {
            "id": message.get("id"),
            "createdDateTime": message.get("createdDateTime"),
            "lastModifiedDateTime": message.get("lastModifiedDateTime"),
            "from": _sender(scanner, message),
            "subject": message.get("subject"),
            "summary": message.get("summary"),
            "body_preview": preview,
            "webUrl": message.get("webUrl"),
            "replyToId": message.get("replyToId"),
        }
        if include_replies and message.get("id"):
            replies = scanner.list_channel_message_replies(team_id, channel_id, message["id"], reply_limit)
            replies_total += len(replies)
            row["replies_count"] = len(replies)
            row["replies"] = [
                {
                    "id": reply.get("id"),
                    "createdDateTime": reply.get("createdDateTime"),
                    "lastModifiedDateTime": reply.get("lastModifiedDateTime"),
                    "from": _sender(scanner, reply),
                    "subject": reply.get("subject"),
                    "summary": reply.get("summary"),
                    "body_preview": _msg_preview(scanner, reply),
                    "webUrl": reply.get("webUrl"),
                    "replyToId": reply.get("replyToId"),
                }
                for reply in replies
            ]
        out_messages.append(row)
    return {
        "team_id": team_id,
        "channel_id": channel_id,
        "messages_count": len(out_messages),
        "replies_count": replies_total,
        "messages": out_messages,
    }


def tool_list_chats(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    scanner = ScannerState.get()
    topic_contains = args.get("topic_contains")
    limit = _clamp(int(args.get("limit", 50)), 1, 200)
    page_top = _clamp(limit, 1, 50)
    chats = scanner._make_paginated_request(f"/me/chats?$top={page_top}", max_items=limit)
    if topic_contains:
        chats = [chat for chat in chats if _contains(chat.get("topic"), topic_contains)]
    return chats[:limit]


def tool_list_chat_messages(args: Dict[str, Any]) -> Dict[str, Any]:
    scanner = ScannerState.get()
    chat_id = args["chat_id"]
    limit = _clamp(int(args.get("limit", 50)), 1, 50)
    contains_text = args.get("contains_text")
    messages = scanner._make_paginated_request(f"/chats/{chat_id}/messages?$top={limit}", max_items=limit)
    out_messages = []
    for message in messages:
        preview = _msg_preview(scanner, message)
        if contains_text and not _contains(preview, contains_text):
            continue
        out_messages.append(
            {
                "id": message.get("id"),
                "createdDateTime": message.get("createdDateTime"),
                "lastModifiedDateTime": message.get("lastModifiedDateTime"),
                "from": _sender(scanner, message),
                "subject": message.get("subject"),
                "summary": message.get("summary"),
                "body_preview": preview,
                "webUrl": message.get("webUrl"),
                "chatId": chat_id,
            }
        )
    return {"chat_id": chat_id, "messages_count": len(out_messages), "messages": out_messages}


def tool_search_chat_messages(args: Dict[str, Any]) -> Dict[str, Any]:
    scanner = ScannerState.get()
    contains_text = args["contains_text"]
    chats_limit = _clamp(int(args.get("chats_limit", 30)), 1, 200)
    messages_per_chat = _clamp(int(args.get("messages_per_chat", 30)), 1, 50)
    page_top = _clamp(chats_limit, 1, 50)
    chats = scanner._make_paginated_request(f"/me/chats?$top={page_top}", max_items=chats_limit)
    matched_chats = []
    total_hits = 0
    for chat in chats:
        chat_id = chat.get("id")
        if not chat_id:
            continue
        messages = scanner._make_paginated_request(
            f"/chats/{chat_id}/messages?$top={messages_per_chat}", max_items=messages_per_chat
        )
        hits = []
        for message in messages:
            preview = _msg_preview(scanner, message)
            if _contains(preview, contains_text):
                hits.append(
                    {
                        "id": message.get("id"),
                        "createdDateTime": message.get("createdDateTime"),
                        "from": _sender(scanner, message),
                        "body_preview": preview,
                        "webUrl": message.get("webUrl"),
                    }
                )
        if hits:
            total_hits += len(hits)
            matched_chats.append(
                {
                    "chat_id": chat_id,
                    "topic": chat.get("topic"),
                    "chatType": chat.get("chatType"),
                    "matched_messages_count": len(hits),
                    "matched_messages": hits,
                }
            )
    return {
        "contains_text": contains_text,
        "matched_chats_count": len(matched_chats),
        "matched_messages_total": total_hits,
        "matched_chats": matched_chats,
    }


TOOLS: Dict[str, Dict[str, Any]] = {
    "list_joined_teams": {
        "description": "List joined Teams (optional display-name filter).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name_contains": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            },
        },
        "handler": tool_list_joined_teams,
    },
    "list_team_channels": {
        "description": "List channels for one Team ID.",
        "inputSchema": {
            "type": "object",
            "required": ["team_id"],
            "properties": {
                "team_id": {"type": "string"},
                "name_contains": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
        },
        "handler": tool_list_team_channels,
    },
    "list_channel_messages": {
        "description": "List messages from one channel (optional replies and text filter).",
        "inputSchema": {
            "type": "object",
            "required": ["team_id", "channel_id"],
            "properties": {
                "team_id": {"type": "string"},
                "channel_id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "contains_text": {"type": "string"},
                "include_replies": {"type": "boolean"},
                "reply_limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
        },
        "handler": tool_list_channel_messages,
    },
    "list_chats": {
        "description": "List personal/group/meeting chats.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic_contains": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
        },
        "handler": tool_list_chats,
    },
    "list_chat_messages": {
        "description": "List messages in one chat (optional text filter).",
        "inputSchema": {
            "type": "object",
            "required": ["chat_id"],
            "properties": {
                "chat_id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                "contains_text": {"type": "string"},
            },
        },
        "handler": tool_list_chat_messages,
    },
    "search_chat_messages": {
        "description": "Search across chats for a keyword.",
        "inputSchema": {
            "type": "object",
            "required": ["contains_text"],
            "properties": {
                "contains_text": {"type": "string"},
                "chats_limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "messages_per_chat": {"type": "integer", "minimum": 1, "maximum": 50},
            },
        },
        "handler": tool_search_chat_messages,
    },
}


def _read_message() -> Optional[Dict[str, Any]]:
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        decoded = line.decode("utf-8").strip()
        if ":" in decoded:
            key, value = decoded.split(":", 1)
            headers[key.lower().strip()] = value.strip()
    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        return None
    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _write_message(payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header + body)
    sys.stdout.buffer.flush()


def _ok(msg_id: Any, result: Dict[str, Any]) -> None:
    _write_message({"jsonrpc": "2.0", "id": msg_id, "result": result})


def _err(msg_id: Any, code: int, message: str) -> None:
    _write_message({"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}})


def _handle_initialize(message: Dict[str, Any]) -> None:
    _ok(
        message.get("id"),
        {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "teams-channels-chats", "version": "0.1.0"},
            "capabilities": {"tools": {}},
        },
    )


def _handle_tools_list(message: Dict[str, Any]) -> None:
    tools = []
    for name, meta in TOOLS.items():
        tools.append({"name": name, "description": meta["description"], "inputSchema": meta["inputSchema"]})
    _ok(message.get("id"), {"tools": tools})


def _handle_tools_call(message: Dict[str, Any]) -> None:
    params = message.get("params", {}) or {}
    name = params.get("name")
    arguments = params.get("arguments", {}) or {}
    if name not in TOOLS:
        _err(message.get("id"), -32601, f"Unknown tool: {name}")
        return
    try:
        result_payload = TOOLS[name]["handler"](arguments)
        _ok(
            message.get("id"),
            {"content": [{"type": "text", "text": json.dumps(result_payload, ensure_ascii=False)}]},
        )
    except Exception as exc:
        _err(message.get("id"), -32603, f"Tool call failed: {exc}")


def main() -> None:
    while True:
        try:
            message = _read_message()
            if message is None:
                break
            method = message.get("method")
            msg_id = message.get("id")

            if method == "initialize":
                _handle_initialize(message)
            elif method == "tools/list":
                _handle_tools_list(message)
            elif method == "tools/call":
                _handle_tools_call(message)
            elif method == "ping":
                if msg_id is not None:
                    _ok(msg_id, {})
            elif method == "notifications/initialized":
                # No response required.
                continue
            else:
                if msg_id is not None:
                    _err(msg_id, -32601, f"Method not found: {method}")
        except Exception:
            traceback.print_exc(file=sys.stderr)
            break


if __name__ == "__main__":
    main()
