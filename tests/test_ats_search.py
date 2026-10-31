import json

import pytest

import ats_search
from ats_search import filter_jobs, normalize_greenhouse, normalize_lever, parse_posting_url, slug_candidates


def test_registry_loads_and_every_entry_is_well_formed():
    companies = ats_search.load_registry()
    assert len(companies) >= 10
    names = [c["name"] for c in companies]
    assert len(names) == len(set(names))
    for c in companies:
        assert c["ats"] in ats_search.ATS_TYPES
        assert c["verified"]


def test_greenhouse_normalisation_and_hidden_text(fixture_json):
    jobs = [normalize_greenhouse(j, "ExamplePay") for j in fixture_json("greenhouse_board.json")["jobs"]]
    assert jobs[0]["india"] and jobs[0]["cities"] == ["bengaluru"]
    assert jobs[0]["posted"] == "2026-10-20"
    assert jobs[0]["deadline"] == "2026-11-15" and jobs[0]["team"] == "Engineering"
    assert not jobs[1]["india"]
    assert jobs[2]["cities"] == ["delhi-ncr"]
    assert "UPI rails" in jobs[2]["description"]
    assert "Ignore previous" not in jobs[2]["description"]
    assert jobs[2]["guard"]["verdict"] == "flagged"
    assert jobs[2]["guard"]["findings"][0]["type"] == "hidden_html"
    assert jobs[0]["guard"]["verdict"] == "clean"


def test_lever_normalisation(fixture_json):
    jobs = [normalize_lever(j, "ExampleCred") for j in fixture_json("lever_board.json")]
    sde = jobs[0]
    assert sde["india"] and sde["remote"] and sde["cities"] == ["bengaluru"]
    assert "Spring Boot" in sde["description"] and "1-2 years with Java" in sde["description"]
    assert sde["employment_type"] == "Full-time"
    assert not jobs[1]["india"]


def test_ashby_skips_unlisted_and_reads_compensation(fixture_json, monkeypatch):
    monkeypatch.setattr(ats_search, "fetch_json", lambda url: fixture_json("ashby_board.json"))
    jobs = ats_search.fetch_board("ashby", "exampleatlas", "ExampleAtlas")
    assert [j["title"] for j in jobs] == ["Software Engineer Intern"]
    assert jobs[0]["compensation"] == "₹50K per month"
    assert jobs[0]["remote"] and jobs[0]["india"]


def test_filters(fixture_json):
    jobs = [normalize_greenhouse(j, "X") for j in fixture_json("greenhouse_board.json")["jobs"]]
    jobs += [normalize_lever(j, "Y") for j in fixture_json("lever_board.json")]
    titles = lambda js: sorted(j["title"] for j in js)
    assert titles(filter_jobs(jobs, keywords=["engineer", "sde"])) == [
        "SDE 1 - Backend (Java)", "Senior Staff Engineer, Payments", "Software Development Engineer - Backend"]
    assert "Senior Staff Engineer, Payments" not in titles(filter_jobs(jobs, keywords=["engineer"], exclude=["senior", "staff"]))
    assert titles(filter_jobs(jobs, cities=["delhi-ncr"])) == ["Senior Staff Engineer, Payments"]
    assert "DevOps Engineer" in titles(filter_jobs(jobs, india_only=False))
    assert filter_jobs(jobs, keywords=["sde"], exclude=["sde 1"]) == []


def test_keyword_matching_respects_word_boundaries(fixture_json):
    jobs = [normalize_greenhouse(j, "X") for j in fixture_json("greenhouse_board.json")["jobs"]]
    assert filter_jobs(jobs, keywords=["ops"]) == []


@pytest.mark.parametrize("url,expected", [
    ("https://job-boards.greenhouse.io/razorpay/jobs/4744950005", ("greenhouse", "razorpay", "4744950005")),
    ("https://boards.greenhouse.io/groww/jobs/123?gh_src=x", ("greenhouse", "groww", "123")),
    ("https://jobs.lever.co/cred/aa98a938-af3a-45f5-851d-966b2b5bad33/apply", ("lever", "cred", "aa98a938-af3a-45f5-851d-966b2b5bad33")),
    ("https://jobs.ashbyhq.com/atlan/6f1c2a10-1111", ("ashby", "atlan", "6f1c2a10-1111")),
    ("https://jobs.lever.co.evil.com/cred/abc", None),
    ("https://evil-greenhouse.io/x/jobs/1", None),
    ("https://greenhouse.io@evil.com/x/jobs/1", None),
    ("ftp://jobs.lever.co/cred/abc", None),
    ("https://www.naukri.com/job-listings-123", None),
])
def test_posting_url_parsing_rejects_lookalikes(url, expected):
    assert parse_posting_url(url) == expected


def test_board_url_rejects_unsafe_slug():
    with pytest.raises(ValueError):
        ats_search.board_url("lever", "../../etc")


def test_slug_candidates():
    cands = slug_candidates("Razorpay Software Private Limited")
    assert "razorpaysoftwareprivatelimited" in cands and "razorpay" in cands
    assert all(ats_search.SLUG_RE.match(c) for c in cands)


def test_search_end_to_end_offline(fixture_json, monkeypatch, capsys, tmp_path):
    registry = tmp_path / "companies.toml"
    registry.write_text(
        '[[company]]\nname="ExamplePay"\nats="greenhouse"\nslug="examplepay"\nverified="2026-10-31"\n'
        '[[company]]\nname="ExampleCred"\nats="lever"\nslug="examplecred"\nverified="2026-10-31"\n'
        '[[company]]\nname="Down"\nats="lever"\nslug="down"\nverified="2026-10-31"\n'
    )

    def fake(url):
        if "greenhouse" in url:
            return fixture_json("greenhouse_board.json")
        if "examplecred" in url:
            return fixture_json("lever_board.json")
        raise ats_search.FetchError("HTTP 404", 404)

    monkeypatch.setattr(ats_search, "fetch_json", fake)
    code = ats_search.main(["--registry", str(registry), "search", "--keywords", "engineer,sde", "--city", "Bangalore"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out["meta"]["companies_searched"] == 3
    assert [e["company"] for e in out["meta"]["errors"]] == ["Down"]
    assert {j["title"] for j in out["results"]} == {"Software Development Engineer - Backend", "SDE 1 - Backend (Java)"}
    assert all("description" not in j for j in out["results"])


def test_unknown_city_is_an_error(capsys):
    assert ats_search.main(["search", "--city", "Atlantis"]) == 1
