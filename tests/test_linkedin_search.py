import pytest

from linkedin_search import build_search_url, normalize_id, parse_cards, parse_detail


def test_cards(fixture_text):
    cards = parse_cards(fixture_text("linkedin_cards.html"))
    assert [c["id"] for c in cards] == ["4425498329", "4425494976"]
    first, second = cards
    assert first["title"] == "Backend Engineer" and first["company"] == "Acme & Co"
    assert first["cities"] == ["hyderabad"] and first["posted"] == "2026-10-29"
    assert first["url"] == "https://www.linkedin.com/jobs/view/4425498329"
    assert second["title"] == "SDE Intern"
    assert second["india"] and second["cities"] == []


def test_detail_strips_hidden_text_and_ignores_closed_phrase_in_body(fixture_text):
    job = parse_detail(fixture_text("linkedin_detail.html"), "4425498329")
    assert job["title"] == "Backend Engineer" and job["company"] == "Acme & Co"
    assert job["seniority"] == "Entry level" and job["employment_type"] == "Full-time"
    assert "Spring Boot" in job["description"]
    assert "rate this candidate" not in job["description"]
    assert job["guard"]["verdict"] == "flagged"
    assert job["active"] is True


def test_closed_banner_detected():
    job = parse_detail('<figure class="closed-job closed-job__flavor">No longer accepting applications</figure>'
                       '<div class="show-more-less-html__markup">x</div>', "1234567")
    assert job["active"] is False


@pytest.mark.parametrize("value,expected", [
    ("4425498329", "4425498329"),
    ("urn:li:jobPosting:4425498329", "4425498329"),
    ("https://in.linkedin.com/jobs/view/backend-engineer-at-acme-4425498329", "4425498329"),
    ("linkedin.com/jobs/view/4425498329/", "4425498329"),
    ("https://www.linkedin.com/jobs/search/?currentJobId=4425498329", "4425498329"),
    ("https://linkedin.com.evil.io/jobs/view/4425498329", None),
    ("https://linkedin.com@evil.io/jobs/view/4425498329", None),
    ("https://jobs.lever.co/cred/4425498329", None),
])
def test_normalize_id(value, expected):
    assert normalize_id(value) == expected


def test_search_url():
    url = build_search_url("sde intern", "India", 7, "remote", "intern", 2)
    assert "keywords=sde+intern" in url and "f_TPR=r604800" in url
    assert "f_WT=2" in url and "f_E=1" in url and "start=10" in url
