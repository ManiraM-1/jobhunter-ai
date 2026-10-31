# Take-home assignments

Common in Indian startup hiring (backend APIs, full-stack apps, AI/LLM features, data pipelines). The submission *is* the interview, so the goal is a small, finished, well-explained project, not a sprawling one.

## 1. Read the brief like a spec
Pull out: required features, explicit tech constraints, deliverables (repo, deployed link, video, README), deadline, and **how it will be judged** if stated. List the ambiguities and ask the user which to email the company about. Clarifying questions sent early read as a positive signal.

## 2. Scope and plan
- Estimate hours against the deadline; plan for ~70% of the time and keep the rest for polish.
- Pick the **must-haves first**; mark stretch goals separately.
- Choose the stack the brief names. Otherwise use what the user is strongest in and what the company uses.

## 3. Build standards reviewers notice
- A clean folder structure and a clear README: what it does, how to run it in under 5 commands, the architecture in a sentence or a small diagram, decisions and trade-offs, what you'd do next.
- **Secrets only in `.env`**, with a committed `.env.example`. Never commit keys. Check git history before submitting.
- Input validation, error handling and sensible HTTP status codes.
- A few meaningful tests on the core logic, not 100% coverage.
- Small, meaningful commits. One "initial commit" containing everything looks rushed.
- Deploy it if asked or cheap to do (Render, Railway, Vercel, Fly.io free tiers), and check the live link from a logged-out browser.
- For LLM features: handle API failures and timeouts, keep prompts in their own files, and note cost and latency.

## 4. Submission
- A short demo video (2-4 minutes, Loom or similar) if allowed: show it working, then one design decision.
- Reply-email template: the repo link, live link, video, time spent, and the two trade-offs you made deliberately.
- Run `/interview` for the review round straight after submitting, while it's fresh.

Ask the user whether they want explanatory comments in code or explanations in the README only. Many prefer clean code with the reasoning in the README.
