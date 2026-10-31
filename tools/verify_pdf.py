#!/usr/bin/env python3
"""Check a compiled CV or cover letter the way an ATS and a recruiter would.

  * page count against a limit (a fresher CV in India should be one page)
  * the text extracts cleanly (no ligature soup, nothing missing), which is what
    Workday, Greenhouse, Lever and Naukri's parsers actually read
  * the posting's must-have keywords appear in that extracted text
  * nothing left from the template (lorem ipsum, TODO, [Company], XX%)

Usage:
  python tools/verify_pdf.py cv.pdf [--max-pages 1] [--keywords "java,spring boot,aws"]
Exit 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import configure_stdout, emit, fail  # noqa: E402

LEFTOVERS = [r"lorem ipsum", r"\bTODO\b", r"\bTBD\b", r"\[(?:company|role|name|date|city)\]", r"\bXX+%?", r"<\?|\?\?\?"]
LIGATURE_JUNK = re.compile(r"[ﬀ-ﬆ]|\(cid:\d+\)")


def extract(path: Path) -> tuple[int, list[str]]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return len(reader.pages), [(p.extract_text() or "") for p in reader.pages]
    except ImportError:
        pass
    if not shutil.which("pdftotext"):
        raise RuntimeError("install pypdf (pip install pypdf) or poppler's pdftotext")
    text = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True).stdout
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return len(pages), pages


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("­", "").replace("-\n", "")).lower()


def check(path: Path, max_pages: int, keywords: list[str]) -> dict:
    pages, texts = extract(path)
    full = "\n".join(texts)
    flat = normalise(full)
    problems = []
    if pages > max_pages:
        problems.append(f"{pages} pages; limit is {max_pages}")
    if len(flat.strip()) < 200:
        problems.append("almost no extractable text: an ATS will see a blank document")
    junk = LIGATURE_JUNK.findall(full)
    if junk:
        problems.append(f"{len(junk)} unparseable glyphs (ligatures or missing font maps)")
    leftovers = sorted({m.group(0) for p in LEFTOVERS for m in re.finditer(p, full, re.I)})
    if leftovers:
        problems.append("template leftovers: " + ", ".join(leftovers))
    missing = [k for k in keywords if k and normalise(k) not in flat]
    if missing:
        problems.append("keywords not found in extracted text: " + ", ".join(missing))
    return {"file": str(path), "pages": pages, "characters": len(flat), "missing_keywords": missing,
            "problems": problems, "ok": not problems}


def main(argv=None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--keywords", default="", help="comma-separated must-have terms from the posting")
    args = parser.parse_args(argv)
    path = Path(args.pdf)
    if not path.is_file():
        return fail(f"no such file: {path}", "NOT_FOUND")
    try:
        report = check(path, args.max_pages, [k.strip() for k in args.keywords.split(",") if k.strip()])
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        return fail(str(exc), "EXTRACT_FAILED")
    emit(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
