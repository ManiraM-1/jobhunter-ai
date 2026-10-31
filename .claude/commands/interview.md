# /interview: prepare for the next round

Input: `$ARGUMENTS` is a company and round (e.g. "Razorpay machine coding on Monday"), or an application folder.

1. Load the application folder (posting, CV sent, research). If the round type is unclear, ask: OA, DSA, machine coding/LLD, HLD, project deep-dive, take-home review, hiring manager, or HR.
2. Research the company's reported process for this round and role level (`interview-guide.md`, sources cited, paraphrased).
3. Build the prep for **that round only**, per `interview-guide.md`, and save it to `applications/<folder>/interview-<round>.md`. For HR rounds, script expected CTC (anchored on fixed pay), notice period and "why leaving" from `profile/preferences.md` and `profile/behavioral.md`.
4. Offer a mock: you ask, the user answers, and you give specific feedback after each answer (what was strong, what was missing, a better structure). For DSA, give the problem, wait for their approach before revealing anything, then review their code.
5. Update the tracker: `python tools/state.py outcome --company "<C>" --role "<R>" --status interviewing --next "<round> on <date>"`.
