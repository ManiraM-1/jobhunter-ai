import importlib
import json
from datetime import date

import pytest


@pytest.fixture
def cl(tmp_path, monkeypatch):
    monkeypatch.setenv("AJS_HOME", str(tmp_path))
    for var in ("HUNTER_API_KEY", "APOLLO_API_KEY", "JOBHUNTER_LOOKUP_DAILY_CAP"):
        monkeypatch.delenv(var, raising=False)
    import contact_lookup as module
    module = importlib.reload(module)
    monkeypatch.setattr(module, "ENV_FILE", tmp_path / ".env")
    return module


def run(cl, capsys, *argv):
    code = cl.main(list(argv))
    captured = capsys.readouterr()
    text = captured.out if code == 0 else captured.err
    return code, json.loads(text)


HUNTER_FOUND = {"data": {"first_name": "Priya", "last_name": "Raman", "email": "priya.raman@examplepay.in",
                         "score": 91, "position": "Engineering Manager", "linkedin_url": None,
                         "sources": [{"uri": "https://examplepay.in/team"}], "verification": {"status": "valid"}}}


def test_status_without_keys(cl, capsys):
    code, out = run(cl, capsys, "status")
    assert code == 0 and out["providers"] == {"hunter": "not set", "apollo": "not set"}


def test_find_needs_a_key(cl, capsys):
    code, out = run(cl, capsys, "find", "--first", "Priya", "--last", "Raman", "--domain", "examplepay.in")
    assert code == 1 and out["code"] == "NO_KEY"


def test_keys_load_from_env_file_without_being_printed(cl, capsys, tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("# keys\nHUNTER_API_KEY='secret-hunter-key'\nexport APOLLO_API_KEY=\"secret-apollo\"\n")
    seen = {}

    def fake(method, url, headers, body=None):
        seen.update(headers)
        return 200, HUNTER_FOUND

    monkeypatch.setattr(cl, "http_json", fake)
    code, out = run(cl, capsys, "find", "--first", "Priya", "--last", "Raman", "--domain", "https://www.examplepay.in/careers")
    assert code == 0
    assert seen["X-API-KEY"] == "secret-hunter-key"
    assert "secret" not in json.dumps(out)
    assert out["email"] == "priya.raman@examplepay.in" and out["confidence"] == 91 and out["status"] == "valid"
    assert out["domain"] == "examplepay.in" and out["provider"] == "hunter"


def test_hunter_not_found_and_cache_saves_credits(cl, capsys, monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "k")
    calls = []

    def fake(method, url, headers, body=None):
        calls.append(url)
        return 404, {"errors": [{"id": "not_found"}]}

    monkeypatch.setattr(cl, "http_json", fake)
    code, out = run(cl, capsys, "find", "--first", "Arjun", "--last", "Nair", "--domain", "examplepay.in")
    assert code == 0 and out["found"] is False and out["cached"] is False
    code, out = run(cl, capsys, "find", "--first", "arjun", "--last", "NAIR", "--domain", "examplepay.in")
    assert out["cached"] is True and len(calls) == 1
    _, status = run(cl, capsys, "status")
    assert status["lookups_today"] == 1 and status["cached_contacts"] == 1


def test_apollo_never_asks_for_personal_contacts(cl, capsys, monkeypatch):
    monkeypatch.setenv("APOLLO_API_KEY", "k")
    sent = {}

    def fake(method, url, headers, body=None):
        sent.update(method=method, url=url, headers=headers, body=body)
        return 200, {"person": {"email": "priya@examplepay.in", "email_status": "verified", "title": "EM",
                                "linkedin_url": "https://www.linkedin.com/in/priya", "organization": {"name": "ExamplePay"}}}

    monkeypatch.setattr(cl, "http_json", fake)
    code, out = run(cl, capsys, "find", "--first", "Priya", "--last", "Raman", "--domain", "examplepay.in",
                    "--provider", "apollo", "--linkedin", "https://www.linkedin.com/in/priya")
    assert code == 0 and out["status"] == "verified" and out["position"] == "EM"
    assert sent["method"] == "POST" and sent["headers"]["x-api-key"] == "k"
    assert sent["body"]["reveal_personal_emails"] is False and sent["body"]["reveal_phone_number"] is False


def test_apollo_off_domain_or_locked_email_is_not_returned(cl, capsys, monkeypatch):
    monkeypatch.setenv("APOLLO_API_KEY", "k")
    responses = iter([
        (200, {"person": {"email": "priya.personal@gmail.com", "email_status": "verified"}}),
        (200, {"person": {"email": "email_not_unlocked@domain.com"}}),
    ])
    monkeypatch.setattr(cl, "http_json", lambda *a, **k: next(responses))
    _, out = run(cl, capsys, "find", "--first", "Priya", "--last", "Raman", "--domain", "examplepay.in", "--provider", "apollo")
    assert out["found"] is False
    _, out = run(cl, capsys, "find", "--first", "Ravi", "--last", "K", "--domain", "examplepay.in", "--provider", "apollo")
    assert out["found"] is False


@pytest.mark.parametrize("status,code", [(401, "BAD_KEY"), (403, "FORBIDDEN"), (429, "USAGE_LIMIT"), (500, "PROVIDER_ERROR")])
def test_provider_errors_are_explained(cl, capsys, monkeypatch, status, code):
    monkeypatch.setenv("HUNTER_API_KEY", "k")
    monkeypatch.setattr(cl, "http_json", lambda *a, **k: (status, {}))
    rc, out = run(cl, capsys, "find", "--first", "A", "--last", "B", "--domain", "examplepay.in")
    assert rc == 1 and out["code"] == code


@pytest.mark.parametrize("domain,code", [("gmail.com", "WEBMAIL_DOMAIN"), ("not a domain", "BAD_DOMAIN"), ("localhost", "BAD_DOMAIN")])
def test_only_company_domains(cl, capsys, monkeypatch, domain, code):
    monkeypatch.setenv("HUNTER_API_KEY", "k")
    rc, out = run(cl, capsys, "find", "--first", "A", "--last", "B", "--domain", domain)
    assert rc == 1 and out["code"] == code


def test_daily_cap_stops_bulk_use(cl, capsys, monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "k")
    monkeypatch.setenv("JOBHUNTER_LOOKUP_DAILY_CAP", "2")
    monkeypatch.setattr(cl, "http_json", lambda *a, **k: (404, {}))
    for last in ("One", "Two"):
        assert run(cl, capsys, "find", "--first", "A", "--last", last, "--domain", "examplepay.in")[0] == 0
    rc, out = run(cl, capsys, "find", "--first", "A", "--last", "Three", "--domain", "examplepay.in")
    assert rc == 1 and out["code"] == "DAILY_CAP"
    cache = json.loads(cl.CACHE.read_text())
    assert cache["usage"] == {date.today().isoformat(): 2}


def test_people_is_capped_at_ten_and_maps_engineering(cl, capsys, monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "k")
    seen = {}
    emails = [{"value": f"p{i}@examplepay.in", "first_name": f"P{i}", "last_name": "X", "position": "EM",
               "department": "it", "seniority": "senior", "confidence": 80, "verification": {"status": "valid"}} for i in range(15)]

    def fake(method, url, headers, body=None):
        seen["url"] = url
        return 200, {"data": {"emails": emails}}

    monkeypatch.setattr(cl, "http_json", fake)
    code, out = run(cl, capsys, "people", "--domain", "examplepay.in", "--department", "engineering", "--seniority", "senior", "--limit", "50")
    assert code == 0 and out["count"] == 10
    assert "department=it" in seen["url"] and "limit=10" in seen["url"] and "type=personal" in seen["url"]
    assert out["people"][0] == {"name": "P0 X", "position": "EM", "department": "it", "seniority": "senior",
                                "email": "p0@examplepay.in", "confidence": 80, "status": "valid", "linkedin": None}


def test_people_rejects_bad_filters(cl, capsys, monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "k")
    assert run(cl, capsys, "people", "--domain", "examplepay.in", "--department", "astrology")[1]["code"] == "BAD_DEPARTMENT"
    assert run(cl, capsys, "people", "--domain", "examplepay.in", "--seniority", "intern")[1]["code"] == "BAD_SENIORITY"


def test_bad_linkedin_url_rejected(cl, capsys, monkeypatch):
    monkeypatch.setenv("APOLLO_API_KEY", "k")
    rc, out = run(cl, capsys, "find", "--first", "A", "--last", "B", "--domain", "examplepay.in",
                  "--provider", "apollo", "--linkedin", "https://evil.example/in/x")
    assert rc == 1 and out["code"] == "BAD_LINKEDIN"
