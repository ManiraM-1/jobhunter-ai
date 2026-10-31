# Evaluating a posting (India)

Used by `/rank` (many postings, short form) and `/apply` (one posting, full form). Read `profile/candidate.md` and `profile/preferences.md` first.

Run the **gates** in order. A posting that fails a gate is not scored and not drafted; report the failure with the exact posting text that caused it, because the user may know something the profile doesn't. Then score the five **dimensions**.

---

## Gate 0: Is it real?

Run `tools/jd_guard.py` on the posting. Any `scam` finding is a hard stop until the user says continue. In India, look in particular for:

- **Any payment from the candidate**: registration, training, "refundable security deposit", laptop or kit purchase, background-verification fee. Legitimate employers pay for these themselves.
- **WhatsApp or Telegram as the only channel**, or an "HR" writing from a personal Gmail or Yahoo address for a company that has its own domain.
- **An offer without an interview**, "direct joining", or a guaranteed placement.
- **Pay out of line with the work**: thousands of rupees a day for data entry, typing, or "liking" products and videos.
- **Impersonation**: a big brand's name on a posting that isn't on that brand's careers site or official ATS board. Check that the posting URL's host is the company's own domain, LinkedIn, or a known ATS (greenhouse.io, lever.co, ashbyhq.com, myworkdayjobs.com, smartrecruiters.com, workable.com, keka.com, darwinbox.in, zohorecruit.in). An unknown host gets an "unverified source" warning.

## Gate 1: Eligibility

Read the "who can apply" text verbatim.

| Posting says | Verdict |
|---|---|
| A **batch / graduation year** that excludes the user (e.g. "2025 and 2026 batch only") | FAIL |
| A **minimum CGPA or %** (e.g. "60% throughout 10th, 12th and graduation", "CGPA ≥ 7.5") the user doesn't meet | FAIL. Note that "throughout" means every level. |
| A **degree or branch** restriction (e.g. "CS/IT only", "B.E./B.Tech only, no BCA") the user doesn't meet | FAIL |
| "**No active backlogs**" or "no gap year" and the profile shows otherwise | FAIL |
| **Experience** floor clearly above the user's (e.g. "3+ years" for a fresher) | FAIL. One year short of a "1-3 years" range is a FLAG, not a fail. |
| A role **outside India** that needs a work visa the user doesn't hold, with no mention of sponsorship | FAIL unless the posting says it sponsors. |
| Silent on all of these | PASS, marked unverified for large companies, which often keep eligibility criteria on campus or careers pages. |

## Gate 2: Logistics

| Check | Verdict |
|---|---|
| City not in the user's list, user won't relocate, and the role isn't remote | FAIL |
| Joining date earlier than the user's notice period allows ("immediate joiners only" vs 60-day notice) | FLAG. Many companies buy out notice or wait; say so. |
| Night or rotational shifts the user excluded | FAIL |
| A language requirement the user doesn't meet (e.g. "fluent Kannada for customer calls") | FAIL |

## Gate 3: Bond and contract terms

Indian postings, especially from IT services firms and some training-led programmes, carry terms the user must see before applying.

- **Service or training bond** (e.g. "2-year service agreement, ₹2 lakh if you leave early"): compare with the user's bond preference. Over the limit is a FAIL; within it is a FLAG that quotes the clause.
- **Unpaid internship**, or a stipend below the user's floor: FAIL.
- **Original certificates held by the employer**: always FLAG. Withholding them is a serious red flag.
- **"Internship then full-time based on performance"** (PPO): note it as a positive, and record any stated conversion rate or stipend-to-CTC figure.

## Dimensions (0-100 each)

### 1. Skills match (weight 35%)
- 80-100: the must-haves are the user's primary skills, shown in real work or projects.
- 60-79: most must-haves are there; one or two gaps a few weeks of study would close.
- 40-59: partial match; real upskilling needed.
- Below 40: a different stack or discipline.

Judge the stack, not the buzzwords: "Java + Spring Boot + AWS" vs a profile of "Java, Spring Boot, AWS Lambda" is a strong match even if the posting also lists Kafka.

### 2. Level and experience fit (20%)
Is this the right rung? A fresher applying to SDE-1 / Associate SE / Graduate Engineer roles scores high. SDE-2 with "2-4 years" scores low for a fresher, unless internships plus a strong project add up. "Intern" with a strong PPO record scores high for students and fresh graduates.

### 3. Compensation (15%)
- Read the posting for numbers. If there are none, say "not stated"; don't guess a figure.
- If the user wants a benchmark, look up public ranges for that company and level (Levels.fyi, AmbitionBox, Glassdoor India, or the company's posts) with web search, cite the source, and label it a range, not a promise.
- Score against the user's **fixed-pay** floor. A big headline CTC padded with ESOPs, a one-time joining bonus, or a large variable component counts only its fixed part.
- Interns: score the monthly stipend against the floor, plus the PPO outlook.

### 4. Company and growth (15%)
- Product company vs IT services vs consulting vs captive/GCC (a global company's Indian engineering centre). Weigh against what the user said they want.
- Funding stage and runway for startups (check recent rounds and layoff news with web search, and cite it).
- What the user would learn: real ownership, the engineering bar, and mentorship signals.

### 5. Culture and work fit (15%)
Compare `profile/behavioral.md` with what the posting and research suggest: team size, pace, on-call, work mode, hours.

## Verdict

Weighted total, then:

- **Strong (75+)**: apply now, with full tailoring and outreach.
- **Moderate (55-74)**: apply if the pipeline is thin, or the gaps are cheap to close.
- **Weak (below 55)**: skip, unless the user overrides.
- **gate_fail**: any gate failed.
- **closed**: the posting is no longer live.

## Output

For `/apply`, write it as a short report the user can scan:

```
Real? clean | ⚠ <scam findings, quoted>
Source: <company site | known ATS | LinkedIn | ⚠ unverified host>
Gates: eligibility PASS, logistics FLAG (immediate joiner vs your 30-day notice), bond PASS
Skills 82 · Level 90 · Comp 60 (not stated) · Company 75 · Culture 70  →  77 Strong
Why it fits: ...
Gaps: ...
Pay: <what the posting states, split into fixed, variable and ESOP, or "not stated">
```

For `/rank`, return JSON per posting: `key`, `score`, `verdict`, `gates` (gate → PASS/FLAG/FAIL plus a short note), `strengths` (≤3), `gaps` (≤3), `ctc` (as stated, or null), `deadline` (YYYY-MM-DD or null).
