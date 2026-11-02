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

    # --- tier-2/3 cities and alternate spellings ---
    ("Madurai, Tamil Nadu", True, ["madurai"], False),
    ("Trichy", True, ["tiruchirappalli"], False),
    ("Warangal, Telangana", True, ["warangal"], False),
    ("Guntur", True, ["guntur"], False),
    ("Nasik", True, ["nashik"], False),
    ("Aurangabad, Maharashtra", True, ["chhatrapati sambhajinagar"], False),
    ("Chhatrapati Sambhajinagar", True, ["chhatrapati sambhajinagar"], False),
    ("Hubli", True, ["hubballi"], False),
    ("Belgaum", True, ["belagavi"], False),
    ("Dehra Dun, Uttarakhand", True, ["dehradun"], False),
    ("Raipur, Chhattisgarh", True, ["raipur"], False),
    ("Ranchi, Jharkhand", True, ["ranchi"], False),
    ("Gauhati", True, ["guwahati"], False),
    ("Trivandrum", True, ["thiruvananthapuram"], False),
    ("Madurai / Trichy", True, ["madurai", "tiruchirappalli"], False),

    # --- must NOT match India ---
    ("Salem, Oregon", False, [], False),
    ("Remote - Salem, Massachusetts", False, [], True),
])
def test_classify(text, india, cities, remote):
    got = classify_location(text)
    assert (got["india"], got["cities"], got["remote"]) == (india, cities, remote)


def test_city_key_aliases():
    assert city_key("Bangalore") == "bengaluru"
    assert city_key("gurugram") == "delhi-ncr"
    assert city_key("Atlantis") is None

    # new
    assert city_key("Trivandrum") == "thiruvananthapuram"
    assert city_key("Aurangabad") == "chhatrapati sambhajinagar"
    assert city_key("Belgaum") == "belagavi"
    assert city_key("Salem") is None  # deliberately ambiguous, not matched


def test_dates():
    from datetime import date
    assert to_date(1761000000000) == "2025-10-20"
    assert to_date("2026-10-20T10:00:00-04:00") == "2026-10-20"
    assert to_date("garbage") is None
    assert age_days("2026-10-01", date(2026, 10, 31)) == 30
