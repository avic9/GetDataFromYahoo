import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from price_target_service import send_email_report


def test_send_email_report_skips_when_not_on_github_actions(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("EMAIL_TO", raising=False)
    try:
        send_email_report("subject", "body")
    except Exception as exc:  # pragma: no cover - just ensuring it doesn't raise in local runs
        raise AssertionError(f"Unexpected exception: {exc}")
