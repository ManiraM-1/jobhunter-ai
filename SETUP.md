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

### Windows: getting LaTeX working (MiKTeX)

1. Download the installer from [miktex.org/download](https://miktex.org/download). (`winget install MiKTeX.MiKTeX` also works, but some Windows installs don't have `winget`.)
2. During setup, set **Install missing packages on-the-fly** to **Yes**.
3. Open **MiKTeX Console** → **Updates** → **Check for updates** → **Update now**. A fresh install that was never updated can fail its first build with *"So far, you have not checked for MiKTeX updates"*.
4. In **MiKTeX Console** → **Settings**, set missing-package installs to **Always** so you don't get a pop-up for every package. The pop-ups are safe: packages come from the official CTAN mirrors.
5. **If you installed to a custom folder** (for example `D:\Softwares\MikTex`), Windows won't find `pdflatex` until you add its folder to your **Path**:
   - Search Start for **"Edit environment variables for your account"**.
   - Select the existing variable named **Path** → **Edit** → **New** → paste the folder that contains `pdflatex.exe`, e.g. `D:\Softwares\MikTex\miktex\bin\x64`.
   - Don't create a new variable with a different name (like `miktex`); Windows only searches the one called **Path**.
6. **Close every terminal and fully restart VS Code / Cursor.** Editors keep the PATH they started with; a new terminal tab isn't enough.
7. Check with `where pdflatex`. It should print a path.

To find `pdflatex.exe` if you're not sure where it went: `dir /s /b "D:\Softwares\MikTex\pdflatex.exe"` (use your install folder).

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
python tools/ats_search.py search --keywords "engineer" --city bengaluru --limit 5
```

## 4. Build your profile

Put whatever you have in `documents/` (CV PDF, LinkedIn "Save to PDF" export, mark sheets), then start Claude Code **from inside the repo folder** and run `/setup`:

```bash
cd jobhunter-ai
claude
```

Claude Code only loads the `/setup`, `/scrape`, `/apply` commands from the `.claude/` folder of the directory you start it in. If typing `/` doesn't list them (they're marked *project*), you started it somewhere else. Say **Yes** if it asks whether to trust the folder.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ats_search.py check` shows `board_unreachable` | The company moved or renamed its board. Run `/add-company "<Company>"` to find the new one, and fix or remove the entry in `data/companies.toml`. |
| LinkedIn search returns HTTP 429 | LinkedIn rate-limited you. Wait an hour and use fewer, more specific queries. |
| A careers page returns 403 | `/apply` falls back to `tools/fetch_page.py`. If robots.txt forbids it too, paste the posting text instead. |
| `verify_pdf.py` reports ligatures or split words | You built with lualatex. Build with `pdflatex`. |
| PDF is two pages | Ask Claude to cut the weakest project or older bullets. Don't shrink the font below 10pt. |
| MiKTeX asks to install packages | Safe to allow: they come from official CTAN mirrors. Set installs to **Always** in MiKTeX Console to stop the pop-ups. |
| `where pdflatex` finds nothing after installing | See *Windows: getting LaTeX working* above: add the folder to **Path** and fully restart your editor. |
| Tests show `3 skipped` | `pdflatex` isn't on PATH, so the PDF tests are skipped. Same fix as above. |
| `/setup` isn't recognised in Claude Code | Start `claude` from inside the repo folder, and trust the folder when asked. |
