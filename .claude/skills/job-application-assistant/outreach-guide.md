# Outreach: reaching a human before (or right after) applying

In Indian hiring, a short note to the right person often beats the cover letter. Draft it; **never send it**. The user sends it themselves.

## Who to contact (in order)

1. The **hiring manager or team lead** for the role. Search for "<company> engineering manager <team>" with web search and check LinkedIn titles.
2. A **founder or CTO**, at a company under ~50 people.
3. The **recruiter or talent-acquisition** person named on the posting, or found for that company.
4. An **alumnus** from the user's college working there (ask the user; they can search LinkedIn's alumni filter).

Give each person's name, title and the public link you found them on. If research turns up no one confidently, say so instead of guessing a name or email. Never guess email patterns and present them as real.

## Finding a work email (optional, needs the user's own key)

Only when the user has added `HUNTER_API_KEY` or `APOLLO_API_KEY` to `.env`. Check with `python tools/contact_lookup.py status`.

- **Who's there:** `python tools/contact_lookup.py people --domain <company-domain> --department engineering --seniority senior,executive --limit 5` lists up to 10 people at that company (Hunter only). Use it to confirm a name you found by research, or to find the engineering manager when research came up empty.
- **One person's email:** `python tools/contact_lookup.py find --first <First> --last <Last> --domain <company-domain>`. Add `--provider apollo --linkedin <profile URL>` for Apollo. Each call spends a credit unless the result is already cached.
- **Report the confidence honestly.** Say "verified" or "valid" only when the tool says so. A Hunter score under 70, or a status of `accept_all`, `unknown` or `unverified`, means **likely, not confirmed**; say that, and prefer LinkedIn for that person.
- **Limits are deliberate:** one person per `find`, at most 10 per `people`, a daily cap, company domains only. If the user hits the cap, don't work around it. JobHunter is for a few targeted contacts a day, not lists.
- Look up only people connected to a role the user is applying to, and only when they ask for outreach on it.

## Formats

**LinkedIn connection note**: keep it under 200 characters. LinkedIn caps invite notes, and free accounts get a limited number of personalised notes a month, so save them for people who matter. One hook, one ask.
> Hi Priya, applied for SDE-1 (Payments) at Razorpay. I built a UPI reconciliation service on Spring Boot at <company>. Would value 10 mins of your view on the team.

**LinkedIn message or InMail after connecting**: 3-5 sentences. Who you are in one line, the single strongest proof, why this team, a small ask (a referral, a quick call, or just to flag your application).

**Cold email** (founder, CTO or recruiter): a subject line with the role and a hook ("SDE-1 application: built X that does Y"). Under 120 words, the CV attached as a PDF named `Firstname_Lastname_CV.pdf`, and links to GitHub or a live project.

**Referral request** (alumnus or friend): make it easy. The role link, the job ID, a 2-line summary of why the user fits, and the CV, so they can forward it in one click.

**Follow-up**: one polite nudge after 5-7 working days, adding something new (a shipped project, a relevant post). Stop after two follow-ups.

## Rules

- Every claim comes from `profile/candidate.md`.
- No flattery padding ("I've always admired..."), no "Respected Sir", and no "please find attached my resume for your kind consideration".
- Personalise one real detail per message: their post, their product, their team's launch.
- Write in the user's voice (`profile/voice.md`).
