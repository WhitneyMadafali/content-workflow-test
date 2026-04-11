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
from forms_url_extract import extract_forms_urls_from_html
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


_ASSISTANT_SUMMARIZE_PREAMBLE = (
    "[Instructions for the assistant — do not show this block verbatim to the user as raw data. "
    "Read the JSON below and reply with a concise thematic summary only: form title, response count, "
    "rating stats per numeric question, and per open-ended question what people said (themes, quotes sparingly). "
    "Do not paste the full JSON or long lists of verbatim answers in your user-facing reply unless asked.]\n\n"
)


def _wrap_summarize_tool_text(payload: Dict[str, Any]) -> str:
    """Prepend guidance so the client model summarizes instead of echoing JSON."""
    return _ASSISTANT_SUMMARIZE_PREAMBLE + _safe_json(payload)


def _brief_question_heading(block: Dict[str, Any], ordinal: int) -> str:
    """Use real title when readable; otherwise 'Question N' (Forms light payload often uses opaque ids)."""
    title = str(block.get("question_title") or block.get("question_id") or "?").strip()
    if len(title) >= 20 and title.startswith("r"):
        return f"Question {ordinal}"
    return title


def _truncate_line(text: str, max_len: int = 240) -> str:
    one = " ".join(text.split())
    if len(one) <= max_len:
        return one
    return one[: max_len - 1] + "…"


def _english_join_phrases(items: List[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _extract_themes_from_text_blob(blob: str) -> List[str]:
    """Lightweight theme labels from combined answer text (no external LLM)."""
    b = blob.lower()
    out: List[str] = []

    def add(label: str) -> None:
        if label not in out:
            out.append(label)

    if re.search(r"pdf|export.*quote|quote.*export|\bpdf\b", b):
        add("exporting or sharing quotes as PDF (or similar documents)")
    if re.search(r"stock|inventory", b):
        add("stock or inventory visibility")
    if re.search(r"manager|approv|discount|b2c", b):
        add("manager visibility, approvals, discounts, or B2C-specific rules")
    if re.search(r"vat|sales\s*person|company detail|excel quote|richer quote", b):
        add("richer quote content (fields, VAT, branding, parity with Excel)")
    if re.search(r"applet|phone|desktop|layout|design|clear|easy to use|well designed", b):
        add("UX and layout (clarity, applets, phone and desktop)")
    if re.search(r"integrat|quicker|faster|efficient|simple|utility", b):
        add("speed, simplicity, or integration with how work is done today")
    if re.search(r"adopt|beneficial|long run|effort", b):
        add("adoption effort versus long-term benefit")
    if re.search(r"not sure|try portal|really work|hands-on", b):
        add("need for more hands-on use before deciding")
    return out


def build_executive_summary(
    form_title: str, response_count: int, by_question: List[Dict[str, Any]]
) -> str:
    """
    Short narrative synthesis (rule-based). For LLM-quality prose, use the assistant + synthesis_hint.
    """
    if response_count <= 0:
        return f'No responses were loaded for "{form_title}".'

    all_text: List[str] = []
    rating_bits: List[str] = []
    for block in by_question:
        for t in block.get("respondent_texts") or []:
            all_text.append(t)
        if block.get("rating"):
            r = block["rating"]
            rating_bits.append(
                f"a numeric rating averaging {r['average']} (min {r['min']}, max {r['max']})"
            )

    blob = " ".join(all_text)
    all_themes = _extract_themes_from_text_blob(blob)
    themes = all_themes[:5]

    parts: List[str] = []
    parts.append(
        f'Summary of "{form_title}" based on {response_count} response(s). '
    )
    if themes:
        parts.append(
            "Across open-ended answers, main themes include: "
            + _english_join_phrases(themes)
            + ". "
        )
        if len(all_themes) > len(themes):
            parts.append("Other points appear in the per-question lines or full export. ")
    else:
        parts.append("See per-question lines below for what people wrote. ")

    if rating_bits:
        parts.append("Ratings: " + "; ".join(rating_bits) + ". ")

    parts.append(
        "This is an automatic thematic sketch, not a substitute for reading nuanced feedback when decisions depend on exact wording."
    )
    return "".join(parts).strip()


def per_question_theme_line(block: Dict[str, Any]) -> str:
    """One line per open question: themes or a short paraphrase starter."""
    texts = block.get("respondent_texts") or []
    if not texts:
        return ""
    blob = " ".join(texts)
    themes = _extract_themes_from_text_blob(blob)
    if themes:
        return "Themes: " + _english_join_phrases(themes) + "."
    return "Paraphrase: " + _truncate_line(texts[0], 220)


def format_brief_cli_summary(payload: Dict[str, Any]) -> str:
    """Readable report: executive summary first, then one theme line per question; minimal quote bullets."""
    lines: List[str] = []
    title = payload.get("form_title") or "(unknown form)"
    n = int(payload.get("responses_count") or 0)
    exec_s = payload.get("executive_summary") or ""

    lines.append("=" * 60)
    lines.append("SUMMARY (thematic — read this first)")
    lines.append("=" * 60)
    lines.append(exec_s if exec_s else "(No executive summary; see JSON without --brief.)")
    lines.append("")

    lines.append(f"Form: {title}")
    lines.append(f"Responses analyzed: {n}")
    lines.append("")
    lines.append("— Per question (theme lines only; no full quotes in --brief) —")
    lines.append("")

    bq = payload.get("by_question") or []
    if not bq:
        lines.append("(No per-question data parsed.)")
        lines.append("Tip: run without --brief for full JSON.")
        return "\n".join(lines)

    for i, block in enumerate(bq, start=1):
        heading = _brief_question_heading(block, i)
        lines.append(f"--- {heading} ---")
        if block.get("rating"):
            r = block["rating"]
            lines.append(
                f"  Rating: average {r['average']} (of {r['count']} answers, min {r['min']}, max {r['max']})"
            )
        texts = block.get("respondent_texts") or block.get("text_excerpts") or []
        if texts:
            tl = per_question_theme_line(block)
            if tl:
                lines.append(f"  {tl}")
        lines.append("")

    lines.append("— Full verbatim answers: omit --brief. Deeper prose: ask the Cursor assistant. —")
    return "\n".join(lines).rstrip()


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


def _parse_answers_field(raw: Any) -> List[Dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
        except json.JSONDecodeError:
            return []
    return []


def _plain_question_title(title: Any) -> str:
    if title is None:
        return ""
    if isinstance(title, str):
        return title.strip()
    if isinstance(title, dict):
        return str(
            title.get("plainText") or title.get("text") or title.get("title") or ""
        ).strip()
    return str(title).strip()


def _question_id_to_title(form_obj: Dict[str, Any]) -> Dict[str, str]:
    """Map Forms questionId -> human-readable title from form definition."""
    out: Dict[str, str] = {}

    def walk(items: Any) -> None:
        if not items or not isinstance(items, list):
            return
        for q in items:
            if not isinstance(q, dict):
                continue
            qid = q.get("id") or q.get("questionId")
            title = _plain_question_title(
                q.get("title") or q.get("questionText") or q.get("text")
            )
            if qid:
                out[str(qid)] = title if title else str(qid)
            nested = q.get("questions") or q.get("subQuestions")
            walk(nested)

    for key in ("questions", "descriptiveQuestions"):
        walk(form_obj.get(key))
    return out


def _looks_like_rating_value(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    if s.isdigit():
        n = int(s)
        return 1 <= n <= 10
    try:
        f = float(s)
        return 1.0 <= f <= 10.0
    except ValueError:
        return False


def _aggregate_answers_by_question(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Per questionId: numeric samples + text answers."""
    per: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        for item in _parse_answers_field(row.get("answers")):
            qid = item.get("questionId")
            if not qid:
                continue
            qid = str(qid)
            val = item.get("answer1")
            if val is None:
                val = item.get("answer")
            text = str(val).strip() if val is not None else ""
            per.setdefault(qid, {"numbers": [], "texts": []})
            if not text:
                continue
            if _looks_like_rating_value(text):
                try:
                    per[qid]["numbers"].append(float(text) if "." in text else int(text))
                except ValueError:
                    per[qid]["texts"].append(text)
            else:
                per[qid]["texts"].append(text)
    return per


def _rating_summary(nums: List[float]) -> Dict[str, Any]:
    if not nums:
        return {}
    nums_f = [float(n) for n in nums]
    avg = sum(nums_f) / len(nums_f)
    return {
        "count": len(nums_f),
        "min": min(nums_f),
        "max": max(nums_f),
        "average": round(avg, 2),
    }


def _build_summary_text(
    form_title: str,
    response_count: int,
    by_question: List[Dict[str, Any]],
) -> str:
    """Short narrative for humans; open-ended detail lives in by_question.respondent_texts."""
    parts: List[str] = []
    parts.append(f'Form "{form_title}" has {response_count} response(s).')
    rating_bits: List[str] = []
    open_bits: List[str] = []
    for block in by_question:
        title = block.get("question_title") or block.get("question_id")
        if block.get("rating"):
            r = block["rating"]
            rating_bits.append(
                f'"{title}" averages {r["average"]} (n={r["count"]}, range {r["min"]}-{r["max"]}).'
            )
        n_txt = block.get("text_response_count") or 0
        if n_txt > 0 and block.get("respondent_texts") is not None:
            n_included = len(block["respondent_texts"])
            total = block.get("text_answers_in_dataset", n_txt)
            open_bits.append(
                f'"{title}": {total} text answer(s); {n_included} included below for synthesis.'
            )
    if rating_bits:
        parts.append(" ".join(rating_bits))
    if open_bits:
        parts.append("Open-ended: " + " ".join(open_bits))
    return " ".join(parts)


def _summarize_responses_enriched(
    form_title: str,
    question_map: Dict[str, str],
    rows: List[Dict[str, Any]],
    max_excerpt_chars: int,
    max_text_answers_per_question: int,
    max_chars_per_text_answer: int,
) -> Tuple[List[Dict[str, Any]], str]:
    agg = _aggregate_answers_by_question(rows)
    by_question: List[Dict[str, Any]] = []
    cap_answers = _clamp(max_text_answers_per_question, 1, 500)
    cap_chars = _clamp(max_chars_per_text_answer, 200, 8000)

    for qid in sorted(agg.keys(), key=lambda x: (question_map.get(x, x), x)):
        block = agg[qid]
        nums = block["numbers"]
        texts = block["texts"]
        title = question_map.get(qid, qid)
        entry: Dict[str, Any] = {
            "question_id": qid,
            "question_title": title,
            "answered_count": len(nums) + len(texts),
        }
        if nums:
            entry["rating"] = _rating_summary(nums)
        if texts:
            excerpts = []
            for t in texts[:5]:
                if len(t) <= max_excerpt_chars:
                    excerpts.append(t)
                else:
                    excerpts.append(t[: max_excerpt_chars - 1] + "…")
            entry["text_excerpts"] = excerpts
            entry["text_response_count"] = len(texts)

            respondent_texts: List[str] = []
            for t in texts[:cap_answers]:
                tt = t.strip()
                if len(tt) > cap_chars:
                    tt = tt[: cap_chars - 1] + "…"
                respondent_texts.append(tt)
            entry["respondent_texts"] = respondent_texts
            entry["text_answers_in_dataset"] = len(texts)
            if len(texts) > len(respondent_texts):
                entry["text_answers_omitted"] = len(texts) - len(respondent_texts)
        by_question.append(entry)

    summary_text = _build_summary_text(form_title, len(rows), by_question)
    return by_question, summary_text


def _gather_response_rows(
    form_id: str,
    tenant_id: Optional[str],
    owner_type: Optional[str],
    owner_id: Optional[str],
    top: int,
    skip: int,
    fetch_all: bool,
    max_responses: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Collect one or more pages of responses. fetch_all paginates until short page or cap."""
    rows: List[Dict[str, Any]] = []
    last: Dict[str, Any] = {}
    cap = _clamp(max_responses, 1, 5000)
    page = _clamp(top, 1, 200)
    cur_skip = max(0, skip)

    while len(rows) < cap:
        take = min(page, cap - len(rows))
        last = FORMS.list_responses(
            form_id=form_id,
            tenant_id=tenant_id,
            owner_type=owner_type,
            owner_id=owner_id,
            top=take,
            skip=cur_skip,
        )
        batch = last.get("responses", [])
        if not batch:
            break
        rows.extend(batch)
        if not fetch_all:
            break
        if len(batch) < take:
            break
        cur_skip += len(batch)

    return rows, last


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
                accounts = self.app.get_accounts()
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
        u = (form_url or "").strip()
        if "safelinks.protection.outlook.com" in u.lower():
            unwrapped = extract_forms_urls_from_html(u)
            if unwrapped:
                form_url = unwrapped[0]
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
    form_id = args.get("form_id")
    if not form_id:
        if not args.get("form_url"):
            raise RuntimeError("Provide form_id or form_url")
        form_id = FORMS.resolve_form(args["form_url"])["form_id"]

    owner_info: Dict[str, Any] = {}
    form_obj: Dict[str, Any] = {}
    try:
        owner_info = FORMS.find_form_owner(form_id)
        form_obj = owner_info.get("form") or {}
    except RuntimeError:
        pass

    form_title = (form_obj.get("title") or "Untitled form").strip()
    question_map = _question_id_to_title(form_obj)

    tenant_id = args.get("tenant_id")
    owner_type = args.get("owner_type") or owner_info.get("owner_type")
    owner_id = args.get("owner_id") or owner_info.get("owner_id")

    fetch_all = bool(args.get("fetch_all", True))
    max_responses = _clamp(int(args.get("max_responses", 2000)), 1, 5000)
    page_top = int(args.get("top", 200))
    page_skip = int(args.get("skip", 0))

    rows, payload = _gather_response_rows(
        form_id=form_id,
        tenant_id=tenant_id,
        owner_type=owner_type,
        owner_id=owner_id,
        top=page_top,
        skip=page_skip,
        fetch_all=fetch_all,
        max_responses=max_responses,
    )

    max_excerpt = _clamp(int(args.get("max_excerpt_chars", 400)), 80, 2000)
    max_text_answers = _clamp(int(args.get("max_text_answers_per_question", 100)), 1, 500)
    max_chars_answer = _clamp(int(args.get("max_chars_per_text_answer", 2000)), 200, 8000)
    by_question, summary_text = _summarize_responses_enriched(
        form_title,
        question_map,
        rows,
        max_excerpt_chars=max_excerpt,
        max_text_answers_per_question=max_text_answers,
        max_chars_per_text_answer=max_chars_answer,
    )

    sample_n = _clamp(int(args.get("sample", 10)), 1, 50)
    sample_respondents = []
    for row in rows[:sample_n]:
        sample_respondents.append(
            {
                "response_id": row.get("id") or row.get("responseId"),
                "startDate": row.get("startDate"),
                "submitDate": row.get("submitDate"),
                "responder": row.get("responder") or row.get("respondent") or row.get("owner"),
                "responderName": row.get("responderName"),
            }
        )

    synthesis_hint = (
        "Prefer presenting executive_summary to the user first, then expand using by_question.respondent_texts "
        "only if detail is needed. For each entry with respondent_texts: explain themes, sentiment, action items. "
        "Rating-only questions use rating stats. If text_answers_omitted is set, note truncated coverage."
    )

    executive_summary = build_executive_summary(form_title, len(rows), by_question)

    return {
        "tenant_id": payload.get("tenant_id"),
        "owner_type": payload.get("owner_type"),
        "owner_id": payload.get("owner_id"),
        "form_id": payload.get("form_id"),
        "form_title": form_title,
        "responses_count": len(rows),
        "fetch_all_used": fetch_all,
        "max_responses_cap": max_responses,
        "executive_summary": executive_summary,
        "synthesis_hint": synthesis_hint,
        "summary_text": summary_text,
        "by_question": by_question,
        "sample_respondents": sample_respondents,
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
        "description": "Aggregates form responses. Returns executive_summary (automatic thematic paragraph), summary_text, by_question (ratings + respondent_texts), synthesis_hint. Lead with executive_summary for the user when possible; use respondent_texts only for detail.",
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
                "fetch_all": {
                    "type": "boolean",
                    "description": "If true (default), keep requesting pages until a short page or max_responses.",
                },
                "max_responses": {"type": "integer", "minimum": 1, "maximum": 5000},
                "sample": {"type": "integer", "minimum": 1, "maximum": 50},
                "max_excerpt_chars": {"type": "integer", "minimum": 80, "maximum": 2000},
                "max_text_answers_per_question": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Max verbatim text answers per question in by_question.respondent_texts (default 100).",
                },
                "max_chars_per_text_answer": {
                    "type": "integer",
                    "minimum": 200,
                    "maximum": 8000,
                    "description": "Trim each text answer to this length (default 2000).",
                },
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
            "serverInfo": {"name": "forms-responses", "version": "0.2.0"},
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
        text_out = (
            _wrap_summarize_tool_text(result_payload)
            if name == "summarize_form_responses"
            else _safe_json(result_payload)
        )
        _ok(
            message.get("id"),
            {
                "content": [
                    {
                        "type": "text",
                        "text": text_out,
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


def _cli_auth_test() -> None:
    """Verify Microsoft Forms sign-in (opens browser on first run)."""
    out = tool_whoami_forms({})
    print(json.dumps(out, indent=2, ensure_ascii=False))


def _cli_summarize_test(argv: List[str]) -> None:
    """Smoke-test summarize_form_responses against a real form (small page)."""
    import argparse

    parser = argparse.ArgumentParser(description="Call summarize_form_responses with a real form URL.")
    parser.add_argument("--form-url", required=True, help="Full forms.office.com link")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Print only form title, counts, and summary_text (no full JSON or respondent_texts).",
    )
    args = parser.parse_args(argv)
    out = tool_summarize_form_responses(
        {
            "form_url": args.form_url,
            "fetch_all": False,
            "top": args.top,
            "skip": 0,
            "max_responses": 100,
            "max_text_answers_per_question": 50,
        }
    )
    if args.brief:
        print(format_brief_cli_summary(out))
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "auth-test":
        _cli_auth_test()
    elif len(sys.argv) >= 2 and sys.argv[1] == "summarize-test":
        _cli_summarize_test(sys.argv[2:])
    else:
        main()
