#!/usr/bin/env python3
"""Simple web UI for Forms MCP summaries."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import msal
from flask import Flask, redirect, render_template, request, session, url_for


def _load_forms_server_module():
    forms_mcp_dir = Path(__file__).resolve().parent.parent / "forms-mcp"
    base = forms_mcp_dir / "server.py"
    # forms-mcp/server.py imports sibling modules like forms_url_extract.py
    if str(forms_mcp_dir) not in sys.path:
        sys.path.insert(0, str(forms_mcp_dir))
    spec = importlib.util.spec_from_file_location("forms_mcp_server", base)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load forms MCP module from {base}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FORMS_SERVER = None
TEAMS_SCANNER_MODULE = None

app = Flask(__name__)
app.secret_key = os.environ.get("FORMS_UI_SECRET_KEY", "dev-insecure-secret-change-me")
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FORMS_UI_SESSION_SECURE", "1").strip() not in {"0", "false", "False"}
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def _safe_list(value: Any) -> List[str]:
    if not value or not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def _load_teams_scanner_module():
    global TEAMS_SCANNER_MODULE
    if TEAMS_SCANNER_MODULE is not None:
        return TEAMS_SCANNER_MODULE

    teams_script = Path(__file__).resolve().parent.parent / "teams" / "scripts" / "scan-teams-graph.py"
    spec = importlib.util.spec_from_file_location("teams_scanner", teams_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Teams scanner module from {teams_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    TEAMS_SCANNER_MODULE = module
    return module


def _get_forms_server():
    global FORMS_SERVER
    if FORMS_SERVER is None:
        FORMS_SERVER = _load_forms_server_module()
    return FORMS_SERVER


def _oauth_scopes() -> List[str]:
    return [
        "User.Read",
        "Group.Read.All",
        "Team.ReadBasic.All",
        "Channel.ReadBasic.All",
        "ChannelMessage.Read.All",
        "Files.Read.All",
        "Sites.Read.All",
        "Chat.Read",
        "Chat.ReadBasic",
    ]


def _oauth_authority() -> str:
    tenant = os.environ.get("MS_TENANT_ID", "common").strip() or "common"
    return f"https://login.microsoftonline.com/{tenant}"


def _oauth_redirect_uri() -> str:
    configured = os.environ.get("MS_REDIRECT_URI", "").strip()
    if configured:
        return configured
    return url_for("auth_callback", _external=True)


def _oauth_client_id(scanner_module: Any) -> str:
    env_client_id = os.environ.get("MS_CLIENT_ID", "").strip()
    if env_client_id:
        return env_client_id
    return str(getattr(scanner_module.TeamsScanner, "CLIENT_ID", "")).strip()


def _build_confidential_client(scanner_module: Any) -> Any:
    client_id = _oauth_client_id(scanner_module)
    client_secret = os.environ.get("MS_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing OAuth configuration. Set MS_CLIENT_ID and MS_CLIENT_SECRET in Vercel environment variables."
        )
    return msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=_oauth_authority(),
        client_credential=client_secret,
    )


def _teams_access_help() -> str:
    return (
        "Connected, but no Teams were returned for this account. "
        "Confirm this user is a member of at least one Team and that Graph delegated permissions "
        "(User.Read, Group.Read.All, Team.ReadBasic.All, Channel.ReadBasic.All) are granted with admin consent."
    )


def _graph_error_hint(scanner: Any) -> str:
    raw = str(getattr(scanner, "last_graph_error", "") or "").strip()
    if not raw:
        return ""
    return f" Graph API error: {raw}"


def _get_teams_scanner(force_select_account: bool = False):
    module = _load_teams_scanner_module()
    scanner = module.TeamsScanner()
    scanner.SCOPES = list(dict.fromkeys(scanner.SCOPES + ["Chat.Read", "Chat.ReadBasic"]))
    token = (session.get("ms_access_token") or "").strip()
    if token and not force_select_account:
        scanner.access_token = token
        return scanner

    # Local fallback for non-serverless runs where browser auth is acceptable.
    ok = scanner.authenticate(force_select_account=force_select_account)
    if not ok:
        raise RuntimeError("Microsoft Teams authentication failed. Try again and sign in with the right account.")
    return scanner


def _collect_forms_urls(obj: Any, out: List[str]) -> None:
    if isinstance(obj, dict):
        for u in obj.get("forms_urls") or []:
            if isinstance(u, str) and u.startswith("http"):
                out.append(u)
        for v in obj.values():
            _collect_forms_urls(v, out)
    elif isinstance(obj, list):
        for x in obj:
            _collect_forms_urls(x, out)


def _dedupe_urls(urls: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _read_int(value: Optional[str], default: int, low: int, high: int) -> int:
    try:
        parsed = int((value or "").strip())
    except Exception:
        parsed = default
    return max(low, min(parsed, high))


def _render_page(
    *,
    error: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    teams: Optional[List[Dict[str, Any]]] = None,
    channels: Optional[List[Dict[str, Any]]] = None,
    forms_urls: Optional[List[str]] = None,
    selected_team_id: str = "",
    selected_channel_id: str = "",
    selected_form_url: str = "",
    max_responses: int = 200,
    message_limit: int = 100,
    channel_messages: Optional[List[Dict[str, Any]]] = None,
    selected_chat_id: str = "",
    chat_list: Optional[List[Dict[str, Any]]] = None,
    chat_messages: Optional[List[Dict[str, Any]]] = None,
    chat_search_text: str = "",
    chat_search_hits: Optional[List[Dict[str, Any]]] = None,
    channel_summary_text: str = "",
    sender_filter: str = "",
    days_back: int = 7,
    sender_options: Optional[List[str]] = None,
    date_from: str = "",
    date_to: str = "",
    connected: bool = False,
    summary_data: Optional[Dict[str, Any]] = None,
    summary_scope: str = "all",
    fast_mode: bool = True,
) -> Any:
    if not connected:
        connected = bool((session.get("ms_access_token") or "").strip())
    team_name = ""
    for t in teams or []:
        if str(t.get("id") or "") == selected_team_id:
            team_name = str(t.get("displayName") or "").strip()
            break

    channel_name = ""
    for c in channels or []:
        if str(c.get("id") or "") == selected_channel_id:
            channel_name = str(c.get("displayName") or "").strip()
            break

    return render_template(
        "index.html",
        error=error,
        result=result,
        teams=teams or [],
        channels=channels or [],
        forms_urls=forms_urls or [],
        selected_team_id=selected_team_id,
        selected_channel_id=selected_channel_id,
        selected_form_url=selected_form_url,
        max_responses=max_responses,
        message_limit=message_limit,
        channel_messages=channel_messages or [],
        selected_chat_id=selected_chat_id,
        chat_list=chat_list or [],
        chat_messages=chat_messages or [],
        chat_search_text=chat_search_text,
        chat_search_hits=chat_search_hits or [],
        channel_summary_text=channel_summary_text,
        sender_filter=sender_filter,
        days_back=days_back,
        sender_options=sender_options or [],
        date_from=date_from,
        date_to=date_to,
        connected=connected,
        summary_data=summary_data or {},
        summary_scope=summary_scope if summary_scope in {"all", "person"} else "all",
        fast_mode=bool(fast_mode),
        selected_team_name=team_name,
        selected_channel_name=channel_name,
        get_texts=_safe_list,
    )


def _parse_graph_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _parse_date_input(value: Optional[str], end_of_day: bool = False) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.strptime(value.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt


def _collect_channel_people(
    scanner: Any,
    team_id: str,
    channel_id: str,
    *,
    fast_mode: bool,
    parent_limit: int = 50,
    reply_limit: int = 20,
) -> List[str]:
    """Collect distinct sender names; fast mode skips reply scans."""
    names = set()
    messages = scanner.list_channel_messages(team_id, channel_id, parent_limit)
    for msg in messages:
        sender = (scanner._sender_display_name(msg) or "").strip()
        if sender:
            names.add(sender)
        if fast_mode:
            continue
        msg_id = msg.get("id")
        if not msg_id:
            continue
        try:
            replies = scanner.list_channel_message_replies(team_id, channel_id, msg_id, reply_limit)
        except Exception:
            replies = []
        for rep in replies:
            rep_sender = (scanner._sender_display_name(rep) or "").strip()
            if rep_sender:
                names.add(rep_sender)
    return sorted(names, key=lambda x: x.lower())


def _summarize_channel_messages(
    messages: List[Dict[str, Any]],
    replies_total: int,
    team_name: str,
    channel_name: str,
    date_from: str,
    date_to: str,
    sender_filter: str,
) -> str:
    if not messages:
        return "No messages were found for this channel and filter."

    enriched = []
    for m in messages:
        txt = str(m.get("body_preview") or "").strip()
        if not txt:
            continue
        enriched.append(
            {
                "sender": str(m.get("from") or "Unknown"),
                "text": txt,
                "created": _parse_graph_dt(m.get("createdDateTime")),
            }
        )
    if not enriched:
        return "Messages were retrieved, but they had no readable text content."

    blob = " ".join(item["text"].lower() for item in enriched[:120])

    theme_rules = [
        ("release planning and rollout updates", r"rollout|launch|go[- ]live|timeline|phase|release|deploy"),
        ("bugs and blockers", r"issue|bug|error|fix|blocker|incident|fail"),
        ("feature enhancements", r"feature|improve|enhancement|request|wish"),
        ("training and onboarding", r"feedback|adoption|training|onboard|usability"),
        ("approvals and decisions", r"approve|approval|decision|sign[- ]off"),
        ("forms and response collection", r"forms\.office\.com|forms\.microsoft\.com|survey|questionnaire"),
        ("operational coordination", r"ops|operation|support|handover|owner|follow up"),
    ]
    themes = [label for label, pattern in theme_rules if re.search(pattern, blob, flags=re.IGNORECASE)]

    sender_counts: Dict[str, int] = {}
    for item in enriched:
        sender_counts[item["sender"]] = sender_counts.get(item["sender"], 0) + 1
    top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    created_values = [item["created"] for item in enriched if item["created"] is not None]
    period_text = "time range unavailable"
    if created_values:
        first = min(created_values).date().isoformat()
        last = max(created_values).date().isoformat()
        period_text = f"{first} to {last}"

    scope_note = (
        f'Scope focuses on posts by "{sender_filter}".' if sender_filter else "Scope includes posts from the full channel."
    )
    what_for = (
        f"This channel is used by {team_name or 'the team'} to coordinate work in {channel_name or 'the selected channel'}, "
        + (f"mainly around {themes[0]}." if themes else "sharing updates and coordinating next steps.")
    )

    happened: List[str] = []
    for item in enriched[:8]:
        created = item["created"].date().isoformat() if item["created"] else "date unclear"
        text = item["text"][:120].rstrip()
        happened.append(f"- {created}: {item['sender']} discussed {text}.")
        if len(happened) >= 4:
            break
    if not happened:
        happened = ["- No clear activity details could be extracted from the selected messages."]

    contributors = [f"- {name} - posted {count} message(s) and helped move discussion forward." for name, count in top_senders[:4]]
    if not contributors:
        contributors = ["- Contributor details are unclear from the retrieved messages."]

    action_items: List[str] = []
    for item in enriched[:12]:
        text = item["text"]
        if re.search(r"\b(will|next|by|deadline|follow up|complete|submit|due)\b", text, flags=re.IGNORECASE):
            action_items.append(f"- {text[:130].rstrip('.')}.")
        if len(action_items) >= 3:
            break
    if not action_items:
        action_items = ["- No explicit future deadline or follow-up was clearly stated in this range."]

    tone = "Communication is collaborative and action-oriented, with contributors mostly sharing concrete updates."
    if len(enriched) < 5:
        tone = "Communication appears light in this range, with limited but focused updates."

    lines = [
        f'Messages below are from the "{channel_name or "selected channel"}" channel in the "{team_name or "selected team"}" team, covering {date_from or period_text} to {date_to or period_text}.',
        scope_note,
        "",
        "**What this channel is for**",
        what_for,
        "",
        "**What happened in this period**",
        *happened,
        "",
        "**Who was active**",
        *contributors,
        "",
        "**Upcoming or action items**",
        *action_items,
        "",
        "**Tone and engagement**",
        tone,
        f"(Analyzed {len(enriched)} messages and {replies_total} replies.)",
    ]
    return "\n".join(lines)


def _build_summary_data(
    messages: List[Dict[str, Any]],
    replies_total: int,
    sender_filter: str,
    date_from: str,
    date_to: str,
    summary_text: str,
) -> Dict[str, Any]:
    name = sender_filter if sender_filter else "Channel Summary"
    decisions: List[str] = []
    for m in messages:
        txt = str(m.get("body_preview") or "")
        if re.search(r"\b(decision|decide|approved|defer|agreed)\b", txt, flags=re.IGNORECASE):
            decisions.append(txt[:120])
    decisions = decisions[:2]

    active_days = len(
        {
            _parse_graph_dt(m.get("createdDateTime")).date().isoformat()
            for m in messages
            if _parse_graph_dt(m.get("createdDateTime")) is not None
        }
    )
    range_text = f"{date_from or 'Start'} - {date_to or 'Now'}"
    top_contributor = "The team"
    top_count = 0
    sender_counts: Dict[str, int] = {}
    for m in messages:
        sender = str(m.get("from") or "Unknown").strip() or "Unknown"
        sender_counts[sender] = sender_counts.get(sender, 0) + 1
    if sender_counts:
        top_contributor, top_count = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[0]

    snippets: List[str] = []
    for m in messages:
        txt = re.sub(r"\s+", " ", str(m.get("body_preview") or "")).strip()
        if not txt:
            continue
        dt = _parse_graph_dt(m.get("createdDateTime"))
        when = dt.strftime("%b %d") if dt else "date unclear"
        sender = str(m.get("from") or "Unknown").strip() or "Unknown"
        snippets.append(f'{when} ({sender}): "{txt[:110].rstrip()}"')
        if len(snippets) >= 2:
            break

    decisions_count = len(decisions)
    text_blob = " ".join(str(m.get("body_preview") or "") for m in messages).lower()
    nutshell = "the discussion centered on general updates and coordination"
    if re.search(r"\b(moq|stock|purchase|order|application|approve|approval)\b", text_blob, flags=re.IGNORECASE):
        nutshell = "the discussion centered on stock preparation, purchase quantities, and approval flow"
    elif re.search(r"\b(training|session|workshop|onboard)\b", text_blob, flags=re.IGNORECASE):
        nutshell = "the discussion centered on training and onboarding updates"
    elif re.search(r"\b(bug|issue|fix|error|resolved)\b", text_blob, flags=re.IGNORECASE):
        nutshell = "the discussion centered on resolving issues and tracking fixes"
    elif re.search(r"\b(forms|survey|response|questionnaire)\b", text_blob, flags=re.IGNORECASE):
        nutshell = "the discussion centered on form responses and follow-up actions"
    elif re.search(r"\b(timeline|deadline|next step|follow up|deliver)\b", text_blob, flags=re.IGNORECASE):
        nutshell = "the discussion centered on deadlines, next steps, and delivery coordination"

    threads_started = sum(1 for m in messages if bool(m.get("is_thread_start")))
    facts = [
        f"{top_contributor} contributed {top_count} item(s)",
        f"{len(messages)} total activity item(s)",
        f"{replies_total} replies in range",
        f"{active_days} active day(s)",
        f"{threads_started} thread(s) started",
        f"{decisions_count} decision phrase(s) detected",
    ]
    overview = f"In a nutshell, {nutshell}. " + "Activity summary: " + "; ".join(facts) + "."
    if snippets:
        overview += " Evidence: " + " | ".join(snippets) + "."
    return {
        "name": name,
        "range": range_text,
        "overview": overview.strip(),
        "metrics": {
            "messages": len(messages),
            "decisions": len(decisions),
            "active_days": active_days,
            "threads": threads_started,
        },
        "decisions": decisions,
        "replies": replies_total,
    }


def _build_activity_from_channel(
    scanner: Any,
    team_id: str,
    channel_id: str,
    raw_messages: List[Dict[str, Any]],
    from_ts: Optional[datetime],
    to_ts: Optional[datetime],
    sender_filter: str,
) -> tuple[List[Dict[str, Any]], int]:
    """Return activity rows (parents + replies) and total replies in selected range."""
    activity: List[Dict[str, Any]] = []
    replies_total = 0
    sender_filter_l = sender_filter.lower().strip()

    for msg in raw_messages:
        parent_sender = scanner._sender_display_name(msg) or "Unknown"
        parent_created_dt = _parse_graph_dt(msg.get("createdDateTime"))
        parent_preview = scanner._strip_html((msg.get("body") or {}).get("content", ""))[:500]

        replies: List[Dict[str, Any]] = []
        if msg.get("id"):
            replies = scanner.list_channel_message_replies(team_id, channel_id, msg["id"], 20)

        # Keep reply totals scoped to date range to avoid mismatched counters.
        for rep in replies:
            rep_created_dt = _parse_graph_dt(rep.get("createdDateTime"))
            if rep_created_dt and from_ts and rep_created_dt < from_ts:
                continue
            if rep_created_dt and to_ts and rep_created_dt > to_ts:
                continue
            replies_total += 1

        parent_in_range = True
        if parent_created_dt and from_ts and parent_created_dt < from_ts:
            parent_in_range = False
        if parent_created_dt and to_ts and parent_created_dt > to_ts:
            parent_in_range = False

        matched_reply_rows: List[Dict[str, Any]] = []
        for rep in replies:
            rep_created_dt = _parse_graph_dt(rep.get("createdDateTime"))
            if rep_created_dt and from_ts and rep_created_dt < from_ts:
                continue
            if rep_created_dt and to_ts and rep_created_dt > to_ts:
                continue
            rep_sender = scanner._sender_display_name(rep) or "Unknown"
            if sender_filter_l and sender_filter_l not in rep_sender.lower():
                continue
            rep_preview = scanner._strip_html((rep.get("body") or {}).get("content", ""))[:500]
            matched_reply_rows.append(
                {
                    "from": rep_sender,
                    "createdDateTime": rep.get("createdDateTime"),
                    "body_preview": rep_preview,
                    "is_thread_start": False,
                }
            )

        parent_sender_match = (not sender_filter_l) or (sender_filter_l in parent_sender.lower())
        if parent_in_range and parent_sender_match:
            activity.append(
                {
                    "from": parent_sender,
                    "createdDateTime": msg.get("createdDateTime"),
                    "body_preview": parent_preview,
                    "is_thread_start": True,
                }
            )
        activity.extend(matched_reply_rows)

    activity.sort(key=lambda row: _parse_graph_dt(row.get("createdDateTime")) or datetime.min.replace(tzinfo=timezone.utc))
    return activity, replies_total


def _looks_like_opaque_question_id(text: str) -> bool:
    """Heuristic: Forms light payload often uses long id-like strings."""
    value = (text or "").strip()
    if not value:
        return True
    if len(value) >= 20 and re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return True
    return False


def _human_question_title(question: Dict[str, Any], ordinal: int) -> str:
    title = str(question.get("question_title") or question.get("question_id") or "").strip()
    if _looks_like_opaque_question_id(title):
        try:
            theme_line = str(_get_forms_server().per_question_theme_line(question) or "").strip()
        except Exception:
            theme_line = ""
        if theme_line:
            theme_line = re.sub(r"^(Themes|Paraphrase):\s*", "", theme_line, flags=re.IGNORECASE)
            theme_line = theme_line.rstrip(".").strip()
            if theme_line:
                if len(theme_line) > 72:
                    theme_line = theme_line[:71].rstrip() + "…"
                return f"Theme: {theme_line}"
        return f"Question {ordinal}"
    return title


@app.get("/")
def index():
    return _render_page()


@app.get("/auth/login")
def auth_login():
    try:
        module = _load_teams_scanner_module()
        app_client = _build_confidential_client(module)
        state = os.urandom(16).hex()
        session["oauth_state"] = state
        auth_url = app_client.get_authorization_request_url(
            scopes=_oauth_scopes(),
            state=state,
            redirect_uri=_oauth_redirect_uri(),
            prompt="select_account",
        )
        return redirect(auth_url)
    except Exception as exc:
        return _render_page(error=f"Microsoft sign-in is not configured yet: {exc}")


@app.get("/auth/callback")
def auth_callback():
    if request.args.get("state", "") != session.get("oauth_state", ""):
        return _render_page(error="OAuth state mismatch. Please try signing in again.")
    code = (request.args.get("code") or "").strip()
    if not code:
        err = request.args.get("error_description") or request.args.get("error") or "Missing OAuth authorization code."
        return _render_page(error=f"Microsoft sign-in failed: {err}")

    try:
        module = _load_teams_scanner_module()
        app_client = _build_confidential_client(module)
        result = app_client.acquire_token_by_authorization_code(
            code=code,
            scopes=_oauth_scopes(),
            redirect_uri=_oauth_redirect_uri(),
        )
    except Exception as exc:
        return _render_page(error=f"Microsoft sign-in callback failed: {exc}")
    access_token = str(result.get("access_token") or "").strip()
    if not access_token:
        err = result.get("error_description") or result.get("error") or "Unknown token exchange error."
        return _render_page(error=f"Microsoft sign-in failed: {err}")

    session["ms_access_token"] = access_token
    session.pop("oauth_state", None)
    return redirect(url_for("index"))


@app.post("/teams/simple")
def simple_channel_summary():
    selected_team_id = (request.form.get("team_id") or "").strip()
    selected_channel_id = (request.form.get("channel_id") or "").strip()
    sender_filter = (request.form.get("sender_filter") or "").strip()
    days_back = _read_int(request.form.get("days_back"), 7, 1, 90)
    date_from = (request.form.get("date_from") or "").strip()
    date_to = (request.form.get("date_to") or "").strip()
    max_responses = _read_int(request.form.get("max_responses"), 200, 1, 2000)
    message_limit = _read_int(request.form.get("message_limit"), 50, 1, 50)
    action = (request.form.get("action") or "load_channels").strip()
    summary_scope = (request.form.get("summary_scope") or "all").strip().lower()
    if summary_scope not in {"all", "person"}:
        summary_scope = "all"
    fast_mode_values = [str(v).strip().lower() for v in request.form.getlist("fast_mode")]
    fast_mode = any(v in {"1", "true", "on", "yes"} for v in fast_mode_values) if fast_mode_values else True
    force_select_account = action == "sign_in"

    try:
        scanner = _get_teams_scanner(force_select_account=force_select_account)
        teams = scanner.list_joined_teams()
        if not teams:
            return _render_page(
                error=_teams_access_help() + _graph_error_hint(scanner),
                teams=[],
                max_responses=max_responses,
                message_limit=message_limit,
                days_back=days_back,
                sender_filter=sender_filter,
                date_from=date_from,
                date_to=date_to,
                connected=True,
                summary_scope=summary_scope,
                fast_mode=fast_mode,
            )

        if not selected_team_id:
            return _render_page(
                teams=teams,
                max_responses=max_responses,
                message_limit=message_limit,
                days_back=days_back,
                sender_filter=sender_filter,
                date_from=date_from,
                date_to=date_to,
                connected=True,
                summary_scope=summary_scope,
                fast_mode=fast_mode,
            )

        channels = scanner.list_team_channels(selected_team_id)
        selected_team_name = next((str(t.get("displayName") or "") for t in teams if str(t.get("id") or "") == selected_team_id), "")
        selected_channel_name = next(
            (str(c.get("displayName") or "") for c in channels if str(c.get("id") or "") == selected_channel_id),
            "",
        )
        # In "load channels" flow, default to first channel so we can preload people names.
        if action == "load_channels" and not selected_channel_id and channels:
            selected_channel_id = str(channels[0].get("id") or "")

        sender_options: List[str] = []
        # Channel refresh should stay fast; only build people list when needed.
        should_load_sender_options = bool(selected_channel_id) and (
            action in {"summarize", "load_people"} or bool(sender_filter) or summary_scope == "person"
        )
        if should_load_sender_options:
            try:
                sender_options = _collect_channel_people(
                    scanner,
                    selected_team_id,
                    selected_channel_id,
                    fast_mode=fast_mode,
                    parent_limit=20 if fast_mode else 50,
                    reply_limit=10 if fast_mode else 20,
                )
            except Exception:
                sender_options = []
        if action != "summarize" or not selected_channel_id:
            info_error = None
            if not channels:
                info_error = (
                    "No channels were returned for this team. "
                    "Try signing in again with the correct account, or choose a different team."
                ) + _graph_error_hint(scanner)
            return _render_page(
                error=info_error,
                teams=teams,
                channels=channels,
                selected_team_id=selected_team_id,
                selected_channel_id=selected_channel_id,
                max_responses=max_responses,
                message_limit=message_limit,
                days_back=days_back,
                sender_filter=sender_filter,
                sender_options=sender_options,
                date_from=date_from,
                date_to=date_to,
                connected=True,
                summary_scope=summary_scope,
                fast_mode=fast_mode,
            )

        from_ts = _parse_date_input(date_from, end_of_day=False)
        to_ts = _parse_date_input(date_to, end_of_day=True)
        raw_messages = scanner.list_channel_messages(selected_team_id, selected_channel_id, message_limit)
        messages, replies_total = _build_activity_from_channel(
            scanner,
            selected_team_id,
            selected_channel_id,
            raw_messages,
            from_ts,
            to_ts,
            sender_filter,
        )

        summary_text = _summarize_channel_messages(
            messages,
            replies_total,
            selected_team_name,
            selected_channel_name,
            date_from,
            date_to,
            sender_filter,
        )
        summary_data = _build_summary_data(
            messages,
            replies_total,
            sender_filter,
            date_from,
            date_to,
            summary_text,
        )
        return _render_page(
            teams=teams,
            channels=channels,
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            max_responses=max_responses,
            message_limit=message_limit,
            channel_messages=messages,
            channel_summary_text=summary_text,
            days_back=days_back,
            sender_filter=sender_filter,
            sender_options=sender_options,
            date_from=date_from,
            date_to=date_to,
            connected=True,
            summary_data=summary_data,
            summary_scope=summary_scope,
            fast_mode=fast_mode,
        )
    except Exception as exc:
        return _render_page(
            error=str(exc),
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            max_responses=max_responses,
            message_limit=message_limit,
            days_back=days_back,
            sender_filter=sender_filter,
            date_from=date_from,
            date_to=date_to,
            summary_scope=summary_scope,
            fast_mode=fast_mode,
        )


@app.post("/teams/load")
def load_teams():
    max_responses = _read_int(request.form.get("max_responses"), 200, 1, 2000)
    message_limit = _read_int(request.form.get("message_limit"), 50, 1, 50)
    force_select = bool(request.form.get("force_select_account"))
    try:
        scanner = _get_teams_scanner(force_select_account=force_select)
        teams = scanner.list_joined_teams()
        return _render_page(teams=teams, max_responses=max_responses, message_limit=message_limit)
    except Exception as exc:
        return _render_page(error=str(exc), max_responses=max_responses, message_limit=message_limit)


@app.post("/teams/channels")
def load_channels():
    selected_team_id = (request.form.get("team_id") or "").strip()
    max_responses = _read_int(request.form.get("max_responses"), 200, 1, 2000)
    message_limit = _read_int(request.form.get("message_limit"), 50, 1, 50)
    force_select = bool(request.form.get("force_select_account"))

    if not selected_team_id:
        return _render_page(
            error="Please choose a team first.",
            max_responses=max_responses,
            message_limit=message_limit,
        )

    try:
        scanner = _get_teams_scanner(force_select_account=force_select)
        teams = scanner.list_joined_teams()
        channels = scanner.list_team_channels(selected_team_id)
        selected_team_name = next((str(t.get("displayName") or "") for t in teams if str(t.get("id") or "") == selected_team_id), "")
        selected_channel_name = next(
            (str(c.get("displayName") or "") for c in channels if str(c.get("id") or "") == selected_channel_id),
            "",
        )
        return _render_page(
            teams=teams,
            channels=channels,
            selected_team_id=selected_team_id,
            max_responses=max_responses,
            message_limit=message_limit,
        )
    except Exception as exc:
        return _render_page(error=str(exc), max_responses=max_responses, message_limit=message_limit)


@app.post("/teams/scan-forms")
def scan_forms():
    selected_team_id = (request.form.get("team_id") or "").strip()
    selected_channel_id = (request.form.get("channel_id") or "").strip()
    max_responses = _read_int(request.form.get("max_responses"), 200, 1, 2000)
    message_limit = _read_int(request.form.get("message_limit"), 50, 1, 50)
    force_select = bool(request.form.get("force_select_account"))

    if not selected_team_id or not selected_channel_id:
        return _render_page(
            error="Please choose both a team and a channel, then scan for Forms links.",
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            max_responses=max_responses,
            message_limit=message_limit,
        )

    try:
        scanner = _get_teams_scanner(force_select_account=force_select)
        teams = scanner.list_joined_teams()
        channels = scanner.list_team_channels(selected_team_id)
        scan_data = scanner.scan_teams(
            include_messages=True,
            message_limit=message_limit,
            include_replies=True,
            reply_limit=30,
            team_id=selected_team_id,
            channel_id=selected_channel_id,
            forms_links_only=True,
        )
        urls: List[str] = []
        _collect_forms_urls(scan_data, urls)
        forms_urls = _dedupe_urls(urls)

        if not forms_urls:
            return _render_page(
                error=(
                    "No Forms links were found in channel posts/replies with current filters. "
                    "Try a higher message limit. If the form is only in a channel tab (not in posts), "
                    "paste the Forms URL manually in Step 3, or enable tab scan with "
                    "TEAMS_ENABLE_TABS_SCAN=1 after admin consent for TeamsTab.Read.All."
                ),
                teams=teams,
                channels=channels,
                selected_team_id=selected_team_id,
                selected_channel_id=selected_channel_id,
                max_responses=max_responses,
                message_limit=message_limit,
            )

        return _render_page(
            teams=teams,
            channels=channels,
            forms_urls=forms_urls,
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            selected_form_url=forms_urls[0],
            max_responses=max_responses,
            message_limit=message_limit,
        )
    except Exception as exc:
        return _render_page(
            error=str(exc),
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            max_responses=max_responses,
            message_limit=message_limit,
        )


@app.post("/teams/explore")
def explore_teams():
    selected_team_id = (request.form.get("team_id") or "").strip()
    selected_channel_id = (request.form.get("channel_id") or "").strip()
    selected_chat_id = (request.form.get("chat_id") or "").strip()
    contains_text = (request.form.get("contains_text") or "").strip()
    chat_search_text = (request.form.get("chat_search_text") or "").strip()
    max_responses = _read_int(request.form.get("max_responses"), 200, 1, 2000)
    message_limit = _read_int(request.form.get("message_limit"), 50, 1, 50)

    try:
        scanner = _get_teams_scanner(force_select_account=False)
        teams = scanner.list_joined_teams()
        channels: List[Dict[str, Any]] = []
        if selected_team_id:
            channels = scanner.list_team_channels(selected_team_id)

        messages: List[Dict[str, Any]] = []
        if selected_team_id and selected_channel_id:
            raw_messages = scanner.list_channel_messages(selected_team_id, selected_channel_id, message_limit)
            for msg in raw_messages:
                preview = scanner._strip_html((msg.get("body") or {}).get("content", ""))[:500]
                if contains_text and contains_text.lower() not in preview.lower():
                    continue
                messages.append(
                    {
                        "from": scanner._sender_display_name(msg),
                        "createdDateTime": msg.get("createdDateTime"),
                        "body_preview": preview,
                    }
                )

        chats = scanner._make_paginated_request("/me/chats?$top=25", max_items=25)
        selected_chat_messages: List[Dict[str, Any]] = []
        if selected_chat_id:
            raw_chat_messages = scanner._make_paginated_request(
                f"/chats/{selected_chat_id}/messages?$top=25", max_items=25
            )
            for msg in raw_chat_messages:
                preview = scanner._strip_html((msg.get("body") or {}).get("content", ""))[:500]
                selected_chat_messages.append(
                    {
                        "from": scanner._sender_display_name(msg),
                        "createdDateTime": msg.get("createdDateTime"),
                        "body_preview": preview,
                    }
                )

        search_hits: List[Dict[str, Any]] = []
        if chat_search_text:
            for chat in chats:
                cid = chat.get("id")
                if not cid:
                    continue
                raw_msgs = scanner._make_paginated_request(f"/chats/{cid}/messages?$top=15", max_items=15)
                for msg in raw_msgs:
                    preview = scanner._strip_html((msg.get("body") or {}).get("content", ""))[:300]
                    if chat_search_text.lower() in preview.lower():
                        search_hits.append(
                            {
                                "chat_topic": chat.get("topic") or chat.get("chatType") or "(untitled)",
                                "from": scanner._sender_display_name(msg),
                                "createdDateTime": msg.get("createdDateTime"),
                                "body_preview": preview,
                            }
                        )
            search_hits = search_hits[:30]

        return _render_page(
            teams=teams,
            channels=channels,
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            max_responses=max_responses,
            message_limit=message_limit,
            channel_messages=messages,
            selected_chat_id=selected_chat_id,
            chat_list=chats,
            chat_messages=selected_chat_messages,
            chat_search_text=chat_search_text,
            chat_search_hits=search_hits,
        )
    except Exception as exc:
        return _render_page(error=str(exc), max_responses=max_responses, message_limit=message_limit)


@app.post("/teams/summarize-channel")
def summarize_channel():
    selected_team_id = (request.form.get("team_id") or "").strip()
    selected_channel_id = (request.form.get("channel_id") or "").strip()
    contains_text = (request.form.get("contains_text") or "").strip()
    sender_filter = (request.form.get("sender_filter") or "").strip()
    days_back = _read_int(request.form.get("days_back"), 7, 1, 90)
    date_from = (request.form.get("date_from") or "").strip()
    date_to = (request.form.get("date_to") or "").strip()
    max_responses = _read_int(request.form.get("max_responses"), 200, 1, 2000)
    message_limit = _read_int(request.form.get("message_limit"), 50, 1, 50)

    if not selected_team_id or not selected_channel_id:
        return _render_page(
            error="Choose a team and channel before summarizing.",
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            max_responses=max_responses,
            message_limit=message_limit,
        )

    try:
        scanner = _get_teams_scanner(force_select_account=False)
        teams = scanner.list_joined_teams()
        channels = scanner.list_team_channels(selected_team_id)
        selected_team_name = next((str(t.get("displayName") or "") for t in teams if str(t.get("id") or "") == selected_team_id), "")
        selected_channel_name = next(
            (str(c.get("displayName") or "") for c in channels if str(c.get("id") or "") == selected_channel_id),
            "",
        )
        raw_messages = scanner.list_channel_messages(selected_team_id, selected_channel_id, message_limit)
        from_ts = _parse_date_input(date_from, end_of_day=False)
        to_ts = _parse_date_input(date_to, end_of_day=True)
        messages, replies_total = _build_activity_from_channel(
            scanner,
            selected_team_id,
            selected_channel_id,
            raw_messages,
            from_ts,
            to_ts,
            sender_filter,
        )
        if contains_text:
            needle = contains_text.lower()
            messages = [m for m in messages if needle in str(m.get("body_preview") or "").lower()]

        summary_text = _summarize_channel_messages(
            messages,
            replies_total,
            selected_team_name,
            selected_channel_name,
            date_from,
            date_to,
            sender_filter,
        )
        summary_data = _build_summary_data(
            messages,
            replies_total,
            sender_filter,
            date_from,
            date_to,
            summary_text,
        )
        return _render_page(
            teams=teams,
            channels=channels,
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            message_limit=message_limit,
            max_responses=max_responses,
            channel_messages=messages,
            channel_summary_text=summary_text,
            sender_filter=sender_filter,
            days_back=days_back,
            date_from=date_from,
            date_to=date_to,
            connected=True,
            summary_data=summary_data,
        )
    except Exception as exc:
        return _render_page(
            error=str(exc),
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            message_limit=message_limit,
            max_responses=max_responses,
            sender_filter=sender_filter,
            days_back=days_back,
            date_from=date_from,
            date_to=date_to,
        )


@app.post("/summarize")
def summarize():
    max_responses = _read_int(request.form.get("max_responses"), 200, 1, 2000)
    message_limit = _read_int(request.form.get("message_limit"), 50, 1, 50)
    selected_team_id = (request.form.get("team_id") or "").strip()
    selected_channel_id = (request.form.get("channel_id") or "").strip()
    forms_urls_json = (request.form.get("forms_urls_json") or "[]").strip()
    selected_form_url = (request.form.get("selected_form_url") or "").strip()
    direct_form_url = (request.form.get("form_url") or "").strip()
    form_url = selected_form_url or direct_form_url

    try:
        forms_urls = _dedupe_urls(json.loads(forms_urls_json))
    except Exception:
        forms_urls = []

    teams: List[Dict[str, Any]] = []
    channels: List[Dict[str, Any]] = []
    try:
        scanner = _get_teams_scanner(force_select_account=False)
        teams = scanner.list_joined_teams()
        if selected_team_id:
            channels = scanner.list_team_channels(selected_team_id)
    except Exception:
        # Keep summarize working even if Teams load fails in this request.
        pass

    if not form_url:
        return _render_page(
            error="Choose a scanned form or paste a Forms URL.",
            teams=teams,
            channels=channels,
            forms_urls=forms_urls,
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            max_responses=max_responses,
            message_limit=message_limit,
        )

    try:
        payload: Dict[str, Any] = _get_forms_server().tool_summarize_form_responses(
            {
                "form_url": form_url,
                "fetch_all": True,
                "max_responses": max_responses,
                "max_text_answers_per_question": 60,
                "max_chars_per_text_answer": 2000,
            }
        )
        for idx, question in enumerate(payload.get("by_question") or [], start=1):
            if isinstance(question, dict):
                question["display_title"] = _human_question_title(question, idx)
        return _render_page(
            result=payload,
            teams=teams,
            channels=channels,
            forms_urls=forms_urls,
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            selected_form_url=form_url,
            max_responses=max_responses,
            message_limit=message_limit,
        )
    except Exception as exc:
        return _render_page(
            error=str(exc),
            teams=teams,
            channels=channels,
            forms_urls=forms_urls,
            selected_team_id=selected_team_id,
            selected_channel_id=selected_channel_id,
            selected_form_url=form_url,
            max_responses=max_responses,
            message_limit=message_limit,
        )


if __name__ == "__main__":
    host = os.environ.get("FORMS_UI_HOST", "127.0.0.1")
    port = int(os.environ.get("FORMS_UI_PORT", "7860"))
    app.run(host=host, port=port, debug=False)
