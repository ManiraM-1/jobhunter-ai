"""The workflow docs tell Claude which commands to run; make sure every one of them exists."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = [p for p in ROOT.rglob("*.md") if ".git" not in p.parts and "tests" not in p.parts] + [ROOT / ".claude" / "settings.json"]
TOOL_CALL = re.compile(r"python3? tools/([a-z_]+)\.py(?:\s+([a-z][a-z-]*))?")


def tool_calls():
    calls = set()
    for doc in DOCS:
        for tool, sub in TOOL_CALL.findall(doc.read_text(encoding="utf-8")):
            calls.add((doc.relative_to(ROOT).as_posix(), tool, sub))
    return sorted(calls)


def subcommands(tool: str) -> set[str] | None:
    out = subprocess.run([sys.executable, str(ROOT / "tools" / f"{tool}.py"), "--help"],
                         capture_output=True, text=True, timeout=30).stdout
    m = re.search(r"\{([a-z,-]+)\}", out)
    return set(m.group(1).split(",")) if m else None


@pytest.mark.parametrize("doc,tool,sub", tool_calls())
def test_documented_tool_calls_exist(doc, tool, sub):
    assert (ROOT / "tools" / f"{tool}.py").exists(), f"{doc} references missing tools/{tool}.py"
    subs = subcommands(tool)
    if subs and sub:
        assert sub in subs, f"{doc} uses `{tool}.py {sub}`, which is not a subcommand ({sorted(subs)})"


def test_commands_and_agents_referenced_exist():
    text = "\n".join(p.read_text(encoding="utf-8") for p in DOCS)
    for cmd in set(re.findall(r"`/([a-z-]+)", text)):
        if cmd in {"setup", "scrape", "rank", "apply", "outreach", "takehome", "interview", "outcome", "add-company"}:
            assert (ROOT / ".claude" / "commands" / f"{cmd}.md").exists()
    for agent in set(re.findall(r"`([a-z]+-[a-z]+(?:-[a-z]+)?)` agent", text)):
        assert (ROOT / ".claude" / "agents" / f"{agent}.md").exists(), agent
    guides = ROOT / ".claude" / "skills" / "job-application-assistant"
    for guide in set(re.findall(r"`([a-z-]+-guide\.md|evaluation\.md)`", text)):
        assert (guides / guide).exists(), guide


def test_profile_templates_cover_what_commands_read():
    text = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / ".claude").rglob("*.md")) + (ROOT / "CLAUDE.md").read_text()
    for name in set(re.findall(r"profile/([a-z_]+)\.md", text)):
        assert (ROOT / "profile.example" / f"{name}.md").exists(), name
