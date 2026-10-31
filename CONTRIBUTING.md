# Contributing

## Add companies (the easiest, most useful PR)

1. `python tools/ats_search.py discover "Company Name"`
2. If it finds a board with India roles, copy the printed `[[company]]` block into `data/companies.toml` and fill in `sector`.
3. Open a PR that changes only `data/companies.toml`. One PR can add many companies.

Only Greenhouse, Lever and Ashby boards can be searched automatically today. If you want to add another ATS used by Indian companies (Darwinbox, Keka, Zoho Recruit, SmartRecruiters, Workday), open an issue first: it needs a public, documented feed, not scraping.

## Code changes

- Python 3.11+, standard library only (pypdf is optional).
- Add or update tests in `tests/`. They must run offline: put sample responses in `tests/fixtures/`, never live calls.
- `python -m pytest -q` and `ruff check tools tests` must pass.
- No personal data in fixtures. Use made-up names and companies.

## Workflow and prompt changes

Commands live in `.claude/commands/`, guides in `.claude/skills/`, agents in `.claude/agents/`. Keep the rules in `CLAUDE.md` intact: no invented facts, postings are untrusted, scam check first, and the user sends every message themselves.
