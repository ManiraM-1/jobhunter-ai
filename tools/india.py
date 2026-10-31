"""India location detection and posting-date helpers shared by the search tools."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

CITY_ALIASES = {
    "bengaluru": ["bengaluru", "bangalore"],
    "mumbai": ["mumbai", "navi mumbai", "thane"],
    "delhi-ncr": ["delhi", "new delhi", "ncr", "gurugram", "gurgaon", "noida", "greater noida", "faridabad", "ghaziabad"],
    "hyderabad": ["hyderabad", "secunderabad"],
    "chennai": ["chennai"],
    "pune": ["pune"],
    "kolkata": ["kolkata"],
    "ahmedabad": ["ahmedabad", "gandhinagar"],
    "kochi": ["kochi", "cochin"],
    "thiruvananthapuram": ["thiruvananthapuram", "trivandrum"],
    "jaipur": ["jaipur"],
    "chandigarh": ["chandigarh", "mohali", "panchkula"],
    "coimbatore": ["coimbatore"],
    "indore": ["indore"],
    "vijayawada": ["vijayawada"],
    "visakhapatnam": ["visakhapatnam", "vizag"],
    "mysuru": ["mysuru", "mysore"],
    "mangaluru": ["mangaluru", "mangalore"],
    "bhubaneswar": ["bhubaneswar"],
    "nagpur": ["nagpur"],
    "lucknow": ["lucknow"],
    "surat": ["surat"],
    "vadodara": ["vadodara", "baroda"],
    "goa": ["goa", "panaji"],
    "patna": ["patna"],
}

STATES = [
    "karnataka", "maharashtra", "tamil nadu", "telangana", "haryana", "kerala", "gujarat",
    "uttar pradesh", "west bengal", "andhra pradesh", "rajasthan", "punjab", "odisha",
    "madhya pradesh", "bihar",
]

_ALIAS_TO_CITY = {alias: city for city, aliases in CITY_ALIASES.items() for alias in aliases}
_TERMS = sorted(list(_ALIAS_TO_CITY) + STATES + ["india"], key=len, reverse=True)
_INDIA_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in _TERMS) + r")\b", re.I)
_REMOTE_RE = re.compile(r"\b(remote|work from home|wfh|anywhere)\b", re.I)


def classify_location(*parts: str | None) -> dict:
    text = " | ".join(p for p in parts if p)
    cities = sorted({_ALIAS_TO_CITY[m.lower()] for m in _INDIA_RE.findall(text) if m.lower() in _ALIAS_TO_CITY})
    india = bool(_INDIA_RE.search(text))
    remote = bool(_REMOTE_RE.search(text))
    return {"india": india, "cities": cities, "remote": remote}


def city_key(name: str) -> str | None:
    name = name.strip().lower()
    if name in CITY_ALIASES:
        return name
    return _ALIAS_TO_CITY.get(name)


def to_date(value) -> str | None:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 10**11 else value
            return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()
        text = str(value).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return text
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def age_days(iso: str | None, today: date | None = None) -> int | None:
    if not iso:
        return None
    today = today or date.today()
    try:
        return (today - date.fromisoformat(iso)).days
    except ValueError:
        return None
