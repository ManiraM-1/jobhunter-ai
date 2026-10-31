#!/usr/bin/env python3
"""Fetch a careers page that blocks plain fetchers, after checking robots.txt.

For company sites that return 403 to WebFetch but serve normal browsers. It
sends a browser user agent, refuses if robots.txt disallows the page, and runs
the result through the posting guard so hidden text is stripped and flagged.

Usage:
  python tools/fetch_page.py <url> [--raw]
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import BROWSER_UA, FetchError, configure_stdout, emit, fail, fetch, robots_allows  # noqa: E402
from jd_guard import analyse  # noqa: E402


def public_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast:
            return False
    return True


def main(argv=None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("--raw", action="store_true", help="print cleaned text only, no JSON")
    args = parser.parse_args(argv)

    parts = urlsplit(args.url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        return fail("only plain http(s) URLs are allowed", "BAD_URL")
    if not public_host(parts.hostname):
        return fail("refusing to fetch a private or local address", "BAD_HOST")
    if not robots_allows(args.url, BROWSER_UA):
        return fail("robots.txt disallows this page; open it in your browser and paste the text instead", "ROBOTS_DISALLOW")
    try:
        page = fetch(args.url, browser=True, accept="text/html,application/xhtml+xml")
    except FetchError as exc:
        return fail(str(exc), "FETCH_FAILED")
    result = analyse(page, is_html=True)
    if args.raw:
        print(result["text"])
    else:
        emit({"url": args.url, **result})
    return 0


if __name__ == "__main__":
    sys.exit(main())
