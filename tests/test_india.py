import pytest

from india import age_days, city_key, classify_location, to_date


@pytest.mark.parametrize("text,india,cities,remote", [
    ("Bangalore, Karnataka", True, ["bengaluru"], False),
    ("Gurgaon / Noida", True, ["delhi-ncr"], False),
    ("Remote - India", True, [], True),
    ("Indianapolis, Indiana", False, [], False),
    ("Remote", False, [], True),
    ("Vizag", True, ["visakhapatnam"], False),
    ("Mumbai, Pune, Hyderabad", True, ["hyderabad", "mumbai", "pune"], False),
])
def test_classify(text, india, cities, remote):
    got = classify_location(text)
    assert (got["india"], got["cities"], got["remote"]) == (india, cities, remote)


def test_city_key_aliases():
    assert city_key("Bangalore") == "bengaluru"
    assert city_key("gurugram") == "delhi-ncr"
    assert city_key("Atlantis") is None


def test_dates():
    from datetime import date
    assert to_date(1761000000000) == "2025-10-20"
    assert to_date("2026-10-20T10:00:00-04:00") == "2026-10-20"
    assert to_date("garbage") is None
    assert age_days("2026-10-01", date(2026, 10, 31)) == 30
