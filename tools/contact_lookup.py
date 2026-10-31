#!/usr/bin/env python3
"""Find one person's work email at a company, with your own Hunter or Apollo API key.

Built for one thing: reaching the hiring manager, recruiter or founder for a
role you are applying to. It is deliberately not a bulk tool:

  * `find` looks up exactly one person per call
  * `people` lists at most 10 people at one company per call
  * work emails only: personal addresses are never requested, and webmail
    domains (gmail.com and friends) are refused
  * a daily cap on lookups (default 20, set JOBHUNTER_LOOKUP_DAILY_CAP to change)
  * results are cached in applications/contacts.json, so asking twice never
    spends a second credit

Keys come from environment variables or a `.env` file in the repo root:
  HUNTER_API_KEY=...      (hunter.io → API)
  APOLLO_API_KEY=...      (apollo.io → Settings → API keys)

Usage:
  python tools/contact_lookup.py status
  python tools/contact_lookup.py find --first Priya --last Raman --domain razorpay.com [--provider hunter|apollo]
                                      [--linkedin https://www.linkedin.com/in/...]
  python tools/contact_lookup.py people --domain razorpay.com [--department engineering] [--seniority senior,executive] [--limit 5]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import USER_AGENT, configure_stdout, emit, fail  # noqa: E402
from state import atomic_write  # noqa: E402

ROOT = Path(os.environ.get("AJS_HOME") or Path(__file__).resolve().parent.parent)
CACHE = ROOT / "applications" / "contacts.json"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
DEFAULT_DAILY_CAP = 20
TIMEOUT = 25

HUNTER_FINDER = "https://api.hunter.io/v2/email-finder"
HUNTER_DOMAIN = "https://api.hunter.io/v2/domain-search"
APOLLO_MATCH = "https://api.apollo.io/api/v1/people/match"

WEBMAIL = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "outlook.com", "hotmail.com", "live.com",
    "rediffmail.com", "icloud.com", "proton.me", "protonmail.com", "aol.com", "zoho.com", "ymail.com",
}
DOMAIN_RE = re.compile(r"^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
NAME_RE = re.compile(r"^[^\d@<>/\\:;\"'{}\[\]]{1,60}$")
HUNTER_DEPARTMENTS = {"executive", "it", "finance", "management", "sales", "legal", "support", "hr",
                      "marketing", "communication", "education", "design", "health", "operations"}
HUNTER_SENIORITY = {"junior", "senior", "executive"}


class LookupError_(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def load_env(path: Path | None = None) -> None:
    path = path or ENV_FILE
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def keys() -> dict:
    return {"hunter": os.environ.get("HUNTER_API_KEY", "").strip(), "apollo": os.environ.get("APOLLO_API_KEY", "").strip()}


def clean_domain(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"^[a-z]+://", "", value).split("/")[0].lstrip("@")
    value = value.removeprefix("www.")
    if not DOMAIN_RE.match(value):
        raise LookupError_(f"'{value}' is not a company domain like razorpay.com", "BAD_DOMAIN")
    if value in WEBMAIL:
        raise LookupError_(f"{value} is a personal-email provider; give the company's own domain", "WEBMAIL_DOMAIN")
    return value


def clean_name(value: str, field: str) -> str:
    value = (value or "").strip()
    if not NAME_RE.match(value):
        raise LookupError_(f"--{field} doesn't look like a name", "BAD_NAME")
    return value


def http_json(method: str, url: str, headers: dict, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, method=method, headers={"User-Agent": USER_AGENT, "Accept": "application/json", **headers})
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8") or "{}")
        except (ValueError, OSError):
            payload = {}
        return exc.code, payload
    except (URLError, TimeoutError, ConnectionError) as exc:
        raise LookupError_(f"network error: {exc}", "NETWORK") from exc


def raise_for(provider: str, status: int) -> None:
    if status == 401:
        raise LookupError_(f"{provider} rejected the API key; check {provider.upper()}_API_KEY in .env", "BAD_KEY")
    if status == 403:
        raise LookupError_(f"{provider} refused the request (rate limit, or your plan has no API access)", "FORBIDDEN")
    if status == 429:
        raise LookupError_(f"{provider} usage limit reached for your plan", "USAGE_LIMIT")
    if status >= 400 and status != 404:
        raise LookupError_(f"{provider} returned HTTP {status}", "PROVIDER_ERROR")


def hunter_find(first: str, last: str, domain: str, key: str) -> dict:
    url = f"{HUNTER_FINDER}?{urlencode({'domain': domain, 'first_name': first, 'last_name': last})}"
    status, payload = http_json("GET", url, {"X-API-KEY": key})
    raise_for("hunter", status)
    data = payload.get("data") or {}
    if status == 404 or not data.get("email"):
        return {"found": False}
    score = data.get("score")
    verification = (data.get("verification") or {}).get("status")
    return {
        "found": True,
        "email": data["email"],
        "confidence": score if isinstance(score, (int, float)) else None,
        "status": verification or ("likely" if (score or 0) >= 70 else "unverified"),
        "position": data.get("position"),
        "linkedin": data.get("linkedin_url"),
        "sources": len(data.get("sources") or []),
    }


def apollo_find(first: str, last: str, domain: str, key: str, linkedin: str | None) -> dict:
    body = {"first_name": first, "last_name": last, "domain": domain,
            "reveal_personal_emails": False, "reveal_phone_number": False}
    if linkedin:
        body["linkedin_url"] = linkedin
    status, payload = http_json("POST", APOLLO_MATCH, {"x-api-key": key, "Content-Type": "application/json",
                                                     "Cache-Control": "no-cache"}, body)
    raise_for("apollo", status)
    person = payload.get("person") or {}
    email = person.get("email") or ""
    if status == 404 or not email or "email_not_unlocked" in email or not email.lower().endswith("@" + domain):
        return {"found": False}
    email_status = person.get("email_status") or "unverified"
    return {
        "found": True,
        "email": email,
        "confidence": None,
        "status": "verified" if email_status == "verified" else email_status,
        "position": person.get("title"),
        "linkedin": person.get("linkedin_url"),
        "sources": None,
    }


def hunter_people(domain: str, key: str, department: str | None, seniority: str | None, limit: int) -> list[dict]:
    params = {"domain": domain, "limit": limit, "type": "personal"}
    if department:
        params["department"] = department
    if seniority:
        params["seniority"] = seniority
    status, payload = http_json("GET", f"{HUNTER_DOMAIN}?{urlencode(params)}", {"X-API-KEY": key})
    raise_for("hunter", status)
    people = []
    for item in ((payload.get("data") or {}).get("emails") or [])[:limit]:
        name = " ".join(x for x in (item.get("first_name"), item.get("last_name")) if x)
        people.append({
            "name": name or None,
            "position": item.get("position"),
            "department": item.get("department"),
            "seniority": item.get("seniority"),
            "email": item.get("value"),
            "confidence": item.get("confidence"),
            "status": (item.get("verification") or {}).get("status"),
            "linkedin": item.get("linkedin"),
        })
    return people


def load_cache() -> dict:
    if not CACHE.exists():
        return {"version": 1, "lookups": {}, "usage": {}}
    try:
        doc = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": 1, "lookups": {}, "usage": {}}
    doc.setdefault("lookups", {})
    doc.setdefault("usage", {})
    return doc


def save_cache(doc: dict) -> None:
    today = date.today().isoformat()
    doc["usage"] = {d: n for d, n in doc["usage"].items() if d == today}
    atomic_write(CACHE, json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def daily_cap() -> int:
    try:
        return max(1, int(os.environ.get("JOBHUNTER_LOOKUP_DAILY_CAP", DEFAULT_DAILY_CAP)))
    except ValueError:
        return DEFAULT_DAILY_CAP


def spend(doc: dict) -> None:
    today = date.today().isoformat()
    used = doc["usage"].get(today, 0)
    if used >= daily_cap():
        raise LookupError_(
            f"daily lookup cap reached ({used}/{daily_cap()}). JobHunter is built for a few targeted contacts a day, "
            "not bulk lookups; raise JOBHUNTER_LOOKUP_DAILY_CAP in .env if you really need more", "DAILY_CAP")
    doc["usage"][today] = used + 1


def pick_provider(requested: str | None) -> tuple[str, str]:
    available = keys()
    if requested:
        if not available[requested]:
            raise LookupError_(f"no {requested.upper()}_API_KEY set; add it to .env", "NO_KEY")
        return requested, available[requested]
    for name in ("hunter", "apollo"):
        if available[name]:
            return name, available[name]
    raise LookupError_("no contact-lookup key set. Add HUNTER_API_KEY or APOLLO_API_KEY to .env (see .env.example)", "NO_KEY")


def cmd_status(args) -> int:
    doc = load_cache()
    k = keys()
    emit({
        "providers": {name: ("configured" if value else "not set") for name, value in k.items()},
        "lookups_today": doc["usage"].get(date.today().isoformat(), 0),
        "daily_cap": daily_cap(),
        "cached_contacts": len(doc["lookups"]),
    })
    return 0


def cmd_find(args) -> int:
    first, last = clean_name(args.first, "first"), clean_name(args.last, "last")
    domain = clean_domain(args.domain)
    linkedin = args.linkedin.strip() if args.linkedin else None
    if linkedin and not re.match(r"^https://([a-z]{2,3}\.)?(www\.)?linkedin\.com/in/[^/?#\s]+/?$", linkedin, re.I):
        raise LookupError_("--linkedin must be a linkedin.com/in/... profile URL", "BAD_LINKEDIN")
    provider, key = pick_provider(args.provider)
    cache_key = f"{provider}|{domain}|{first.lower()} {last.lower()}"
    doc = load_cache()
    if cache_key in doc["lookups"] and not args.refresh:
        emit({**doc["lookups"][cache_key], "cached": True})
        return 0
    spend(doc)
    if provider == "hunter":
        result = hunter_find(first, last, domain, key)
    else:
        result = apollo_find(first, last, domain, key, linkedin)
    record = {"name": f"{first} {last}", "domain": domain, "provider": provider,
              "looked_up": datetime.now().isoformat(timespec="seconds"), **result}
    doc["lookups"][cache_key] = record
    save_cache(doc)
    emit({**record, "cached": False})
    return 0


def cmd_people(args) -> int:
    domain = clean_domain(args.domain)
    dept = (args.department or "").strip().lower() or None
    if dept == "engineering":
        dept = "it"
    if dept and dept not in HUNTER_DEPARTMENTS:
        raise LookupError_(f"--department must be one of: engineering, {', '.join(sorted(HUNTER_DEPARTMENTS))}", "BAD_DEPARTMENT")
    seniority = ",".join(s.strip().lower() for s in (args.seniority or "").split(",") if s.strip()) or None
    if seniority and not set(seniority.split(",")) <= HUNTER_SENIORITY:
        raise LookupError_("--seniority takes junior, senior, executive (comma-separated)", "BAD_SENIORITY")
    if not keys()["hunter"]:
        raise LookupError_("`people` needs HUNTER_API_KEY (Apollo's people search is not used here)", "NO_KEY")
    limit = max(1, min(args.limit, 10))
    doc = load_cache()
    spend(doc)
    people = hunter_people(domain, keys()["hunter"], dept, seniority, limit)
    save_cache(doc)
    emit({"domain": domain, "count": len(people), "people": people})
    return 0


def main(argv=None) -> int:
    configure_stdout()
    load_env()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("status", help="which keys are set, and today's usage"); s.set_defaults(func=cmd_status)
    f = sub.add_parser("find", help="one person's work email")
    f.add_argument("--first", required=True); f.add_argument("--last", required=True); f.add_argument("--domain", required=True)
    f.add_argument("--provider", choices=["hunter", "apollo"]); f.add_argument("--linkedin")
    f.add_argument("--refresh", action="store_true", help="ignore the cache and spend a new lookup")
    f.set_defaults(func=cmd_find)
    p = sub.add_parser("people", help="up to 10 people at one company (Hunter)")
    p.add_argument("--domain", required=True); p.add_argument("--department"); p.add_argument("--seniority")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=cmd_people)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except LookupError_ as exc:
        return fail(str(exc), exc.code)


if __name__ == "__main__":
    sys.exit(main())
