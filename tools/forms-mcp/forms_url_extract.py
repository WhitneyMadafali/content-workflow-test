"""
Extract Microsoft Forms URLs from Teams message HTML.

Teams often wraps links in Outlook Safe Links; the real URL is in the ?url= query parameter.
"""

from __future__ import annotations

import html
import re
from typing import List, Optional
from urllib.parse import parse_qs, unquote, urlparse

_FORMS_HOST_RE = re.compile(r"forms\.(?:office|microsoft)\.com", re.IGNORECASE)

_FORMS_URL_RE = re.compile(
    r"(?:https?)://[^\s<>\"']*forms\.(?:office|microsoft)\.com[^\s<>\"']*",
    re.IGNORECASE,
)

_SAFELINKS_RE = re.compile(
    r"https://[^\s<>\"']+safelinks\.protection\.outlook\.com[^\s<>\"']*",
    re.IGNORECASE,
)


def _netloc_host(url: str) -> str:
    try:
        return (urlparse(url).netloc or "").lower()
    except Exception:
        return ""


def extract_forms_urls_from_html(html_content: Optional[str]) -> List[str]:
    if not html_content:
        return []
    raw = html.unescape(html_content)
    out: List[str] = []
    seen = set()

    def add(u: str) -> None:
        u = u.strip().rstrip(".,;)]}\"'")
        if not u or u in seen:
            return
        seen.add(u)
        out.append(u)

    for m in _FORMS_URL_RE.finditer(raw):
        u = m.group(0)
        if "safelinks.protection.outlook.com" in _netloc_host(u):
            continue
        add(u)

    for m in _SAFELINKS_RE.finditer(raw):
        link = m.group(0).strip().rstrip(".,;)]}\"'")
        try:
            parsed = urlparse(link)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            for key in ("url", "originalurl", "u"):
                vals = qs.get(key) or qs.get(key.title())
                if not vals:
                    continue
                candidate = unquote(vals[0])
                if _FORMS_HOST_RE.search(candidate):
                    clean = candidate.split("&", 1)[0]
                    add(clean)
        except Exception:
            continue

    return out
