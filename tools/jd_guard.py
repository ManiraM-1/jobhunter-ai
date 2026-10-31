#!/usr/bin/env python3
"""Clean a job posting and flag anything that should make you stop and look.

Two kinds of finding:

  injection  Text aimed at the AI rather than at you: hidden HTML, invisible
             characters, lines like "ignore previous instructions". These are
             stripped from the cleaned text and quoted back so you can judge.
  scam       Common Indian fake-job patterns: asking you to pay (registration,
             training, security deposit, laptop), WhatsApp/Telegram-only
             contact, offers without an interview, personal-email "HR".

A flagged posting is never rejected automatically. You decide.

Usage:
  python tools/jd_guard.py --in posting.html            (HTML input)
  python tools/jd_guard.py --in posting.txt --text      (plain text input)
Prints JSON: {"verdict": "clean"|"flagged", "findings": [...], "text": "..."}
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import INVISIBLE_CHARS, configure_stdout, emit, fail, html_to_text, remove_hidden_html  # noqa: E402

INJECTION_PATTERNS = [
    r"ignore (?:all |any )?(?:the )?(?:previous|prior|above|earlier) (?:instructions|prompts?|rules)",
    r"disregard (?:all |any )?(?:the )?(?:previous|prior|above) ",
    r"\b(?:system|developer) prompt\b",
    r"\bif you are an? (?:ai|llm|language model|assistant|bot|chatbot)\b",
    r"\byou are (?:now )?(?:an? )?(?:ai|llm|language model|chatgpt|claude|gpt|assistant)\b",
    r"\b(?:ai|llm|language model)s? (?:reading|processing|screening) this\b",
    r"\b(?:include|mention|insert|add) the (?:word|phrase|code|keyword)\b",
    r"\b(?:rate|score|rank) (?:this|the) (?:candidate|applicant|application) (?:as|at|10|highly)\b",
    r"<\|?(?:im_start|im_end|system|endoftext)\|?>",
    r"^\s*(?:assistant|system)\s*:",
    r"\bnew instructions?\b",
]

SCAM_PATTERNS = {
    "asks_for_payment": r"\b(?:registration|processing|training|onboarding|security|refundable|joining|kit|verification|interview)\s+(?:fee|fees|charges?|deposit|amount)\b",
    "asks_for_payment_rupees": r"(?:pay|deposit|transfer)\s+(?:rs\.?|inr|₹)\s?\d",
    "buy_own_equipment": r"\b(?:purchase|buy)\s+(?:your own |a )?(?:laptop|device|kit|starter pack)\b",
    "chat_app_only": r"\b(?:whatsapp|telegram)\b[^.\n]{0,60}\b(?:only|directly|to apply|for (?:the )?interview|hr)\b",
    "no_interview": r"\b(?:no interview|without (?:any )?interview|direct (?:joining|selection)|guaranteed (?:job|placement|selection))\b",
    "too_good_pay": r"\b(?:earn|salary of)\s+(?:rs\.?|inr|₹)?\s?\d[\d,]*\s*(?:per|/)\s*(?:day|week)\b.*\b(?:work from home|part[- ]time|typing|data entry)\b",
    "task_scam": r"\b(?:like|rate|review)\s+(?:youtube|google|hotel|product)s?\b.*\b(?:earn|paid|commission)\b",
}

FREE_MAIL = r"\b[\w.+-]+@(?:gmail|yahoo|outlook|hotmail|rediffmail|ymail)\.com\b"


def analyse(raw: str, *, is_html: bool) -> dict:
    findings: list[dict] = []
    if is_html:
        _, removed = remove_hidden_html(raw)
        for snippet in removed:
            findings.append({"kind": "injection", "type": "hidden_html", "quote": snippet})
        text = html_to_text(raw)
    else:
        text = raw
    invisible = len(INVISIBLE_CHARS.findall(text))
    if invisible:
        findings.append({"kind": "injection", "type": "invisible_characters", "quote": f"{invisible} invisible character(s) removed"})
        text = INVISIBLE_CHARS.sub("", text)

    kept_lines = []
    for line in text.splitlines():
        hit = next((p for p in INJECTION_PATTERNS if re.search(p, line, re.I)), None)
        if hit:
            findings.append({"kind": "injection", "type": "instruction_like_line", "quote": line.strip()[:300]})
        else:
            kept_lines.append(line)
    text = "\n".join(kept_lines).strip()

    lowered = text.lower()
    for name, pattern in SCAM_PATTERNS.items():
        m = re.search(pattern, lowered, re.I | re.S)
        if m:
            start = max(0, m.start() - 60)
            findings.append({"kind": "scam", "type": name, "quote": text[start : m.end() + 60].replace("\n", " ").strip()})
    mails = sorted(set(re.findall(FREE_MAIL, text, re.I)))
    if mails:
        findings.append({"kind": "scam", "type": "personal_email_contact", "quote": ", ".join(mails)})

    return {"verdict": "flagged" if findings else "clean", "findings": findings, "text": text}


def guarded(raw: str | None, *, is_html: bool) -> tuple[str | None, dict]:
    """Clean posting text and return (text, {"verdict", "findings"}) for embedding in tool output."""
    if not raw:
        return None, {"verdict": "clean", "findings": []}
    result = analyse(raw, is_html=is_html)
    return result["text"] or None, {"verdict": result["verdict"], "findings": result["findings"]}


def main(argv=None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="path", required=True)
    parser.add_argument("--text", action="store_true", help="input is plain text, not HTML")
    args = parser.parse_args(argv)
    try:
        raw = Path(args.path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return fail(str(exc), "READ_FAILED")
    looks_html = bool(re.search(r"<(?:html|body|div|p|span|ul|li|br)\b", raw, re.I))
    emit(analyse(raw, is_html=looks_html and not args.text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
