# Tailoring the CV

Start from `profile/master_cv.tex` (built from `cv/template.tex` during `/setup`). Never add a fact that isn't in `profile/candidate.md` or the master CV.

## What Indian screeners and ATSs want

- **One page** for under ~3 years of experience. Two pages only for 5+ years.
- **No photo, date of birth, marital status, father's name, religion or "Declaration" paragraph.** These are common on older Indian CV templates; product companies read them as dated and they add bias risk.
- **Education near the top for freshers and interns**: degree, branch, college, years, CGPA (as "CGPA 8.4/10"). Add 12th and 10th percentages only for campus or mass-hiring roles that ask for them.
- **Contact line**: city (not full address), +91 phone, professional email, LinkedIn, GitHub. Hyperlink them.
- **Skills grouped by type** (Languages, Frameworks, Cloud & DevOps, Data), in the order the posting cares about.
- **Plain, single-column layout** with standard section names (Education, Experience, Projects, Skills, Achievements) so Workday, Darwinbox, Naukri RMS and Greenhouse parse it. No tables for layout, no text in images, no icons carrying meaning.

## Tailoring steps

1. Pull the posting's **must-haves** (explicitly required) and **nice-to-haves**. Use the posting's exact spelling for a skill the user really has ("Spring Boot", not "SpringBoot").
2. Reorder: the experience and projects closest to the role go first, and their best bullets lead.
3. Rewrite bullets as **action → what → how → result**, with numbers from the profile: "Built a retrieval MCP server in Python (FastMCP) over the internal KB, cutting support lookups from minutes to seconds." If the profile has no number, don't invent one; describe the scope instead (users, services, team size).
4. Cut anything that doesn't serve this role to stay on one page. Don't shrink fonts below 10pt or margins below 1.5cm to cheat it.
5. Only mention a gap in the CV when the user wants to. The cover letter or outreach is the place to bridge it honestly.

## Checks before handing it over

- Compile with `pdflatex` (xelatex also works; avoid lualatex, whose PDFs extract badly) and run `tools/verify_pdf.py <pdf> --max-pages 1 --keywords "<must-haves the user truly has>"`.
- Look at the rendered PDF page itself, not just the source: no orphaned headings, nothing spilling to page 2, links visible.
- Every claim traces back to the profile. The reviewer agent checks this again.
