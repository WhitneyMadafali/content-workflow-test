#!/usr/bin/env python3
"""
Use Forms MCP summarize on Microsoft Forms URLs found in a Teams channel scan JSON.

Produce the JSON with: tools/teams/scripts/scan-teams-graph.py --include-channel-messages --forms-links-only ...
Each message includes forms_urls[] (see forms_url_extract).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from forms_url_extract import extract_forms_urls_from_html


def _load_server():
    root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("forms_mcp_server", root / "server.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run summarize_form_responses using Forms URLs from a Teams scan JSON export."
    )
    parser.add_argument("teams_json", type=Path, help="Output JSON from scan-teams-graph.py")
    parser.add_argument(
        "--pick",
        type=int,
        default=0,
        help="Which Forms URL to use (0 = first in document order)",
    )
    parser.add_argument(
        "--one-page",
        action="store_true",
        help="Only request a single page of responses (same as fetch_all false).",
    )
    parser.add_argument("--max-responses", dest="max_responses", type=int, default=2000)
    parser.add_argument("--top", type=int, default=200)
    parser.add_argument("--tenant-id", dest="tenant_id", default=None)
    parser.add_argument("--owner-type", dest="owner_type", choices=("user", "group"), default=None)
    parser.add_argument("--owner-id", dest="owner_id", default=None)
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Print only form title, counts, and summary_text (no full JSON).",
    )
    args = parser.parse_args()

    data = json.loads(args.teams_json.read_text(encoding="utf-8"))
    urls: List[str] = []
    _collect_forms_urls(data, urls)
    if not urls:
        blob = json.dumps(data, ensure_ascii=False)
        urls.extend(extract_forms_urls_from_html(blob))

    seen = set()
    ordered: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)

    if not ordered:
        print(
            "No Forms URLs found. Re-scan with a current scan-teams-graph.py "
            "(messages must include forms_urls) or use --forms-links-only.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.pick < 0 or args.pick >= len(ordered):
        print(f"--pick {args.pick} invalid; found {len(ordered)} URL(s).", file=sys.stderr)
        sys.exit(1)

    form_url = ordered[args.pick]
    mod = _load_server()
    payload: Dict[str, Any] = {
        "form_url": form_url,
        "fetch_all": not args.one_page,
        "max_responses": args.max_responses,
        "top": args.top,
        "skip": 0,
    }
    if args.tenant_id:
        payload["tenant_id"] = args.tenant_id
    if args.owner_type:
        payload["owner_type"] = args.owner_type
    if args.owner_id:
        payload["owner_id"] = args.owner_id

    out = mod.tool_summarize_form_responses(payload)
    if args.brief:
        print(mod.format_brief_cli_summary(out))
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
