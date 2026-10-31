# /outreach: find the right person and draft the message

Input: `$ARGUMENTS` is a company and role, an application folder, or "follow-ups".

**You draft; the user sends.** Never send messages, connection requests or emails yourself, even if a connector would let you.

## For a role
1. Load `applications/<folder>/posting.md` and the company research. If there's no folder, fetch the posting the way `/apply` Step 0 does.
2. Find 1-3 people per `outreach-guide.md` (hiring manager → founder/CTO for small companies → recruiter → alumni). For each: name, title, the public URL where you found them, and why them. If you can't find anyone with confidence, say so.
3. Ask the user if they have an alumnus or friend at the company; if so, draft a referral request first. It has the best odds.
4. **Email address (optional).** If `python tools/contact_lookup.py status` shows a provider configured, ask the user which of the people you found they want an email for, then run `find` for each one they pick (one per call). Show the result with its confidence, worded as `outreach-guide.md` says. If no key is set, skip this step and mention once that adding a Hunter or Apollo key to `.env` enables it.
5. Draft, per person, the right format from `outreach-guide.md`: connection note (under 200 characters), follow-up message, and a cold email when you have an address (public, or from step 4). Save the drafts to `applications/<folder>/outreach.md`.
6. Record it: `python tools/state.py outcome --company "<C>" --role "<R>" --note "outreach drafted: <names>"` (if the application is in the tracker).

## For "follow-ups"
```
python tools/state.py followups
```
For each row due, draft one short, polite nudge that adds something new, and list them. Don't draft a third follow-up for the same person.
