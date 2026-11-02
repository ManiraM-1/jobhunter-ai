import json
from email import policy
from email.parser import BytesParser
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

import email_draft

BODY = "Hi Priya,\n\nI applied for SDE-1 (Payments). I built a UPI reconciliation service on Spring Boot.\n\nThanks,\nAarav\n"


def run(capsys, *argv):
    code = email_draft.main(list(argv))
    captured = capsys.readouterr()
    return code, json.loads(captured.out if code == 0 else captured.err)


@pytest.fixture
def files(tmp_path):
    body = tmp_path / "body.txt"
    body.write_text(BODY, encoding="utf-8")
    cv = tmp_path / "Aarav_Sharma_CV.pdf"
    cv.write_bytes(b"%PDF-1.4 fake")
    return tmp_path, body, cv


def test_writes_draft_with_attachment_and_never_sends(files, capsys):
    tmp, body, cv = files
    out = tmp / "outreach" / "priya.eml"
    code, result = run(capsys, "--to", "priya.raman@examplepay.in", "--subject", "SDE-1 application: UPI reconciliation",
                       "--body-file", str(body), "--attach", str(cv), "--from", "aarav@example.com", "--out", str(out))
    assert code == 0 and result["sent"] is False and result["attachment"] == "Aarav_Sharma_CV.pdf"
    msg = BytesParser(policy=policy.default).parsebytes(out.read_bytes())
    assert msg["To"] == "priya.raman@examplepay.in" and msg["From"] == "aarav@example.com"
    assert msg["X-Unsent"] == "1"
    assert "UPI reconciliation service" in msg.get_body(("plain",)).get_content()
    parts = [p for p in msg.iter_attachments()]
    assert [p.get_filename() for p in parts] == ["Aarav_Sharma_CV.pdf"]
    assert parts[0].get_content_type() == "application/pdf"
    assert parts[0].get_content() == b"%PDF-1.4 fake"


def test_mailto_link_round_trips(files, capsys):
    tmp, body, _ = files
    _, result = run(capsys, "--to", "priya@examplepay.in", "--cc", "hr@examplepay.in", "--subject", "Hello & thanks?",
                    "--body-file", str(body), "--out", str(tmp / "a.eml"))
    parts = urlsplit(result["mailto"])
    assert parts.scheme == "mailto" and unquote(parts.path) == "priya@examplepay.in"
    query = parse_qs(parts.query)
    assert query["subject"] == ["Hello & thanks?"] and query["cc"] == ["hr@examplepay.in"]
    assert query["body"][0].startswith("Hi Priya,") and result["mailto_body_truncated"] is False


def test_long_body_truncates_only_the_link(files, capsys):
    tmp, body, _ = files
    body.write_text("word " * 1000)
    out = tmp / "long.eml"
    _, result = run(capsys, "--to", "a@examplepay.in", "--subject", "x", "--body-file", str(body), "--out", str(out))
    assert result["mailto_body_truncated"] is True
    msg = BytesParser(policy=policy.default).parsebytes(out.read_bytes())
    assert msg.get_body(("plain",)).get_content().count("word") == 1000


@pytest.mark.parametrize("argv,code", [
    (["--to", "a@x.in, b@y.in"], "BAD_ADDRESS"),
    (["--to", "not-an-email"], "BAD_ADDRESS"),
    (["--to", "a@x.in\nBcc: evil@z.com"], "BAD_ADDRESS"),
    (["--to", "a@x.in", "--subject", "Hi\nBcc: evil@z.com"], "BAD_SUBJECT"),
    (["--to", "a@x.in", "--subject", "x" * 151], "BAD_SUBJECT"),
])
def test_rejects_header_injection_and_multiple_recipients(files, capsys, argv, code):
    tmp, body, _ = files
    base = {"--subject": "Hello"}
    args = list(argv)
    if "--subject" not in args:
        args += ["--subject", base["--subject"]]
    rc, result = run(capsys, *args, "--body-file", str(body), "--out", str(tmp / "x.eml"))
    assert rc == 1 and result["code"] == code
    assert not (tmp / "x.eml").exists()


def test_missing_files_and_bad_out(files, capsys):
    tmp, body, _ = files
    assert run(capsys, "--to", "a@x.in", "--subject", "s", "--body-file", str(tmp / "nope.txt"), "--out", str(tmp / "a.eml"))[1]["code"] == "NO_BODY"
    assert run(capsys, "--to", "a@x.in", "--subject", "s", "--body-file", str(body), "--attach", str(tmp / "cv.pdf"), "--out", str(tmp / "a.eml"))[1]["code"] == "NO_ATTACHMENT"
    assert run(capsys, "--to", "a@x.in", "--subject", "s", "--body-file", str(body), "--out", str(tmp / "a.txt"))[1]["code"] == "BAD_OUT"
