import csv
import importlib
import json
from datetime import date, timedelta

import pytest


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setenv("AJS_HOME", str(tmp_path))
    import state as module
    return importlib.reload(module)


def run(state, capsys, *argv):
    code = state.main(list(argv))
    out = capsys.readouterr().out
    return code, (json.loads(out) if out.strip().startswith("{") else out.strip())


def write(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


JOBS = {"results": [
    {"company": "CRED", "title": "SDE 1 - Backend", "url": "https://jobs.lever.co/cred/a?lever-source=x", "source": "lever", "posted": "2026-10-28"},
    {"company": "Groww", "title": "Software Engineer", "url": "https://job-boards.greenhouse.io/groww/jobs/1", "source": "greenhouse", "posted": "2026-10-20"},
    {"company": "CRED", "title": "SDE 1 - Backend", "url": "https://www.linkedin.com/jobs/view/999999", "source": "linkedin"},
]}


def test_key_is_stable_and_path_safe(state):
    key = state.make_key("Ops Consulting, LLC", "Penetration Tester / Red Teamer (OT/IoT)")
    assert "/" not in key and "," not in key and key == state.make_key("Ops Consulting, LLC", "Penetration Tester / Red Teamer (OT/IoT)")
    long_a = state.make_key("Acme", "Senior Software Engineer " + "x" * 80 + " A")
    long_b = state.make_key("Acme", "Senior Software Engineer " + "x" * 80 + " B")
    assert long_a != long_b and len(long_a) < 120
    assert state.make_key("सर्वम", "डेवलपर", "1") != state.make_key("सर्वम", "डेवलपर", "2")


def test_store_dedupes_within_and_across_runs(state, tmp_path, capsys):
    path = write(tmp_path, "s.json", JOBS)
    code, out = run(state, capsys, "store", "--in", path)
    assert code == 0 and out["stored"] == 2 and out["duplicate_in_batch"] == 1
    code, out = run(state, capsys, "new", "--in", path)
    assert out["meta"]["new"] == 0 and out["meta"]["already_seen"] == 3


def test_rank_shortlist_and_apply_flow(state, tmp_path, capsys):
    run(state, capsys, "store", "--in", write(tmp_path, "s.json", JOBS))
    _, cands = run(state, capsys, "candidates")
    keys = {c["company"]: c["key"] for c in cands["candidates"]}
    scores = [
        {"key": keys["CRED"], "score": 82, "verdict": "strong", "strengths": ["Java"], "gaps": [], "ctc": "18-24 LPA"},
        {"key": keys["Groww"], "score": 35, "verdict": "weak"},
        {"key": "nope", "score": 50, "verdict": "moderate"},
    ]
    code, out = run(state, capsys, "record-rank", "--in", write(tmp_path, "r.json", scores))
    assert code == 1 and out == {"written": 2, "not_written": ["nope"]}
    _, short = run(state, capsys, "shortlist")
    assert [s["company"] for s in short["shortlist"]] == ["CRED"]
    assert short["shortlist"][0]["ctc"] == "18-24 LPA"

    code, _ = run(state, capsys, "applied", "--company", "CRED", "--role", "SDE 1 - Backend",
                  "--url", "https://jobs.lever.co/cred/a", "--source", "lever", "--notes", "=HYPERLINK(\"x\")")
    assert code == 0
    _, cands = run(state, capsys, "candidates", "--all")
    assert all(c["company"] != "CRED" for c in cands["candidates"])
    assert run(state, capsys, "applied", "--company", "cred", "--role", "SDE 1 - Backend", "--url", "u")[0] == 1

    rows = list(csv.DictReader((tmp_path / "applications" / "tracker.csv").open(encoding="utf-8")))
    assert rows[0]["notes"].startswith("'=")


def test_outcome_and_followups(state, tmp_path, capsys):
    run(state, capsys, "applied", "--company", "Zeta", "--role", "SDE Intern", "--url", "u")
    code, out = run(state, capsys, "outcome", "--company", "zeta", "--role", "sde intern", "--status", "oa",
                    "--note", "HackerRank OA on Sat", "--follow-up", (date.today() - timedelta(days=1)).isoformat())
    assert code == 0 and out["updated"]["status"] == "oa" and "HackerRank" in out["updated"]["notes"]
    _, due = run(state, capsys, "followups")
    assert due["count"] == 1 and due["due"][0]["reason"] == "follow-up date reached"
    run(state, capsys, "outcome", "--company", "Zeta", "--role", "SDE Intern", "--status", "rejected")
    assert run(state, capsys, "followups")[1]["count"] == 0
    assert run(state, capsys, "outcome", "--company", "Nobody", "--role", "x", "--status", "oa")[0] == 1


def test_stale_application_surfaces(state, tmp_path, capsys):
    tracker = tmp_path / "applications" / "tracker.csv"
    old = (date.today() - timedelta(days=15)).isoformat()
    rows = [{c: "" for c in state.COLUMNS} | {"company": "Paytm", "role": "SDE", "status": "applied", "last_update": old, "date_applied": old}]
    state.save_tracker(rows, tracker)
    _, due = run(state, capsys, "followups", "--stale-days", "10")
    assert due["due"][0]["reason"] == "no update for 15 days"


def test_invalid_score_rejected(state, tmp_path, capsys):
    run(state, capsys, "store", "--in", write(tmp_path, "s.json", JOBS))
    _, cands = run(state, capsys, "candidates")
    key = cands["candidates"][0]["key"]
    code, out = run(state, capsys, "record-rank", "--in", write(tmp_path, "r.json", [{"key": key, "score": 140}]))
    assert code == 1 and out["written"] == 0
