# /outreach: find the right person and draft the message

Input: `$ARGUMENTS` is a company and role, an application folder, or "follow-ups".

**You draft; the user sends.** Never send messages, connection requests or emails yourself, even if a connector would let you.

## For a role
1. Load `applications/<folder>/posting.md` and the company research. If there's no folder, fetch the posting the way `/apply` Step 0 does.
2. Find 1-3 people per `outreach-guide.md` (hiring manager → founder/CTO for small companies → recruiter → alumni). For each: name, title, the public URL where you found them, and why them. If you can't find anyone with confidence, say so.
3. Ask the user if they have an alumnus or friend at the company; if so, draft a referral request first. It has the best odds.
4. **Email address (optional).** If `python tools/contact_lookup.py status` shows a provider configured, ask the user which of the people you found they want an email for, then run `find` for each one they pick (one per call). Show the result with its confidence, worded as `outreach-guide.md` says. If no key is set, skip this step and mention once that adding a Hunter or Apollo key to `.env` enables it.
5. Draft, per person, the right format from `outreach-guide.md`: connection note (under 200 characters), follow-up message, and a cold email when you have an address (public, or from step 4). Save the drafts to `applications/<folder>/outreach.md`.
6. **Turn each cold email into a ready-to-send draft**, after the user approves its text:
   - **Gmail connector available** (a Gmail tool that creates drafts is in this session): create the draft there with the recipient, subject and body. Use the draft tool only; never a send tool. If it can't attach files, tell the user to attach the CV PDF before sending.
   - **Otherwise:** save the body to `applications/<folder>/outreach/<person>.txt`, then
     ```
     python tools/email_draft.py --to <address> --subject "<subject>" --body-file applications/<folder>/outreach/<person>.txt --attach applications/<folder>/<Firstname_Lastname_CV.pdf> --out applications/<folder>/outreach/<person>.eml
     ```
     Tell the user: double-click the `.eml` to open it as a draft in Outlook or Windows Mail, with the CV attached; or use the `mailto` link the tool prints (opens Gmail too if it's their browser's mail handler; attach the CV by hand).
   - Either way, say plainly that nothing has been sent.
7. Record it: `python tools/state.py outcome --company "<C>" --role "<R>" --note "outreach drafted: <names>"` (if the application is in the tracker).

## For "follow-ups"
```
python tools/state.py followups
```
For each row due, draft one short, polite nudge that adds something new, and list them. Don't draft a third follow-up for the same person.
