"""
core/email_client.py - Resend API Wrapper & Local HTML Logging Fallback
"""

import os
from pathlib import Path
from typing import Dict, Any

try:
    import resend
except ImportError:
    resend = None

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def send_daily_email(subject: str, html_body: str, date_str: str) -> Dict[str, Any]:
    """
    Send daily HTML report via Resend API.
    If API key is unconfigured or request fails, logs HTML to reports/ directory.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    local_file_path = REPORTS_DIR / f"daily_digest_{date_str}.html"
    
    # Always save a local copy of the HTML report
    with open(local_file_path, "w", encoding="utf-8") as f:
        f.write(html_body)

    api_key = os.getenv("RESEND_API_KEY", "").strip()
    to_email = os.getenv("REPORT_TO_EMAIL", "gadhamk89@gmail.com").strip()
    from_email = os.getenv("REPORT_FROM_EMAIL", "onboarding@resend.dev").strip()

    if not api_key or resend is None:
        return {
            "success": True,
            "sent_via_resend": False,
            "saved_locally": True,
            "local_file": str(local_file_path),
            "recipient": to_email,
            "message": "Resend API key missing or SDK uninstalled. Report saved to local HTML file."
        }

    resend.api_key = api_key

    try:
        response = resend.Emails.send({
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html": html_body
        })
        return {
            "success": True,
            "sent_via_resend": True,
            "saved_locally": True,
            "local_file": str(local_file_path),
            "recipient": to_email,
            "response": response
        }
    except Exception as e:
        return {
            "success": False,
            "sent_via_resend": False,
            "saved_locally": True,
            "local_file": str(local_file_path),
            "recipient": to_email,
            "error": str(e),
            "message": f"Resend API send failed: {str(e)}. Report saved locally."
        }
