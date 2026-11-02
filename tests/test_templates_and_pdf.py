import shutil
import subprocess
from pathlib import Path

import pytest

from verify_pdf import check

ROOT = Path(__file__).resolve().parent.parent

needs_pdflatex = pytest.mark.skipif(not shutil.which("pdflatex"), reason="pdflatex not installed")


def latex_errors(log: Path) -> str:
    if not log.exists():
        return "(no .log file was written)"
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    picked = []
    for i, line in enumerate(lines):
        if line.startswith("!"):
            picked.extend(lines[i : i + 3])
    return "\n".join(picked) or "\n".join(lines[-15:])


def build(tex: Path, out: Path) -> Path:
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={out}", str(tex)],
        capture_output=True, timeout=180,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        pytest.fail(
            f"pdflatex could not build {tex.name}.\n\nLaTeX says:\n{latex_errors(out / (tex.stem + '.log'))}"
            + (f"\n\npdflatex stderr: {stderr}" if stderr else "")
            + "\n\nOn MiKTeX: open MiKTeX Console, run Updates, and set 'Install missing packages' to Always.",
            pytrace=False,
        )
    return out / (tex.stem + ".pdf")


@needs_pdflatex
@pytest.mark.parametrize("tex", ["cv/template.tex", "cover_letters/template.tex"])
def test_template_builds_to_one_clean_page(tex, tmp_path):
    report = check(build(ROOT / tex, tmp_path), max_pages=1, keywords=["Java", "Spring Boot", "AWS", "GitHub Actions"])
    assert report["ok"], report["problems"]


@needs_pdflatex
def test_checker_catches_leftovers_and_missing_keywords(tmp_path):
    tex = tmp_path / "bad.tex"
    tex.write_text("\\documentclass{article}\\begin{document}"
                   + "Worked at [Company] improving latency by XX\\%. TODO add more. " * 8
                   + "\\end{document}")
    report = check(build(tex, tmp_path), max_pages=1, keywords=["Kubernetes"])
    joined = " ".join(report["problems"])
    assert not report["ok"]
    assert "[Company]" in joined and "TODO" in joined and "Kubernetes" in joined


def test_no_personal_data_paths_are_tracked():
    ignore = (ROOT / ".gitignore").read_text()
    for path in ("profile/", "applications/", "job_scraper/", "documents/*", ".env"):
        assert path in ignore
