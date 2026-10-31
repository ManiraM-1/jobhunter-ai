# /setup: build the user's profile

Goal: fill `profile/` so every other command has true, complete facts to work from. `profile/` is git-ignored; nothing in it is ever committed.

## Step 1: Create the folder
If `profile/` doesn't exist, copy every file from `profile.example/` into `profile/`, and copy `cv/template.tex` to `profile/master_cv.tex`. If it already exists, say so and ask whether to **update** it (keep what's there, fill gaps) or **start over**.

## Step 2: Gather the facts
Ask which they have, in one question:
1. **Files in `documents/`**: a CV PDF, LinkedIn "Save to PDF" export, mark sheets, offer letters, old cover letters. Read every file there.
2. **A CV pasted in chat.**
3. **Nothing ready**: interview them, one section at a time (education → experience → projects → skills → achievements).

Fill `profile/candidate.md` with exactly what the sources say. When a bullet has no number, ask once whether there is one ("roughly how many users / requests / hours saved?"). If they don't know, keep the bullet without a number. Never estimate one for them.

## Step 3: Preferences
Walk through `profile/preferences.md` as a short conversation, not a form: target titles and level, cities, remote, minimum **fixed** CTC (and stipend floor if they want internships), notice period or joining date, graduation batch, bond tolerance, company types to avoid. Keep the defaults if they skip something.

## Step 4: How they work and how they write
Ask 3-4 quick questions for `profile/behavioral.md` (best environment, what drains them, why they're looking) and collect 3 short STAR stories. Ask for 1-2 writing samples for `profile/voice.md` (a LinkedIn post or email is fine).

## Step 5: Master CV
Fill `profile/master_cv.tex` from `profile/candidate.md` with everything relevant; it may run past one page. `/apply` cuts it down per role. Compile it with `pdflatex -interaction=nonstopmode -output-directory=profile profile/master_cv.tex` and fix any errors.

## Step 6: Company list
Show the companies in `data/companies.toml`. Ask for 5-10 companies they'd love to work at and run `/add-company` on each.

## Step 7: Finish
Summarise in 5 lines what's in the profile, what's missing, and the next command (`/scrape`). Remind them that `profile/`, `applications/` and `job_scraper/` stay on their machine and out of git.
