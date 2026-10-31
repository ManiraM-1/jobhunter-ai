# /add-company: add companies to the board search

Input: `$ARGUMENTS` is one or more company names, comma-separated (e.g. "Swiggy, Postman, Sarvam AI").

For each company:

1. `python tools/ats_search.py discover "<Company>"`. It tries likely board names on Greenhouse, Lever and Ashby and reports open and India role counts.
2. **Found, with India roles** → show the `registry_entry` block and, once the user agrees, append it to `data/companies.toml` (fill in `sector`).
3. **Found, but 0 India roles** → mention it and add only if the user wants it.
4. **Not found** → search the web for "<Company> careers" and look at where the "Apply" buttons go:
   - a `greenhouse.io`, `lever.co` or `ashbyhq.com` link → its URL contains the board name; re-run `discover "<Company>" --slug <name>`;
   - Workday, SmartRecruiters, Darwinbox, Keka, Zoho Recruit or a custom page → not supported for automatic search yet. Tell the user to watch that careers page or set a job alert there, and that any posting from it still works with `/apply`.

After adding, run `python tools/ats_search.py check` once and show only problem rows. If the user wants to contribute verified companies back, suggest a pull request that touches `data/companies.toml` only.
