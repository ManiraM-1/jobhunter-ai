#!/usr/bin/env python3
"""Turn an outreach email into a draft you open, check and send yourself.

It never sends anything. It writes:

  * an .eml file: double-click it and Outlook or Windows Mail opens it as an
    editable draft, with your CV already attached (Apple Mail and Thunderbird
    open it too; use "Edit as new" / "Send again" there)
  * a mailto: link: opens a new message in your default mail app, including
    Gmail in the browser if you set Gmail as the handler (attach the CV by hand;
    mailto links can't carry attachments)

Usage:
  python tools/email_draft.py --to priya.raman@company.in --subject "SDE-1 application: ..." \\
      --body-file applications/<folder>/email-priya.txt [--attach applications/<folder>/Firstname_Lastname_CV.pdf] \\
      [--from you@example.com] [--cc someone@company.in] --out applications/<folder>/outreach/priya.eml
"""

from __future__ import annotations

import argparse
import mimetypes
import re
import sys
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import configure_stdout, emit, fail  # noqa: E402

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]{1,64}@([A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,63}$")
MAX_ATTACHMENT = 10 * 1024 * 1024
MAILTO_BODY_LIMIT = 1800


class DraftError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def check_address(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not EMAIL_RE.match(value):
        raise DraftError(f"--{field} must be one plain email address", "BAD_ADDRESS")
    return value


def check_subject(subject: str) -> str:
    subject = subject.strip()
    if not subject or "\n" in subject or "\r" in subject:
        raise DraftError("--subject must be a single non-empty line", "BAD_SUBJECT")
    if len(subject) > 150:
        raise DraftError("--subject is over 150 characters; keep it short", "BAD_SUBJECT")
    return subject


def build_message(to: str, subject: str, body: str, sender: str | None, cc: str | None, attachment: Path | None) -> EmailMessage:
    msg = EmailMessage()
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    if sender:
        msg["From"] = sender
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["X-Unsent"] = "1"
    msg.set_content(body.replace("\r\n", "\n").strip() + "\n")
    if attachment:
        if not attachment.is_file():
            raise DraftError(f"attachment not found: {attachment}", "NO_ATTACHMENT")
        if attachment.stat().st_size > MAX_ATTACHMENT:
            raise DraftError("attachment is over 10 MB", "ATTACHMENT_TOO_BIG")
        ctype, _ = mimetypes.guess_type(attachment.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(attachment.read_bytes(), maintype=maintype, subtype=subtype, filename=attachment.name)
    return msg


def mailto_link(to: str, subject: str, body: str, cc: str | None) -> tuple[str, bool]:
    short = body.strip()
    truncated = len(short) > MAILTO_BODY_LIMIT
    if truncated:
        short = short[:MAILTO_BODY_LIMIT].rsplit(" ", 1)[0] + " ..."
    params = [f"subject={quote(subject)}", f"body={quote(short)}"]
    if cc:
        params.insert(0, f"cc={quote(cc)}")
    return f"mailto:{quote(to, safe='@')}?{'&'.join(params)}", truncated


def main(argv=None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--to", required=True)
    parser.add_argument("--cc")
    parser.add_argument("--from", dest="sender")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", required=True, help="plain-text body")
    parser.add_argument("--attach", help="usually the tailored CV PDF")
    parser.add_argument("--out", required=True, help="where to write the .eml draft")
    args = parser.parse_args(argv)
    try:
        to = check_address(args.to, "to")
        cc = check_address(args.cc, "cc")
        sender = check_address(args.sender, "from")
        subject = check_subject(args.subject)
        body_path = Path(args.body_file)
        if not body_path.is_file():
            raise DraftError(f"body file not found: {body_path}", "NO_BODY")
        body = body_path.read_text(encoding="utf-8")
        if not body.strip():
            raise DraftError("body file is empty", "NO_BODY")
        attachment = Path(args.attach) if args.attach else None
        msg = build_message(to, subject, body, sender, cc, attachment)
        out = Path(args.out)
        if out.suffix.lower() != ".eml":
            raise DraftError("--out must end in .eml", "BAD_OUT")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(bytes(msg))
        link, truncated = mailto_link(to, subject, body, cc)
    except DraftError as exc:
        return fail(str(exc), exc.code)
    except OSError as exc:
        return fail(str(exc), "IO_ERROR")
    emit({
        "draft": str(out),
        "to": to,
        "subject": subject,
        "attachment": attachment.name if attachment else None,
        "mailto": link,
        "mailto_body_truncated": truncated,
        "sent": False,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
