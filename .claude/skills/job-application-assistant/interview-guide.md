# Interview preparation (Indian tech hiring)

Ask which round is next, then prepare **only for that round**, specific to this company and role. Use `applications/<folder>/` (posting, CV sent, research) as context.

## Common rounds and how to prep each

| Round | What it is | How to prep |
|---|---|---|
| **Online assessment (OA)** | 60-120 min on HackerRank, HackerEarth, Codility, Mettl or the company's own platform. 2-3 DSA problems, sometimes MCQs on CS fundamentals or aptitude. | Research reported OA patterns for this company (cite sources). Make a 3-5 day plan with topics by frequency: arrays/strings, hashing, two pointers, binary search, graphs (BFS/DFS), DP. Timing strategy: read all problems first, bank partial scores. |
| **DSA / problem solving** | 45-60 min live coding with an interviewer. | Practise talking through approach → complexity → code → dry run → edge cases. Generate 6-8 problems at the company's reported level and hold a mock: the user answers, you play interviewer and give feedback. |
| **Machine coding / LLD** | 90-120 min to build a working, extensible mini-system (parking lot, splitwise, rate limiter, snake & ladder), common at Flipkart, Swiggy, Razorpay, Uber, PhonePe and similar. | Drill: clarify requirements → entities and relationships → interfaces → SOLID → design patterns where they fit (strategy, factory, observer) → in-memory storage → a runnable demo → tests. Time-box practice to 90 minutes. |
| **HLD / system design** | SDE-2 and above, occasionally SDE-1. | Requirements → back-of-envelope numbers → APIs → data model → architecture → bottlenecks → trade-offs. Tie it to the company's real product (e.g. "design UPI collect" for a payments firm). |
| **Project deep-dive** | "Walk me through X" on the user's own work. | For each project on the CV: the problem, why this design, alternatives rejected, the hardest bug, what you'd change, the numbers. Only what's in `profile/candidate.md`; flag anything the user can't defend. |
| **Take-home review** | Defending a submitted assignment. | Re-read the repo; prepare the 3 decisions most likely to be challenged and the improvements you'd make with more time. |
| **Hiring manager / culture** | Ownership, conflict, failure, ambiguity. | Map 5-6 STAR stories from `profile/behavioral.md` to the company's stated values. |
| **HR** | Expected CTC, notice period, current CTC, relocation, "why are you leaving", other offers. | Script these. **Expected CTC**: give a researched range and anchor on fixed pay. **Current CTC**: you can say you'd rather discuss expectations. **Notice period**: state it, plus buy-out flexibility if any. Never misstate a past CTC; Indian employers often verify it with payslips and in background checks. |

## Company research to include

Recent funding or layoffs, the product and its main engineering challenges, the tech stack (engineering blog, job posts, GitHub), interview experiences reported on LeetCode Discuss, GeeksforGeeks or Glassdoor (paraphrase and cite), and the interviewer's background if the user has their name.

## Questions the user should ask

Write 4-5 specific to this team: what the first 90 days look like, on-call, how work gets prioritised, what the last person in the role moved on to, and for interns, how PPO decisions are made and what share converted last cycle.

## Output

Save prep to `applications/<folder>/interview-<round>.md`. Offer a live mock round afterwards.
