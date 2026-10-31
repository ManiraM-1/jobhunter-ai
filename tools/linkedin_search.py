#!/usr/bin/env python3
"""Search LinkedIn's public (logged-out) job listings for India.

Uses the same guest endpoints a logged-out browser loads, one page of 10 cards
at a time, with backoff on rate limits. It never logs in and never touches your
LinkedIn account.

Usage:
  python tools/linkedin_search.py search --query "backend engineer" [--location "Bengaluru, Karnataka, India"]
         [--days 7] [--mode remote|hybrid|onsite] [--level intern|entry|associate] [--pages 2]
  python tools/linkedin_search.py detail <job-url-or-id>
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from urllib.parse import urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import FetchError, configure_stdout, emit, fail, fetch, host_matches, strip_invisible  # noqa: E402
from india import classify_location  # noqa: E402
from jd_guard import guarded  # noqa: E402

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting"
WORK_TYPE = {"onsite": "1", "on-site": "1", "remote": "2", "hybrid": "3"}
EXPERIENCE = {"intern": "1", "internship": "1", "entry": "2", "associate": "3", "mid": "4", "director": "5"}


def _clean(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return strip_invisible(re.sub(r"\s+", " ", html.unescape(text))).strip()


def build_search_url(query: str, location: str, days: int | None, mode: str | None, level: str | None, page: int) -> str:
    params = {"keywords": query, "location": location, "start": str((page - 1) * 10)}
    if days:
        params["f_TPR"] = f"r{days * 86400}"
    if mode:
        params["f_WT"] = WORK_TYPE[mode]
    if level:
        params["f_E"] = EXPERIENCE[level]
    return f"{SEARCH_URL}?{urlencode(params)}"


def parse_cards(markup: str) -> list[dict]:
    cards = []
    for chunk in markup.split('data-entity-urn="urn:li:jobPosting:')[1:]:
        id_match = re.match(r"(\d+)", chunk)
        if not id_match:
            continue
        job_id = id_match.group(1)
        title_m = re.search(r'class="base-search-card__title"[^>]*>(.*?)</h3>', chunk, re.S | re.I) or re.search(
            r'class="sr-only"[^>]*>(.*?)</span>', chunk, re.S | re.I
        )
        title = _clean(title_m.group(1)) if title_m else ""
        if not title:
            continue
        company_m = re.search(r'class="base-search-card__subtitle"[^>]*>(.*?)</h4>', chunk, re.S | re.I)
        loc_m = re.search(r'class="job-search-card__location"[^>]*>(.*?)</span>', chunk, re.S | re.I)
        date_m = re.search(r'class="job-search-card__listdate[^"]*"[^>]*datetime="([^"]+)"', chunk, re.I)
        location = _clean(loc_m.group(1)) if loc_m else ""
        cards.append({
            "source": "linkedin",
            "company": _clean(company_m.group(1)) if company_m else "",
            "title": title,
            "location": location,
            "url": f"https://www.linkedin.com/jobs/view/{job_id}",
            "id": job_id,
            "posted": date_m.group(1) if date_m else None,
            **classify_location(location),
        })
    return cards


def normalize_id(value: str) -> str | None:
    value = value.strip()
    urn = re.search(r"urn:li:jobPosting:(\d+)", value)
    if urn:
        return urn.group(1)
    if re.fullmatch(r"\d{6,}", value):
        return value
    if not re.match(r"https?://", value, re.I):
        value = "https://" + value
    parts = urlsplit(value)
    if not host_matches(parts.hostname or "", "linkedin.com"):
        return None
    path = re.search(r"/jobs/view/(?:[^/]*-)?(\d{6,})/?$", parts.path)
    if path:
        return path.group(1)
    current = re.search(r"currentJobId=(\d{6,})", parts.query or "")
    return current.group(1) if current else None


def parse_detail(markup: str, job_id: str) -> dict:
    title_m = re.search(r'class="(?:top-card-layout__title|topcard__title)[^"]*"[^>]*>(.*?)</h[12]>', markup, re.S | re.I)
    org_m = re.search(r'class="topcard__org-name-link[^"]*"[^>]*>(.*?)</a>', markup, re.S | re.I)
    loc_m = re.search(r'class="topcard__flavor topcard__flavor--bullet"[^>]*>(.*?)</span>', markup, re.S | re.I)
    desc_start = re.search(r'class="(?:show-more-less-html__markup|description__text)[^"]*"[^>]*>', markup, re.I)
    description, guard = None, {"verdict": "clean", "findings": []}
    if desc_start:
        body = markup[desc_start.end():]
        end = body.find('class="description__job-criteria-list')
        description, guard = guarded(body[: end if end != -1 else len(body)], is_html=True)
    criteria = {
        _clean(k).lower(): _clean(v)
        for k, v in re.findall(
            r'class="description__job-criteria-subheader"[^>]*>(.*?)</h3>.*?class="description__job-criteria-text[^"]*"[^>]*>(.*?)</span>',
            markup, re.S | re.I,
        )
    }
    topcard = markup[: desc_start.start()] if desc_start else markup
    location = _clean(loc_m.group(1)) if loc_m else ""
    return {
        "source": "linkedin",
        "id": job_id,
        "title": _clean(title_m.group(1)) if title_m else "(untitled)",
        "company": _clean(org_m.group(1)) if org_m else "",
        "location": location,
        "url": f"https://www.linkedin.com/jobs/view/{job_id}",
        "seniority": criteria.get("seniority level"),
        "employment_type": criteria.get("employment type"),
        "industries": criteria.get("industries"),
        "active": not re.search(r"closed-job__flavor|no longer accepting applications", topcard, re.I),
        "description": description,
        "guard": guard,
        **classify_location(location),
    }


def cmd_search(args) -> int:
    seen, results = set(), []
    for page in range(1, args.pages + 1):
        try:
            markup = fetch(build_search_url(args.query, args.location, args.days, args.mode, args.level, page), browser=True)
        except FetchError as exc:
            if results:
                break
            return fail(str(exc), "SEARCH_FAILED")
        cards = parse_cards(markup)
        if not cards:
            break
        for card in cards:
            if card["id"] not in seen:
                seen.add(card["id"])
                results.append(card)
    emit({"meta": {"query": args.query, "location": args.location, "count": len(results)}, "results": results})
    return 0


def cmd_detail(args) -> int:
    job_id = normalize_id(args.job)
    if not job_id:
        return fail("could not read a LinkedIn job id from that input", "BAD_ID")
    try:
        markup = fetch(f"{DETAIL_URL}/{job_id}", browser=True)
    except FetchError as exc:
        return fail(str(exc), "NOT_FOUND" if exc.status == 404 else "DETAIL_FAILED")
    emit(parse_detail(markup, job_id))
    return 0


def main(argv=None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("search")
    s.add_argument("--query", required=True)
    s.add_argument("--location", default="India")
    s.add_argument("--days", type=int)
    s.add_argument("--mode", choices=sorted(WORK_TYPE))
    s.add_argument("--level", choices=sorted(EXPERIENCE))
    s.add_argument("--pages", type=int, default=1, choices=range(1, 6))
    s.set_defaults(func=cmd_search)
    d = sub.add_parser("detail")
    d.add_argument("job")
    d.set_defaults(func=cmd_detail)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
