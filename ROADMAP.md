# Roadmap

Pick anything here and comment on the matching issue before starting, so two people don't build the same thing.

## Good first issues
- **Grow the company list.** Use `discover` to add 10+ Indian companies (fintech, SaaS, AI, consumer) to `data/companies.toml`.
- **More cities.** Extend `tools/india.py` with tier-2 cities and their common spellings.
- **More scam patterns.** Add real-world fake-job wording to `tools/jd_guard.py`, with a test per pattern. Use anonymised examples.
- **CV template variants.** A two-column-free "experienced" template (3+ years) alongside the fresher one.

## Next
- **New job sources** with public, documented feeds. Investigate SmartRecruiters, Workable and Keka public career-page APIs.
- **Internship mode.** Stipend and PPO-focused scoring, plus Internshala paste-in support.
- **Telugu / Hindi output** for outreach drafts, when the user asks.
- **Offer comparison sheet.** Turn `/outcome` offer breakdowns into a side-by-side comparison with in-hand estimates under the new tax regime.
- **Cross-agent support.** Instructions so the workflow runs in other coding agents, not just Claude Code.

## Later
- A GitHub Action that runs `ats_search.py check` weekly and opens an issue for boards that moved.
- An opt-in, anonymised funnel benchmark (applied → OA → interview → offer by company type).
