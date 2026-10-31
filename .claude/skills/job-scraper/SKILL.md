---
name: job-scraper
description: How /scrape searches Indian job sources - company ATS boards (Greenhouse, Lever, Ashby) and LinkedIn's public listings - and which sources are deliberately not scraped.
---

# Job sources

| Source | Tool | Notes |
|---|---|---|
| Company boards on Greenhouse, Lever, Ashby | `tools/ats_search.py` | Official public JSON. Reliable, complete, no login. Coverage is whatever is in `data/companies.toml`; grow it with `/add-company`. |
| LinkedIn public listings | `tools/linkedin_search.py` | Logged-out guest pages. Rate-limited; keep runs small (≤6 queries × 2 pages). Location strings work best as "City, State, India" or just "India". |
| Naukri, Instahyre, Wellfound, Cutshort, Internshala, YC Work at a Startup | **not scraped** | Logins, bot protection, or terms that forbid scraping. Users can paste any posting into `/apply`, or set up alerts on those sites and paste the emails. |

## Building good queries

- LinkedIn matches the whole posting, not just the title, so use **titles** as queries ("SDE 1", "Backend Engineer", "Software Engineer Intern"), not stacks ("java spring").
- The ATS search matches **titles only**. Pass several synonyms: `--keywords "sde,software engineer,backend,developer,engineer i"`.
- Freshers: exclude `senior,sr,staff,lead,principal,manager,director,architect,sde 3,sde iii`.
- Interns: use `--keywords "intern,internship,trainee"` and LinkedIn `--level intern`.
- Don't date-filter company boards: they list only open roles, and plenty were first published months ago. Use `tools/state.py new` to keep only roles you haven't seen.
- City names are normalised: Bangalore → bengaluru; Gurgaon, Noida and Delhi → delhi-ncr.

## Output shape (both tools)

Each result has `source, company, title, location, url, id, posted, india, cities, remote`. That's the shape `tools/state.py new/store` expects.
