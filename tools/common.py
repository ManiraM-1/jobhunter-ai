"""Shared helpers: polite HTTP, robots.txt checks, HTML to text, invisible-text stripping."""

from __future__ import annotations

import html
import json
import random
import re
import sys
import time
import urllib.robotparser
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

USER_AGENT = "jobhunter-ai/1.0 (+https://github.com/ManiraM-1/jobhunter-ai)"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
TIMEOUT = 20
RETRY_STATUSES = {429, 500, 502, 503, 504}

INVISIBLE_CHARS = re.compile(
    "[­͏؜ᅟᅠ឴឵᠋-᠎​-‏"
    "‪-‮⁠-⁯ㅤ︀-️﻿ﾠ\U000e0000-\U000e007f]"
)


class FetchError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def fetch(url: str, *, browser: bool = False, retries: int = 3, accept: str = "*/*") -> str:
    headers = {
        "User-Agent": BROWSER_UA if browser else USER_AGENT,
        "Accept": accept,
        "Accept-Language": "en-IN,en;q=0.9",
    }
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(Request(url, headers=headers), timeout=TIMEOUT) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset, errors="replace")
        except HTTPError as exc:
            last = FetchError(f"HTTP {exc.code} for {url}", exc.code)
            if exc.code not in RETRY_STATUSES:
                raise last from exc
        except (URLError, TimeoutError, ConnectionError) as exc:
            last = FetchError(f"network error for {url}: {exc}")
        if attempt < retries:
            time.sleep(min(8.0, 0.8 * 2**attempt) + random.random() * 0.4)
    raise last or FetchError(f"failed to fetch {url}")


def fetch_json(url: str, **kwargs):
    text = fetch(url, accept="application/json", **kwargs)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise FetchError(f"invalid JSON from {url}: {exc}") from exc


def robots_allows(url: str, agent: str = USER_AGENT) -> bool:
    parts = urlsplit(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    try:
        parser.parse(fetch(robots_url, retries=1).splitlines())
    except FetchError as exc:
        if exc.status in (401, 403):
            return False
        return True
    return parser.can_fetch(agent, url)


def host_matches(host: str, apex: str) -> bool:
    host = (host or "").lower().rstrip(".")
    apex = apex.lower()
    return host == apex or host.endswith("." + apex)


def strip_invisible(text: str) -> str:
    return INVISIBLE_CHARS.sub("", text or "")


_HIDDEN_STYLE = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0(?:px|pt|em|rem)?\s*(?:;|$)|opacity\s*:\s*0(?:\.0+)?\s*(?:;|$)",
    re.I,
)
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
_OPEN_TAG = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)(\s[^>]*)?>")


def _is_hidden(attrs: str) -> bool:
    if not attrs:
        return False
    if re.search(r"(?:^|\s)(hidden|aria-hidden\s*=\s*['\"]?true)", attrs, re.I):
        return True
    style = re.search(r"style\s*=\s*(\"[^\"]*\"|'[^']*')", attrs, re.I)
    return bool(style and _HIDDEN_STYLE.search(style.group(1)))


def remove_hidden_html(markup: str) -> tuple[str, list[str]]:
    """Drop comments, scripts, styles and elements styled invisible. Return (clean, removed snippets)."""
    removed: list[str] = []

    def keep(match: re.Match) -> str:
        snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(0))).strip()
        if snippet:
            removed.append(snippet[:200])
        return " "

    markup = re.sub(r"<!--.*?-->", keep, markup, flags=re.S)
    markup = re.sub(r"<(script|style|noscript|template)\b.*?</\1\s*>", " ", markup, flags=re.S | re.I)

    out: list[str] = []
    pos = 0
    while True:
        m = _OPEN_TAG.search(markup, pos)
        if not m:
            out.append(markup[pos:])
            break
        tag = m.group(1).lower()
        if tag in _VOID or not _is_hidden(m.group(2) or ""):
            out.append(markup[pos : m.end()])
            pos = m.end()
            continue
        out.append(markup[pos : m.start()])
        depth, scan = 1, m.end()
        pair = re.compile(rf"<(/?){tag}\b[^>]*?(/?)>", re.I)
        end = len(markup)
        while depth:
            n = pair.search(markup, scan)
            if not n:
                break
            if n.group(1):
                depth -= 1
            elif not n.group(2):
                depth += 1
            scan = n.end()
            end = n.end()
        snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markup[m.start() : end])).strip()
        if snippet:
            removed.append(snippet[:200])
        pos = end
    return "".join(out), removed


def html_to_text(markup: str) -> str:
    visible, _ = remove_hidden_html(markup or "")
    text = re.sub(r"<\s*br\s*/?>", "\n", visible, flags=re.I)
    text = re.sub(r"<\s*li[^>]*>", "\n- ", text, flags=re.I)
    text = re.sub(r"</\s*(p|div|li|ul|ol|h[1-6]|tr|section)\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = strip_invisible(text)
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def emit(data, fmt: str = "json") -> None:
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)


def fail(message: str, code: str) -> int:
    print(json.dumps({"error": message, "code": code}), file=sys.stderr)
    return 1
