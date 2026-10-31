# /rank: score every unranked posting and build a shortlist

Arguments (optional): `$ARGUMENTS`, e.g. `--limit 20`, or a focus like "fintech only".

## Step 1: Candidates
```
python tools/state.py candidates [--limit N]
```
If none, say so and suggest `/scrape`.

## Step 2: Score in parallel
Split the candidates into batches of about 5 and dispatch one `fit-scorer` agent per batch (`.claude/agents/fit-scorer.md`). Pass each agent only: the batch (key, company, title, url, source), and the paths `profile/candidate.md`, `profile/preferences.md` and `.claude/skills/job-application-assistant/evaluation.md`. Each agent fetches its postings, runs the guard, applies the gates and dimensions, and returns a JSON array.

## Step 3: Save
Merge the arrays into `<scratch>/scores.json` and run:
```
python tools/state.py record-rank --in <scratch>/scores.json
```
If keys come back `not_written`, fix them (usually a typo in the key) and re-run for those.

## Step 4: Report
```
python tools/state.py shortlist --min 55
```
Show `Score | Company | Title | Pay (as stated) | Deadline | Why | Gap`, best first. Then, in one line each: postings that failed a gate (and which gate), postings with scam flags, and closed postings. End with the top 3 to `/apply` to first.
