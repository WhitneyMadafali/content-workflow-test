#!/usr/bin/env python3
"""
MCP server for Microsoft Forms responses.

Implements a minimal JSON-RPC-over-stdio MCP-compatible server with tools to:
- resolve form IDs from forms.office.com URLs
- fetch form responses from the Microsoft Forms API
- summarize responses for quick review
"""

import base64
import json
import os
import re
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from msal import PublicClientApplication, SerializableTokenCache


FORMS_ENDPOINT = "https://forms.office.com"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
AUTHORITY = "https://login.microsoftonline.com/common"
DEFAULT_CLIENT_ID = "1df26ef8-c7ce-4aee-aff2-bc36342362e0"
DEFAULT_SCOPES_CANDIDATES = [
    ["https://forms.office.com/.default"],
    ["https://forms.office.com/Forms.Read"],
]


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload = parts[1]
        payload += "=" * ((4 - len(payload) % 4) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}


def _extract_form_id_from_url(url: str) -> Optional[str]:
    """
    Try common Forms URL shapes:
    - https://forms.office.com/r/<shortId>
    - ...?id=<formId>
    - ...?FormId=<formId>
    """
    if not url:
        return None

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    for key in ("id", "FormId", "formId"):
        values = qs.get(key)
        if values:
            return values[0]

    m = re.search(r"/r/([A-Za-z0-9_-]+)", parsed.path)
    if m:
        return m.group(1)
    return None


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


@dataclass
class FormsContext:
    access_token: str
    tenant_id: Optional[str]
    user_object_id: Optional[str]
    scope_used: List[str]


class FormsAuth:
    def __init__(self):
        self.cache_file = Path(__file__).resolve().parent / ".forms_token_cache.json"
        self.client_id = os.environ.get("FORMS_CLIENT_ID", DEFAULT_CLIENT_ID)
        self.app = PublicClientApplication(
            self.client_id,
            authority=AUTHORITY,
            token_cache=self._load_cache(),
        )
        self._ctx: Optional[FormsContext] = None

    def _load_cache(self) -> SerializableTokenCache:
        cache = SerializableTokenCache()
        if self.cache_file.exists():
            cache.deserialize(self.cache_file.read_text())
        return cache

    def _save_cache(self):
        token_cache = self.app.token_cache
        if token_cache.has_state_changed:
            self.cache_file.write_text(token_cache.serialize())

    def _scope_candidates(self) -> List[List[str]]:
        raw = os.environ.get("FORMS_SCOPES", "").strip()
        if raw:
            scopes = [s.strip() for s in raw.split(",") if s.strip()]
            if scopes:
                return [scopes]
        return DEFAULT_SCOPES_CANDIDATES

    def get_context(self) -> FormsContext:
        if self._ctx is not None:
            return self._ctx

        accounts = self.app.get_accounts()
        last_error = None

        for scopes in self._scope_candidates():
            token = None
            if accounts:
                token = self.app.acquire_token_silent(scopes, account=accounts[0])
            if not token or "access_token" not in token:
                token = self.app.acquire_token_interactive(scopes=scopes, prompt="select_account")
            if token and "access_token" in token:
                self._save_cache()
                payload = _decode_jwt_payload(token["access_token"])
                tenant_id = payload.get("tid")
                user_object_id = payload.get("oid")

                # Forms tokens can be encrypted JWE (claims not directly readable).
                # Fall back to MSAL account metadata when token claims are unavailable.
                if (not tenant_id or not user_object_id) and accounts:
                    acct = accounts[0]
                    home_account_id = acct.get("home_account_id", "")
                    if "." in home_account_id:
                        uid, utid = home_account_id.split(".", 1)
                        user_object_id = user_object_id or uid
                        tenant_id = tenant_id or utid
                    user_object_id = user_object_id or acct.get("local_account_id")

                self._ctx = FormsContext(
                    access_token=token["access_token"],
                    tenant_id=tenant_id,
                    user_object_id=user_object_id,
                    scope_used=scopes,
                )
                return self._ctx
            last_error = token

        raise RuntimeError(
            "Forms authentication failed. Ensure the app has Microsoft Forms permissions. "
            f"Last error: {last_error}"
        )

    def get_graph_token(self) -> str:
        """
        Acquire a Graph token for lightweight owner discovery (joined teams).
        Reuses the same account selected for Forms auth.
        """
        scopes = ["User.Read", "Team.ReadBasic.All"]
        accounts = self.app.get_accounts()
        token = None
        if accounts:
            token = self.app.acquire_token_silent(scopes, account=accounts[0])
        if not token or "access_token" not in token:
            token = self.app.acquire_token_interactive(scopes=scopes, prompt="select_account")
        if not token or "access_token" not in token:
            raise RuntimeError(f"Graph token acquisition failed: {token}")
        self._save_cache()
        return token["access_token"]


class FormsClient:
    def __init__(self):
        self.auth = FormsAuth()

    def _forms_request(self, url: str) -> Dict[str, Any]:
        ctx = self.auth.get_context()
        headers = {
            "Authorization": f"Bearer {ctx.access_token}",
            "Accept": "application/json",
        }
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def _graph_request(self, endpoint: str) -> Dict[str, Any]:
        token = self.auth.get_graph_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        url = endpoint if endpoint.startswith("http") else f"{GRAPH_ENDPOINT}{endpoint}"
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def resolve_form(self, form_url: str) -> Dict[str, Any]:
        # First-pass extraction from the provided URL
        extracted = _extract_form_id_from_url(form_url)

        # Follow redirects; some short links resolve to URL containing FormId/id
        resolved_url = form_url
        final_form_id = extracted
        try:
            resp = requests.get(form_url, allow_redirects=True, timeout=30)
            resolved_url = resp.url or form_url
            maybe = _extract_form_id_from_url(resolved_url)
            if maybe:
                final_form_id = maybe
        except Exception:
            # Keep best effort from original URL.
            pass

        if not final_form_id:
            raise RuntimeError(
                "Could not resolve a form ID from URL. Provide a forms.office.com URL containing /r/<id> or ?id=<id>."
            )

        return {
            "input_url": form_url,
            "resolved_url": resolved_url,
            "form_id": final_form_id,
        }

    def list_my_forms(self, top: int = 200) -> List[Dict[str, Any]]:
        ctx = self.auth.get_context()
        endpoint = f"{FORMS_ENDPOINT}/formapi/api/{ctx.tenant_id}/users/{ctx.user_object_id}/light/forms?$top={_clamp(top,1,500)}"
        payload = self._forms_request(endpoint)
        return payload.get("value", []) if isinstance(payload, dict) else []

    def list_group_forms(self, group_id: str, top: int = 200) -> List[Dict[str, Any]]:
        ctx = self.auth.get_context()
        endpoint = f"{FORMS_ENDPOINT}/formapi/api/{ctx.tenant_id}/groups/{group_id}/light/forms?$top={_clamp(top,1,500)}"
        payload = self._forms_request(endpoint)
        return payload.get("value", []) if isinstance(payload, dict) else []

    def list_joined_team_ids(self, top: int = 200) -> List[str]:
        endpoint = f"/me/joinedTeams?$select=id,displayName"
        payload = self._graph_request(endpoint)
        rows = payload.get("value", []) if isinstance(payload, dict) else []
        return [row.get("id") for row in rows[: _clamp(top, 1, 500)] if row.get("id")]

    def find_form_owner(self, form_id: str) -> Dict[str, Any]:
        # 1) Personal/user-owned forms
        for form in self.list_my_forms():
            if form.get("id") == form_id:
                ctx = self.auth.get_context()
                return {
                    "owner_type": "user",
                    "owner_id": ctx.user_object_id,
                    "tenant_id": ctx.tenant_id,
                    "form": form,
                }

        # 2) Group-owned forms for joined Teams
        for group_id in self.list_joined_team_ids():
            try:
                forms = self.list_group_forms(group_id)
            except Exception:
                continue
            for form in forms:
                if form.get("id") == form_id:
                    ctx = self.auth.get_context()
                    return {
                        "owner_type": "group",
                        "owner_id": group_id,
                        "tenant_id": ctx.tenant_id,
                        "form": form,
                    }

        raise RuntimeError(
            "Form owner not found from personal forms or joined-team group forms. "
            "Pass owner_type and owner_id explicitly."
        )

    def list_responses(
        self,
        form_id: str,
        tenant_id: Optional[str],
        owner_type: Optional[str],
        owner_id: Optional[str],
        top: int,
        skip: int,
    ) -> Dict[str, Any]:
        ctx = self.auth.get_context()
        tenant = tenant_id or ctx.tenant_id
        resolved_owner_type = owner_type
        resolved_owner_id = owner_id

        if not resolved_owner_type or not resolved_owner_id:
            owner = self.find_form_owner(form_id)
            resolved_owner_type = resolved_owner_type or owner["owner_type"]
            resolved_owner_id = resolved_owner_id or owner["owner_id"]

        if not tenant or not resolved_owner_type or not resolved_owner_id:
            raise RuntimeError("Missing tenant/owner information to query responses")

        page_top = _clamp(top, 1, 200)
        page_skip = max(0, skip)

        if resolved_owner_type not in ("user", "group"):
            raise RuntimeError("owner_type must be 'user' or 'group'")
        owner_segment = "users" if resolved_owner_type == "user" else "groups"

        endpoint = (
            f"{FORMS_ENDPOINT}/formapi/api/{tenant}/{owner_segment}/{resolved_owner_id}/light/"
            f"forms('{form_id}')/responses?$top={page_top}&$skip={page_skip}"
        )
        payload = self._forms_request(endpoint)

        items = payload.get("value") if isinstance(payload, dict) else None
        if items is None:
            # Some responses may return array directly
            items = payload if isinstance(payload, list) else []

        return {
            "tenant_id": tenant,
            "owner_type": resolved_owner_type,
            "owner_id": resolved_owner_id,
            "form_id": form_id,
            "top": page_top,
            "skip": page_skip,
            "count": len(items),
            "responses": items,
            "raw": payload,
        }


FORMS = FormsClient()


def tool_resolve_form(args: Dict[str, Any]) -> Dict[str, Any]:
    return FORMS.resolve_form(args["form_url"])


def tool_list_form_responses(args: Dict[str, Any]) -> Dict[str, Any]:
    form_id = args.get("form_id")
    if not form_id:
        if not args.get("form_url"):
            raise RuntimeError("Provide form_id or form_url")
        form_id = FORMS.resolve_form(args["form_url"])["form_id"]

    return FORMS.list_responses(
        form_id=form_id,
        tenant_id=args.get("tenant_id"),
        owner_type=args.get("owner_type"),
        owner_id=args.get("owner_id"),
        top=int(args.get("top", 50)),
        skip=int(args.get("skip", 0)),
    )


def tool_summarize_form_responses(args: Dict[str, Any]) -> Dict[str, Any]:
    payload = tool_list_form_responses(args)
    rows = payload.get("responses", [])

    # Best-effort common fields
    sample = []
    for row in rows[: min(len(rows), int(args.get("sample", 10)))]:
        sample.append(
            {
                "response_id": row.get("id") or row.get("responseId"),
                "created": row.get("createdDate") or row.get("createDate") or row.get("createdDateTime"),
                "modified": row.get("lastModifiedDate") or row.get("lastModifiedDateTime"),
                "responder": row.get("responder") or row.get("respondent") or row.get("owner"),
                "answers": row.get("answers") or row.get("questions") or row.get("responseItems"),
            }
        )

    return {
        "tenant_id": payload.get("tenant_id"),
        "owner_type": payload.get("owner_type"),
        "owner_id": payload.get("owner_id"),
        "form_id": payload.get("form_id"),
        "responses_count": payload.get("count", 0),
        "sample": sample,
    }


def tool_list_my_forms(args: Dict[str, Any]) -> Dict[str, Any]:
    top = int(args.get("top", 200))
    rows = FORMS.list_my_forms(top=top)
    return {"count": len(rows), "forms": rows}


def tool_list_group_forms(args: Dict[str, Any]) -> Dict[str, Any]:
    top = int(args.get("top", 200))
    rows = FORMS.list_group_forms(group_id=args["group_id"], top=top)
    return {"group_id": args["group_id"], "count": len(rows), "forms": rows}


def tool_find_form_owner(args: Dict[str, Any]) -> Dict[str, Any]:
    form_id = args.get("form_id")
    if not form_id:
        form_id = FORMS.resolve_form(args["form_url"])["form_id"]
    return FORMS.find_form_owner(form_id)


def tool_whoami_forms(args: Dict[str, Any]) -> Dict[str, Any]:
    ctx = FORMS.auth.get_context()
    return {
        "tenant_id": ctx.tenant_id,
        "user_object_id": ctx.user_object_id,
        "scope_used": ctx.scope_used,
        "forms_endpoint": FORMS_ENDPOINT,
    }


TOOLS: Dict[str, Dict[str, Any]] = {
    "whoami_forms": {
        "description": "Authenticate against Microsoft Forms and return token context.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_whoami_forms,
    },
    "resolve_form": {
        "description": "Resolve a forms.office.com URL into a concrete form ID.",
        "inputSchema": {
            "type": "object",
            "required": ["form_url"],
            "properties": {"form_url": {"type": "string"}},
        },
        "handler": tool_resolve_form,
    },
    "list_my_forms": {
        "description": "List forms owned by the authenticated user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "top": {"type": "integer", "minimum": 1, "maximum": 500},
            },
        },
        "handler": tool_list_my_forms,
    },
    "list_group_forms": {
        "description": "List forms owned by a Microsoft 365 group/team.",
        "inputSchema": {
            "type": "object",
            "required": ["group_id"],
            "properties": {
                "group_id": {"type": "string"},
                "top": {"type": "integer", "minimum": 1, "maximum": 500},
            },
        },
        "handler": tool_list_group_forms,
    },
    "find_form_owner": {
        "description": "Find whether a form is user-owned or group-owned (joined teams).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "form_url": {"type": "string"},
                "form_id": {"type": "string"},
            },
        },
        "handler": tool_find_form_owner,
    },
    "list_form_responses": {
        "description": "List real response records for a form from Microsoft Forms API.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "form_url": {"type": "string"},
                "form_id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "owner_type": {"type": "string", "enum": ["user", "group"]},
                "owner_id": {"type": "string"},
                "top": {"type": "integer", "minimum": 1, "maximum": 200},
                "skip": {"type": "integer", "minimum": 0},
            },
        },
        "handler": tool_list_form_responses,
    },
    "summarize_form_responses": {
        "description": "Fetch responses and return compact summary + sample rows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "form_url": {"type": "string"},
                "form_id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "owner_type": {"type": "string", "enum": ["user", "group"]},
                "owner_id": {"type": "string"},
                "top": {"type": "integer", "minimum": 1, "maximum": 200},
                "skip": {"type": "integer", "minimum": 0},
                "sample": {"type": "integer", "minimum": 1, "maximum": 50},
            },
        },
        "handler": tool_summarize_form_responses,
    },
}


def _read_message() -> Optional[Dict[str, Any]]:
    headers: Dict[str, str] = {}
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
    body = _safe_json(payload).encode("utf-8")
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
            "serverInfo": {"name": "forms-responses", "version": "0.1.0"},
            "capabilities": {"tools": {}},
        },
    )


def _handle_tools_list(message: Dict[str, Any]) -> None:
    tools = [
        {
            "name": name,
            "description": meta["description"],
            "inputSchema": meta["inputSchema"],
        }
        for name, meta in TOOLS.items()
    ]
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
            {
                "content": [
                    {
                        "type": "text",
                        "text": _safe_json(result_payload),
                    }
                ]
            },
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
                continue
            else:
                if msg_id is not None:
                    _err(msg_id, -32601, f"Method not found: {method}")
        except Exception:
            traceback.print_exc(file=sys.stderr)
            break


if __name__ == "__main__":
    main()
