#!/usr/bin/env python3
"""Job history and application tracker, kept out of the AI's context.

Files (both git-ignored, both yours):
  job_scraper/seen_jobs.json   every posting /scrape has shown you, with /rank's scores
  applications/tracker.csv     every application you sent and where it stands

Commands:
  key        --company C --title T                 print the dedup key for a posting
  new        --in search.json                      postings in a search result you have not seen yet
  store      --in search.json                      remember postings (never overwrites existing ones)
  candidates [--limit N] [--all]                   unranked postings for /rank
  record-rank --in scores.json                     save /rank's scores
  shortlist  [--min 60]                            ranked postings, best first
  applied    --company C --role R --url U [--source S] [--folder F] [--ctc TEXT] [--notes TEXT]
  outcome    --company C --role R --status S [--note TEXT] [--next TEXT] [--follow-up YYYY-MM-DD]
  followups  [--stale-days 10]                     applications due a nudge
  tracker                                          print the tracker
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import configure_stdout, emit, fail  # noqa: E402

ROOT = Path(os.environ.get("AJS_HOME") or Path(__file__).resolve().parent.parent)
SEEN = ROOT / "job_scraper" / "seen_jobs.json"
TRACKER = ROOT / "applications" / "tracker.csv"
COLUMNS = ["date_applied", "company", "role", "url", "source", "status", "ctc", "next_step", "follow_up_on", "last_update", "folder", "notes"]
STATUSES = ["applied", "oa", "takehome", "interviewing", "offer", "accepted", "rejected", "ghosted", "withdrawn"]
ACTIVE = {"applied", "oa", "takehome", "interviewing", "offer"}


def slugify(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", folded.lower())).strip("-")


def make_key(company: str, title: str, fallback_id: str = "") -> str:
    c, t = slugify(company), slugify(title)
    raw = f"{(company or '').strip().lower()}|{(title or '').strip().lower()}"
    if not c or not t or len(t) < len(re.sub(r"\W", "", title or "")) // 2:
        digest = hashlib.sha1((raw + "|" + fallback_id).encode()).hexdigest()[:10]
        return f"{c or 'company'}__{(t or 'job')[:40]}-{digest}"
    if len(c) > 40 or len(t) > 60:
        digest = hashlib.sha1(raw.encode()).hexdigest()[:8]
        return f"{c[:40].rstrip('-')}__{t[:60].rstrip('-')}-{digest}"
    return f"{c}__{t}"


def norm_url(url: str) -> str:
    return (url or "").split("?")[0].split("#")[0].rstrip("/").lower()


def load_seen(path: Path = SEEN) -> dict:
    if not path.exists():
        return {"version": 1, "jobs": {}}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
        raise ValueError(f"{path} is not a seen-jobs file")
    return doc


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(tmp, path)


def save_seen(doc: dict, path: Path = SEEN) -> None:
    atomic_write(path, json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def read_results(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("results", [])
    if not isinstance(data, list):
        raise ValueError("expected a JSON array, or an object with a results array")
    return [j for j in data if isinstance(j, dict) and j.get("title") and j.get("company")]


def safe_cell(value) -> str:
    text = "" if value is None else str(value).replace("\r", " ").replace("\n", " ")
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t") else text


def load_tracker(path: Path = TRACKER) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [{c: row.get(c, "") for c in COLUMNS} for row in csv.DictReader(handle)]


def save_tracker(rows: list[dict], path: Path = TRACKER) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix="tracker", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: safe_cell(row.get(c, "")) for c in COLUMNS})
    os.replace(tmp, path)


def applied_pairs(rows: list[dict]) -> set[tuple[str, str]]:
    return {(slugify(r["company"]), slugify(r["role"])) for r in rows}


def cmd_key(args) -> int:
    print(make_key(args.company, args.title, args.id or ""))
    return 0


def split_new(jobs, doc, rows):
    seen_urls = {norm_url(e.get("url", "")) for e in doc["jobs"].values()}
    applied = applied_pairs(rows)
    fresh, counts, batch = [], {"already_seen": 0, "already_applied": 0, "duplicate_in_batch": 0}, set()
    for job in jobs:
        key = make_key(job["company"], job["title"], str(job.get("id", "")))
        url = norm_url(job.get("url", ""))
        if (slugify(job["company"]), slugify(job["title"])) in applied:
            counts["already_applied"] += 1
        elif key in doc["jobs"] or (url and url in seen_urls):
            counts["already_seen"] += 1
        elif key in batch:
            counts["duplicate_in_batch"] += 1
        else:
            batch.add(key)
            fresh.append({**job, "key": key})
    return fresh, counts


def cmd_new(args) -> int:
    fresh, counts = split_new(read_results(args.input), load_seen(), load_tracker())
    emit({"meta": {"new": len(fresh), **counts}, "results": fresh})
    return 0


def cmd_store(args) -> int:
    doc = load_seen()
    fresh, counts = split_new(read_results(args.input), doc, load_tracker())
    today = date.today().isoformat()
    for job in fresh:
        doc["jobs"][job["key"]] = {
            "key": job["key"], "company": job["company"], "title": job["title"], "url": job.get("url", ""),
            "source": job.get("source", ""), "location": job.get("location", ""), "posted": job.get("posted"),
            "first_seen": today, "status": "new",
        }
    save_seen(doc)
    emit({"stored": len(fresh), **counts, "total": len(doc["jobs"])})
    return 0


def cmd_candidates(args) -> int:
    doc = load_seen()
    applied = applied_pairs(load_tracker())
    wanted = {"new", "ranked"} if args.all else {"new"}
    picks = [
        {k: e.get(k) for k in ("key", "company", "title", "url", "source", "location", "posted")}
        for e in doc["jobs"].values()
        if e.get("status") in wanted and (slugify(e["company"]), slugify(e["title"])) not in applied
    ]
    picks.sort(key=lambda e: e.get("posted") or "", reverse=True)
    if args.limit:
        picks = picks[: args.limit]
    emit({"count": len(picks), "candidates": picks})
    return 0


def cmd_record_rank(args) -> int:
    doc = load_seen()
    scores = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if isinstance(scores, dict):
        scores = scores.get("results", [])
    written, missing = 0, []
    for item in scores:
        entry = doc["jobs"].get(item.get("key", ""))
        if not entry:
            missing.append(item.get("key"))
            continue
        score = item.get("score")
        if score is not None and not (isinstance(score, (int, float)) and 0 <= score <= 100):
            missing.append(item.get("key"))
            continue
        verdict = item.get("verdict", "")
        entry.update({
            "score": round(score) if score is not None else None,
            "verdict": verdict,
            "gates": item.get("gates", {}),
            "strengths": item.get("strengths", []),
            "gaps": item.get("gaps", []),
            "ctc": item.get("ctc"),
            "deadline": item.get("deadline"),
            "ranked_at": datetime.now().isoformat(timespec="seconds"),
            "status": "closed" if verdict == "closed" else ("skipped" if verdict in ("weak", "gate_fail") else "ranked"),
        })
        written += 1
    save_seen(doc)
    emit({"written": written, "not_written": missing})
    return 0 if not missing else 1


def cmd_shortlist(args) -> int:
    doc = load_seen()
    rows = [e for e in doc["jobs"].values() if e.get("status") == "ranked" and (e.get("score") or 0) >= args.min]
    rows.sort(key=lambda e: e.get("score") or 0, reverse=True)
    emit({"count": len(rows), "shortlist": [
        {k: e.get(k) for k in ("key", "score", "verdict", "company", "title", "location", "ctc", "deadline", "url", "strengths", "gaps")}
        for e in rows
    ]})
    return 0


def find_row(rows, company, role):
    target = (slugify(company), slugify(role))
    return next((r for r in rows if (slugify(r["company"]), slugify(r["role"])) == target), None)


def cmd_applied(args) -> int:
    rows = load_tracker()
    today = date.today().isoformat()
    if find_row(rows, args.company, args.role):
        return fail("already in the tracker; use `outcome` to update it", "DUPLICATE")
    rows.append({
        "date_applied": today, "company": args.company, "role": args.role, "url": args.url,
        "source": args.source or "", "status": "applied", "ctc": args.ctc or "", "next_step": "",
        "follow_up_on": args.follow_up or "", "last_update": today, "folder": args.folder or "", "notes": args.notes or "",
    })
    save_tracker(rows)
    doc = load_seen()
    key = make_key(args.company, args.role)
    url = norm_url(args.url)
    for entry in doc["jobs"].values():
        if entry["key"] == key or (url and norm_url(entry.get("url", "")) == url):
            entry["status"] = "applied"
    save_seen(doc)
    emit({"recorded": True, "row": rows[-1]})
    return 0


def cmd_outcome(args) -> int:
    rows = load_tracker()
    row = find_row(rows, args.company, args.role)
    if not row:
        return fail("no tracker row for that company and role", "NOT_FOUND")
    if args.status:
        row["status"] = args.status
    if args.next is not None:
        row["next_step"] = args.next
    if args.follow_up is not None:
        row["follow_up_on"] = args.follow_up
    if args.ctc:
        row["ctc"] = args.ctc
    if args.note:
        stamp = date.today().isoformat()
        row["notes"] = f"{row['notes']} | {stamp}: {args.note}".strip(" |")
    row["last_update"] = date.today().isoformat()
    save_tracker(rows)
    emit({"updated": row})
    return 0


def cmd_followups(args) -> int:
    today = date.today()
    due = []
    for row in load_tracker():
        if row["status"] not in ACTIVE:
            continue
        reason = None
        if row["follow_up_on"]:
            try:
                if date.fromisoformat(row["follow_up_on"]) <= today:
                    reason = "follow-up date reached"
            except ValueError:
                pass
        if not reason and row["last_update"]:
            try:
                idle = (today - date.fromisoformat(row["last_update"])).days
                if idle >= args.stale_days:
                    reason = f"no update for {idle} days"
            except ValueError:
                pass
        if reason:
            due.append({**row, "reason": reason})
    emit({"count": len(due), "due": due})
    return 0


def cmd_tracker(args) -> int:
    emit({"rows": load_tracker()})
    return 0


def main(argv=None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    k = sub.add_parser("key"); k.add_argument("--company", required=True); k.add_argument("--title", required=True); k.add_argument("--id")
    k.set_defaults(func=cmd_key)
    for name, func in (("new", cmd_new), ("store", cmd_store), ("record-rank", cmd_record_rank)):
        p = sub.add_parser(name); p.add_argument("--in", dest="input", required=True); p.set_defaults(func=func)
    c = sub.add_parser("candidates"); c.add_argument("--limit", type=int); c.add_argument("--all", action="store_true")
    c.set_defaults(func=cmd_candidates)
    s = sub.add_parser("shortlist"); s.add_argument("--min", type=int, default=60); s.set_defaults(func=cmd_shortlist)
    a = sub.add_parser("applied")
    for flag in ("--company", "--role", "--url"):
        a.add_argument(flag, required=True)
    for flag in ("--source", "--folder", "--ctc", "--notes", "--follow-up"):
        a.add_argument(flag)
    a.set_defaults(func=cmd_applied)
    o = sub.add_parser("outcome")
    o.add_argument("--company", required=True); o.add_argument("--role", required=True)
    o.add_argument("--status", choices=STATUSES); o.add_argument("--note"); o.add_argument("--next")
    o.add_argument("--follow-up"); o.add_argument("--ctc")
    o.set_defaults(func=cmd_outcome)
    f = sub.add_parser("followups"); f.add_argument("--stale-days", type=int, default=10); f.set_defaults(func=cmd_followups)
    t = sub.add_parser("tracker"); t.set_defaults(func=cmd_tracker)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc), "ERROR")


if __name__ == "__main__":
    sys.exit(main())
