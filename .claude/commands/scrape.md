# /scrape: find new postings

Arguments (optional): `$ARGUMENTS`, e.g. "intern roles in Hyderabad, last 7 days" or "only CRED and Razorpay".

Read `profile/preferences.md` and the job-scraper skill (`.claude/skills/job-scraper/SKILL.md`). Use a scratch folder (the session's scratchpad, or `job_scraper/tmp/`) for intermediate JSON.

## Step 1: Build the search from preferences plus arguments
Keywords from target titles and search keywords; excludes from "title words to exclude"; cities from the location list. Use `--days 14` for LinkedIn only (see Step 2 for why company boards get no date filter). Arguments override preferences for this run only.

## Step 2: Company boards
```
python tools/ats_search.py search --keywords "<k1,k2,...>" --exclude "<x1,...>" --city <c1> --city <c2> [--remote] > <scratch>/ats.json
```
Don't pass `--days` here. Company boards list only roles that are open right now, and many stay open for months after they were first published, so a date filter silently drops live jobs. Step 4 already keeps only the roles you haven't seen before.
Report any `errors` in one line (a board that moved; suggest `python tools/ats_search.py check`).

## Step 3: LinkedIn
Run one search per main title, 2 pages each, India-wide or per city:
```
python tools/linkedin_search.py search --query "<title>" --location "<City>, India" --days 14 [--level entry|intern] --pages 2 > <scratch>/li-<n>.json
```
Keep it to at most 6 LinkedIn searches per run. If one fails with HTTP 429, stop LinkedIn for this run and say so.

## Step 4: Merge and keep only what's new
Combine every `results` array into one JSON array at `<scratch>/all.json`, then:
```
python tools/state.py new --in <scratch>/all.json
```
Drop anything off-target by title that slipped through (e.g. "Sales Engineer" for a backend search) and say how many you dropped.

## Step 5: Show the user
A table sorted by quick fit (title match, then city preference, then newest): `# | Company | Title | City | Posted | Source`. At most 25 rows; mention the rest by count.

## Step 6: Remember them
```
python tools/state.py store --in <scratch>/all.json
```
Then offer: `/rank` to score them all, or `/apply <row number>` to go straight to one.
