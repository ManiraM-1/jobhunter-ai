# Setup guide

## 1. Install

| Tool | Windows | macOS | Linux |
|---|---|---|---|
| Claude Code | [claude.com/claude-code](https://claude.com/claude-code) | same | same |
| Python 3.11+ | [python.org](https://www.python.org/downloads/) (tick "Add to PATH") | `brew install python` | your package manager |
| LaTeX | [MiKTeX](https://miktex.org/) (allow on-the-fly package installs) | [MacTeX](https://tug.org/mactex/) or `brew install --cask basictex` | `sudo apt install texlive-latex-extra` |
| pypdf (optional) | `pip install pypdf` | `pip3 install pypdf` | `pip3 install pypdf` |

Claude Code needs a paid Claude plan or Anthropic API credits.

**Windows:** run tools as `python tools/...`. The `python3` name on Windows often points to the Microsoft Store stub. The permissions in `.claude/settings.json` allow both.

## 2. Get the code, privately

Your profile lives in git-ignored folders, but a private repository is still the safer default for a personal job search.

```bash
# Option A: just clone and use it
git clone https://github.com/ManiraM-1/jobhunter-ai.git

# Option B: your own private copy that can still pull updates
git clone --bare https://github.com/ManiraM-1/jobhunter-ai.git
cd jobhunter-ai.git
git push --mirror https://github.com/<you>/my-job-search.git   # create it as PRIVATE first
cd .. && rm -rf jobhunter-ai.git
git clone https://github.com/<you>/my-job-search.git && cd my-job-search
git remote add upstream https://github.com/ManiraM-1/jobhunter-ai.git
# later: git pull upstream main
```

## 3. Check it works

```bash
python -m pytest -q                                       # needs: pip install pytest
python tools/ats_search.py check                          # every company board should say "ok"
python tools/ats_search.py search --keywords "engineer" --city bengaluru --days 14 --limit 5
```

## 4. Build your profile

Put whatever you have in `documents/` (CV PDF, LinkedIn "Save to PDF" export, mark sheets), then open Claude Code in the folder and run `/setup`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ats_search.py check` shows `board_unreachable` | The company moved or renamed its board. Run `/add-company "<Company>"` to find the new one, and fix or remove the entry in `data/companies.toml`. |
| LinkedIn search returns HTTP 429 | LinkedIn rate-limited you. Wait an hour and use fewer, more specific queries. |
| A careers page returns 403 | `/apply` falls back to `tools/fetch_page.py`. If robots.txt forbids it too, paste the posting text instead. |
| `verify_pdf.py` reports ligatures or split words | You built with lualatex. Build with `pdflatex`. |
| PDF is two pages | Ask Claude to cut the weakest project or older bullets. Don't shrink the font below 10pt. |
| MiKTeX asks to install packages | Allow it, or turn on automatic installs in the MiKTeX Console. |
