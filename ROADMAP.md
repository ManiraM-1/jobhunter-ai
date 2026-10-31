# Roadmap

JobHunter's direction: **fewer, better applications, and a human on the other end.** Features that help someone find the right role, apply well and reach a real person come first. Features that only increase volume (bulk auto-apply, mass email) are out of scope on purpose.

Pick anything here and comment on the matching issue before starting, so two people don't build the same thing.

## In progress
- **Email drafts.** `/outreach` writes the email as a ready-to-send draft (Gmail Drafts if a Gmail connector is set up, otherwise a file any mail app opens). You always click Send.

## Next
- **Fill the form, you submit.** Open Greenhouse and Lever application forms (most don't need an account) in your own browser, fill them in from your profile and tailored CV, and stop before Submit so you review and send it yourself.
- **Run on a free-tier agent.** Most Indian freshers won't pay for a coding-agent plan. Port the commands so the workflow also runs in an agent with a free tier (for example Gemini CLI). This matters more for reach than any single feature.
- **Internship mode.** Stipend and PPO-focused scoring, plus Internshala paste-in support.
- **Offer comparison.** Turn `/outcome` offer breakdowns into a side-by-side comparison with in-hand estimates under the new tax regime.
- **New job sources** with public, documented feeds. Investigate SmartRecruiters, Workable and Keka career-page APIs.

## Good first issues
- **Grow the company list.** Use `discover` to add 10+ Indian companies (fintech, SaaS, AI, consumer) to `data/companies.toml`.
- **More cities.** Extend `tools/india.py` with tier-2 cities and their common spellings.
- **More scam patterns.** Add real-world fake-job wording to `tools/jd_guard.py`, with a test per pattern. Use anonymised examples.
- **CV template variants.** An "experienced" template (3+ years) alongside the fresher one.

## Later
- **Telugu / Hindi output** for outreach drafts, when the user asks.
- A GitHub Action that runs `ats_search.py check` weekly and opens an issue for boards that moved.
- An opt-in, anonymised funnel benchmark (applied → OA → interview → offer by company type).

## Not planned
- **Scraping LinkedIn or other sites behind a login** for profiles or emails. It breaks their terms and puts users' own accounts at risk.
- **Bulk auto-apply or bulk sending.** It hurts response rates, annoys recruiters and gets inboxes flagged as spam.
