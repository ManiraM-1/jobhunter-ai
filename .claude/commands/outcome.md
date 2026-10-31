# /outcome: record what happened

Input: `$ARGUMENTS`, e.g. "Zeta OA cleared, DSA round Thursday", "rejected by Groww", "offer from CRED 18 LPA fixed + 2 variable", or nothing (then show the tracker).

Statuses: `applied, oa, takehome, interviewing, offer, accepted, rejected, ghosted, withdrawn`.

1. Nothing given → `python tools/state.py tracker` and `python tools/state.py followups`. Show active applications by stage, then what's due.
2. Otherwise map the message to company, role, status, note, next step and follow-up date, then:
   ```
   python tools/state.py outcome --company "<C>" --role "<R>" --status <s> --note "<what happened>" [--next "<next step>"] [--follow-up YYYY-MM-DD] [--ctc "<offer terms>"]
   ```
   If the company has several open applications, ask which one.
3. **Offer**: break it down as fixed, variable (and how it's paid), joining bonus (and clawback terms), retention bonus, ESOPs (count, vesting schedule, cliff, strike price if known), benefits, bond, notice period and joining date. Compare with `profile/preferences.md` and any other offers in the tracker. Don't call fixed + variable + ESOPs "salary".
4. **Rejection**: if feedback was given, add it to the note, and suggest one concrete thing to change for similar roles. Offer to draft a short, gracious reply asking to be considered for future roles.
5. Every 10 outcomes, show a funnel (applied → OA → interview → offer) by source and company type, so the user sees where the pipeline leaks.
