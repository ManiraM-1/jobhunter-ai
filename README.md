# JobHunter AI 🇮🇳

**An AI job-search assistant for Indian job seekers, built on [Claude Code](https://claude.com/claude-code).** It runs on your machine and keeps your data there.

It finds roles at Indian companies, scores them against your profile, filters out fake jobs, tailors a one-page ATS-safe CV, drafts referral and cold-outreach messages, helps you ship take-home assignments, and preps you for OA, DSA, machine-coding and HR rounds.

> Independent open-source project. Not affiliated with Anthropic.

## What's different for India

| | |
|---|---|
| **Job sources** | Company boards on Greenhouse, Lever and Ashby (official public feeds: no login, no scraping), plus LinkedIn's public listings. A starter list of verified Indian companies ships in `data/companies.toml`; add any company with `/add-company`. |
| **Fake-job filter** | Every posting is checked for the patterns behind Indian job scams: registration or "refundable deposit" fees, laptop purchases, WhatsApp-only HR, "direct joining, no interview", Gmail recruiters. |
| **Eligibility gates** | Batch / graduation year, CGPA and "60% throughout" cut-offs, branch restrictions, backlogs, service bonds, notice period vs "immediate joiner". |
| **Pay in Indian terms** | LPA and ₹/month, always split into fixed, variable, joining bonus and ESOPs, so a padded CTC never looks like salary. Internship stipends and PPO odds scored separately. |
| **Outreach over cover letters** | Indian startups rarely read cover letters, so `/outreach` finds the hiring manager, founder or alumnus and drafts the LinkedIn note, cold email or referral ask. You send it yourself. Cover letters are still there when a form asks. |
| **Rounds Indian companies run** | OA (HackerRank, HackerEarth, Codility), DSA, **machine coding / LLD**, HLD, project deep-dive, take-home review, and the HR round (expected CTC, notice period, "why are you leaving"). |
| **Python only** | Every tool is stdlib Python 3.11+. No Node or Bun. |

## Commands

| Command | What it does |
|---|---|
| `/setup` | Builds your profile from your CV, LinkedIn PDF, or a short interview. |
| `/scrape` | Searches company boards and LinkedIn for new roles that match your preferences. |
| `/rank` | Scores every new posting in parallel and gives you a shortlist. |
| `/apply <url or text>` | Scam check → eligibility gates → fit report → tailored CV (+ cover letter or form answers) → a reviewer agent audits every claim against your profile → a verified one-page PDF. |
| `/outreach` | Finds the right person and drafts the message; also drafts follow-ups for applications that went quiet. |
| `/takehome` | Turns an assignment brief into a time-boxed plan, a build, a README and a submission email. |
| `/interview` | Round-specific prep and live mock interviews. |
| `/outcome` | Updates the tracker, breaks down offers, and shows your funnel. |
| `/add-company` | Finds a company's public job board and adds it to the search. |

## Quick start

You need [Claude Code](https://claude.com/claude-code), Python 3.11+, and a LaTeX distribution with `pdflatex` ([MiKTeX](https://miktex.org/) on Windows, [MacTeX](https://tug.org/mactex/) on macOS, `texlive` on Linux). Optionally run `pip install pypdf` for the PDF checks; poppler's `pdftotext` also works.

```bash
# Use a private repo, not a public fork: your profile stays out of git anyway,
# but private is the safer default for a personal job search.
git clone https://github.com/ManiraM-1/jobhunter-ai.git
cd jobhunter-ai
claude
```

Then, inside Claude Code:

```
/setup
/scrape
/rank
/apply 3
```

Details, Windows notes and troubleshooting are in [SETUP.md](SETUP.md).

## Your data stays yours

- `profile/`, `applications/`, `job_scraper/` and `documents/` are git-ignored. They never leave your machine unless you move them.
- The tools only read public job feeds. Nothing logs into LinkedIn, Naukri or any other account, and nothing sends a message on your behalf.
- Job postings are treated as untrusted text: hidden HTML, invisible characters and "ignore previous instructions"-style lines are stripped and shown to you, never followed.
- Nothing about you is made up. A separate reviewer agent checks every claim in a draft against your profile, and anything it can't trace is removed.

## How it works

```
/scrape ─► tools/ats_search.py  (Greenhouse · Lever · Ashby JSON)
        └► tools/linkedin_search.py (public listings)
             │
             ▼
        tools/state.py ── dedup against seen_jobs.json + tracker.csv
             │
/rank ─► fit-scorer agents (parallel) ─► evaluation.md gates + scores
             │
/apply ─► jd-fetcher (read-only) ─► jd_guard.py (scam + injection)
        ─► tailored CV / letter / answers ─► claim-auditor (grounding audit)
        ─► pdflatex ─► verify_pdf.py (1 page, ATS text, keywords, leftovers)
```

## Contributing

The most useful contribution is **more companies**: run `python tools/ats_search.py discover "Company"` and open a PR that adds the `[[company]]` block to `data/companies.toml`. Run `python -m pytest` before sending code changes. See [CONTRIBUTING.md](CONTRIBUTING.md), the [roadmap](ROADMAP.md) for what's next, and the [code of conduct](CODE_OF_CONDUCT.md).

## License

MIT. See [LICENSE](LICENSE).
