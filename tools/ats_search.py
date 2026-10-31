#!/usr/bin/env python3
"""Search Indian companies' public job boards (Greenhouse, Lever, Ashby).

These boards publish open roles as JSON for anyone to read, so this needs no
login and no scraping. The companies searched come from data/companies.toml.

Usage:
  python tools/ats_search.py search --keywords "backend,sde,software engineer" [--exclude "senior,staff,lead"]
         [--city bengaluru --city hyderabad] [--remote] [--days 30] [--company CRED] [--limit 50]
  python tools/ats_search.py detail <posting-url>
  python tools/ats_search.py discover "Company Name" [--slug guess]
  python tools/ats_search.py check

All commands print JSON. Exit 0 on success, 1 on error.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import FetchError, configure_stdout, emit, fail, fetch_json, host_matches  # noqa: E402
from india import age_days, city_key, classify_location, to_date  # noqa: E402
from jd_guard import guarded  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "companies.toml"
ATS_TYPES = ("greenhouse", "lever", "ashby")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,80}$")


def board_url(ats: str, slug: str) -> str:
    if not SLUG_RE.match(slug):
        raise ValueError(f"invalid board slug: {slug!r}")
    if ats == "greenhouse":
        return f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    if ats == "lever":
        return f"https://api.lever.co/v0/postings/{slug}?mode=json"
    if ats == "ashby":
        return f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    raise ValueError(f"unknown ats: {ats}")


def load_registry(path: Path = REGISTRY) -> list[dict]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    companies = data.get("company", [])
    for entry in companies:
        if entry.get("ats") not in ATS_TYPES or not SLUG_RE.match(str(entry.get("slug", ""))):
            raise ValueError(f"bad registry entry: {entry}")
    return companies


def normalize_greenhouse(raw: dict, company: str) -> dict:
    location = (raw.get("location") or {}).get("name") or ""
    description, guard = guarded(html.unescape(raw["content"]) if raw.get("content") else None, is_html=True)
    return {
        "source": "greenhouse",
        "company": company or raw.get("company_name") or "",
        "title": (raw.get("title") or "").strip(),
        "location": location,
        "url": raw.get("absolute_url") or "",
        "id": str(raw.get("id") or ""),
        "posted": to_date(raw.get("first_published") or raw.get("updated_at")),
        "deadline": to_date(raw.get("application_deadline")),
        "team": ((raw.get("departments") or [{}])[0] or {}).get("name"),
        "employment_type": None,
        "workplace": None,
        "description": description,
        "guard": guard,
        "compensation": None,
        **classify_location(location),
    }


def normalize_lever(raw: dict, company: str) -> dict:
    cats = raw.get("categories") or {}
    locations = [cats.get("location") or ""] + list(cats.get("allLocations") or [])
    location = ", ".join(dict.fromkeys(l for l in locations if l))
    parts = [html.escape(raw.get("descriptionPlain") or "")]
    for block in raw.get("lists") or []:
        parts.append(f"<h3>{html.escape(block.get('text') or '')}</h3><ul>{block.get('content') or ''}</ul>")
    parts.append(html.escape(raw.get("additionalPlain") or ""))
    markup = "".join(f"<div>{p}</div>" for p in parts if p.strip())
    description, guard = guarded(markup, is_html=True)
    salary = raw.get("salaryRange") or None
    return {
        "source": "lever",
        "company": company,
        "title": (raw.get("text") or "").strip(),
        "location": location,
        "url": raw.get("hostedUrl") or "",
        "id": str(raw.get("id") or ""),
        "posted": to_date(raw.get("createdAt")),
        "team": cats.get("team") or cats.get("department"),
        "employment_type": cats.get("commitment"),
        "workplace": raw.get("workplaceType"),
        "description": description,
        "guard": guard,
        "compensation": salary,
        **classify_location(location, raw.get("country")),
    }


def normalize_ashby(raw: dict, company: str) -> dict:
    locs = [raw.get("location") or ""] + [
        (s.get("location") if isinstance(s, dict) else str(s)) or "" for s in raw.get("secondaryLocations") or []
    ]
    address = ((raw.get("address") or {}).get("postalAddress") or {})
    location = ", ".join(dict.fromkeys(l for l in locs if l))
    comp = raw.get("compensation") or {}
    info = classify_location(location, address.get("addressCountry"), address.get("addressLocality"))
    if raw.get("isRemote"):
        info["remote"] = True
    if raw.get("descriptionHtml"):
        description, guard = guarded(raw["descriptionHtml"], is_html=True)
    else:
        description, guard = guarded(raw.get("descriptionPlain"), is_html=False)
    return {
        "source": "ashby",
        "company": company,
        "title": (raw.get("title") or "").strip(),
        "location": location,
        "url": raw.get("jobUrl") or "",
        "id": str(raw.get("id") or ""),
        "posted": to_date(raw.get("publishedAt")),
        "team": raw.get("team") or raw.get("department"),
        "employment_type": raw.get("employmentType"),
        "workplace": raw.get("workplaceType"),
        "description": description,
        "guard": guard,
        "compensation": comp.get("compensationTierSummary") or comp.get("scrapeableCompensationSalarySummary"),
        **info,
    }


def fetch_board(ats: str, slug: str, company: str = "") -> list[dict]:
    data = fetch_json(board_url(ats, slug))
    if ats == "greenhouse":
        return [normalize_greenhouse(j, company) for j in (data or {}).get("jobs", [])]
    if ats == "lever":
        if not isinstance(data, list):
            raise FetchError(f"unexpected Lever response for {slug}")
        return [normalize_lever(j, company) for j in data]
    jobs = (data or {}).get("jobs", [])
    return [normalize_ashby(j, company) for j in jobs if j.get("isListed", True)]


def _split(values: list[str] | None) -> list[str]:
    out: list[str] = []
    for value in values or []:
        out.extend(v.strip().lower() for v in value.split(",") if v.strip())
    return out


def _word_match(term: str, text: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None


def filter_jobs(jobs, *, keywords=(), exclude=(), cities=(), remote=False, days=None, india_only=True):
    kept = []
    for job in jobs:
        title = job["title"].lower()
        if keywords and not any(_word_match(k, title) for k in keywords):
            continue
        if exclude and any(_word_match(x, title) for x in exclude):
            continue
        if india_only and not job["india"]:
            continue
        if cities and not (set(job["cities"]) & set(cities)) and not (remote and job["remote"]):
            continue
        if days is not None:
            age = age_days(job["posted"])
            if age is not None and age > days:
                continue
        kept.append(job)
    return kept


def cmd_search(args) -> int:
    companies = load_registry(Path(args.registry))
    if args.company:
        wanted = {c.lower() for c in _split(args.company)}
        companies = [c for c in companies if c["name"].lower() in wanted]
        if not companies:
            return fail("none of --company matched data/companies.toml", "NO_COMPANY")
    cities = []
    for raw in _split(args.city):
        key = city_key(raw)
        if not key:
            return fail(f"unknown Indian city: {raw}", "BAD_CITY")
        cities.append(key)

    errors, results = [], []

    def run(entry):
        try:
            return fetch_board(entry["ats"], entry["slug"], entry["name"]), None
        except (FetchError, ValueError) as exc:
            return [], {"company": entry["name"], "error": str(exc)}

    with ThreadPoolExecutor(max_workers=6) as pool:
        for jobs, err in pool.map(run, companies):
            if err:
                errors.append(err)
            results.extend(jobs)

    matched = filter_jobs(
        results,
        keywords=_split(args.keywords),
        exclude=_split(args.exclude),
        cities=cities,
        remote=args.remote,
        days=args.days,
        india_only=not args.anywhere,
    )
    matched.sort(key=lambda j: j["posted"] or "", reverse=True)
    if args.limit:
        matched = matched[: args.limit]
    if not args.with_description:
        for job in matched:
            job.pop("description", None)
            job.pop("guard", None)
    emit({
        "meta": {"companies_searched": len(companies), "postings_scanned": len(results), "matched": len(matched), "errors": errors},
        "results": matched,
    })
    return 0


def parse_posting_url(url: str) -> tuple[str, str, str] | None:
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https"):
        return None
    host, segs = parts.hostname or "", [s for s in parts.path.split("/") if s]
    if host_matches(host, "greenhouse.io") and len(segs) >= 3 and segs[1] == "jobs" and segs[2].isdigit():
        return "greenhouse", segs[0].lower(), segs[2]
    if host_matches(host, "lever.co") and host.startswith("jobs.") and len(segs) >= 2:
        return "lever", segs[0].lower(), segs[1]
    if host_matches(host, "ashbyhq.com") and host.startswith("jobs.") and len(segs) >= 2:
        return "ashby", segs[0].lower(), segs[1]
    return None


def cmd_detail(args) -> int:
    parsed = parse_posting_url(args.url)
    if not parsed:
        return fail("not a Greenhouse, Lever or Ashby posting URL", "BAD_URL")
    ats, slug, job_id = parsed
    if not SLUG_RE.match(slug) or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", job_id):
        return fail("posting URL has an unexpected board or job id", "BAD_URL")
    try:
        known = {(c["ats"], c["slug"]): c["name"] for c in load_registry(Path(args.registry))}
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        known = {}
    name = known.get((ats, slug), slug)
    try:
        if ats == "greenhouse":
            raw = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}")
            job = normalize_greenhouse(raw, known.get((ats, slug)) or raw.get("company_name") or slug)
        elif ats == "lever":
            raw = fetch_json(f"https://api.lever.co/v0/postings/{slug}/{quote(job_id)}?mode=json")
            job = normalize_lever(raw, name)
        else:
            jobs = [j for j in fetch_board("ashby", slug, name) if j["id"] == job_id]
            if not jobs:
                return fail("posting not found on the board (closed or unlisted)", "NOT_FOUND")
            job = jobs[0]
    except FetchError as exc:
        if exc.status == 404:
            return fail("posting not found (likely closed)", "NOT_FOUND")
        return fail(str(exc), "FETCH_FAILED")
    emit(job)
    return 0


def slug_candidates(name: str) -> list[str]:
    base = re.sub(r"[^a-z0-9 ]", "", name.lower()).split()
    noise = {"technologies", "technology", "tech", "labs", "india", "private", "pvt", "ltd", "limited", "inc", "software", "solutions"}
    core = [w for w in base if w not in noise] or base
    cands = ["".join(base), "-".join(base), "".join(core), "-".join(core), core[0] if core else ""]
    cands += ["".join(core) + "hq", "".join(core) + "india", "".join(core) + "tech", "".join(core) + "labs"]
    return [c for c in dict.fromkeys(cands) if c and SLUG_RE.match(c)]


def probe(ats: str, slug: str) -> dict | None:
    try:
        jobs = fetch_board(ats, slug, slug)
    except (FetchError, ValueError):
        return None
    india = sum(1 for j in jobs if j["india"])
    return {"ats": ats, "slug": slug, "open_roles": len(jobs), "india_roles": india}


def cmd_discover(args) -> int:
    slugs = [args.slug.lower()] if args.slug else slug_candidates(args.name)
    tasks = [(ats, s) for s in slugs for ats in ATS_TYPES]
    with ThreadPoolExecutor(max_workers=6) as pool:
        hits = [h for h in pool.map(lambda t: probe(*t), tasks) if h]
    hits.sort(key=lambda h: (h["india_roles"], h["open_roles"]), reverse=True)
    snippet = None
    if hits:
        best = hits[0]
        snippet = (
            f'[[company]]\nname = "{args.name}"\nats = "{best["ats"]}"\nslug = "{best["slug"]}"\n'
            f'sector = ""\nverified = "{__import__("datetime").date.today().isoformat()}"'
        )
    emit({"company": args.name, "tried": slugs, "boards_found": hits, "registry_entry": snippet})
    return 0


def cmd_check(args) -> int:
    companies = load_registry(Path(args.registry))
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda c: (c, probe(c["ats"], c["slug"])), companies))
    report = []
    for entry, hit in rows:
        status = "ok" if hit and hit["india_roles"] else ("no_india_roles" if hit else "board_unreachable")
        report.append({"company": entry["name"], "ats": entry["ats"], "slug": entry["slug"], "status": status,
                       "open_roles": hit["open_roles"] if hit else None, "india_roles": hit["india_roles"] if hit else None})
    emit({"checked": len(report), "results": report})
    return 0 if all(r["status"] != "board_unreachable" for r in report) else 1


def main(argv=None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--registry", default=str(REGISTRY))
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("search", help="search every company in the registry")
    s.add_argument("--keywords", action="append", help="title must contain one of these (comma-separated)")
    s.add_argument("--exclude", action="append", help="drop titles containing any of these (comma-separated)")
    s.add_argument("--city", action="append", help="keep roles in these Indian cities (repeatable)")
    s.add_argument("--remote", action="store_true", help="with --city, also keep remote India roles")
    s.add_argument("--days", type=int, help="only roles posted in the last N days")
    s.add_argument("--company", action="append", help="limit to these registry companies")
    s.add_argument("--anywhere", action="store_true", help="include roles outside India")
    s.add_argument("--limit", type=int)
    s.add_argument("--with-description", action="store_true")
    s.set_defaults(func=cmd_search)

    d = sub.add_parser("detail", help="full posting for one Greenhouse/Lever/Ashby URL")
    d.add_argument("url")
    d.set_defaults(func=cmd_detail)

    disc = sub.add_parser("discover", help="find which public board a company uses")
    disc.add_argument("name")
    disc.add_argument("--slug", help="try this board name instead of guessing")
    disc.set_defaults(func=cmd_discover)

    c = sub.add_parser("check", help="re-verify every registry entry")
    c.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, tomllib.TOMLDecodeError, OSError) as exc:
        return fail(str(exc), "ERROR")


if __name__ == "__main__":
    sys.exit(main())
