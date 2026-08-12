"""Gmail SMTP delivery. smtplib and email.mime are stdlib - no new dependency.

Requires a Google App Password, NOT the account password. Generate one at
https://myaccount.google.com/apppasswords (2-Step Verification must be on).
"""

from __future__ import annotations

import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import config
from tools.pdf_tool import build_pdf
from utils import store
from utils.logger import get_logger

log = get_logger(__name__)

RESEND_URL = "https://api.resend.com/emails"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def send_email(to_address: str, subject: str = "", body: str = "",
               attachment: str | Path | None = None) -> str:
    sender = config.get_secret("GMAIL_ADDRESS")
    password = config.get_secret("GMAIL_APP_PASSWORD")

    if not sender or not password:
        return (
            "Email is not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env "
            "(use a Google App Password, not your account password)."
        )
    if not to_address or not EMAIL_RE.match(to_address.strip()):
        return f"'{to_address}' is not a valid email address."

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = to_address.strip()
    message["Subject"] = subject or "Your AI-generated travel itinerary"
    message.attach(MIMEText(body or "Your itinerary is attached. Safe travels!", "plain", "utf-8"))

    if attachment:
        path = Path(attachment)
        if path.exists():
            try:
                part = MIMEApplication(path.read_bytes(), _subtype="pdf")
                part.add_header("Content-Disposition", "attachment", filename=path.name)
                message.attach(part)
            except OSError as exc:
                log.warning("Could not attach %s: %s", path, exc)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(message)
        return f"Email sent to {to_address}."
    except smtplib.SMTPAuthenticationError as exc:
        # Google's own text distinguishes the causes - don't hide it.
        detail = ""
        try:
            raw = exc.smtp_error.decode("utf-8", "replace") if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error)
            detail = f" Google said ({exc.smtp_code}): {raw.strip()[:300]}"
        except Exception:
            pass

        hint = "Check the app password was copied correctly."
        lowered = detail.lower()
        if "application-specific password required" in lowered:
            hint = ("You used your account password. Generate an App Password at "
                    "https://myaccount.google.com/apppasswords")
        elif "username and password not accepted" in lowered:
            hint = ("Either the app password is wrong/revoked, or the Gmail address does not "
                    "match the account that generated it. Generate a fresh one.")
        elif "disabled" in lowered or "not enabled" in lowered:
            hint = "This account has SMTP or app passwords disabled - often a Workspace admin policy."

        return f"Gmail rejected the credentials. {hint}{detail}"
    except (smtplib.SMTPException, OSError) as exc:
        log.warning("SMTP send failed: %s", exc)
        return f"Could not send the email: {exc}"


def send_via_resend(to_address: str, subject: str, body: str,
                    attachment: str | Path | None = None) -> str:
    """Resend API - one key, no 2FA, no app password, no SMTP.

    Free accounts send from onboarding@resend.dev, which Resend restricts to
    the address you signed up with. Add a domain to mail anyone.
    """
    import base64

    import requests

    api_key = config.get_secret("RESEND_API_KEY")
    if not api_key:
        return "Resend is not configured. Paste an API key from resend.com/api-keys."
    if not to_address or not EMAIL_RE.match(to_address.strip()):
        return f"'{to_address}' is not a valid email address."

    sender = config.get_secret("RESEND_FROM") or "AI Travel Planner <onboarding@resend.dev>"
    payload: dict = {
        "from": sender,
        "to": [to_address.strip()],
        "subject": subject or "Your AI-generated travel itinerary",
        "text": body or "Your itinerary is attached. Safe travels!",
    }

    if attachment:
        path = Path(attachment)
        if path.exists():
            try:
                payload["attachments"] = [
                    {
                        "filename": path.name,
                        "content": base64.b64encode(path.read_bytes()).decode(),
                    }
                ]
            except OSError as exc:
                log.warning("Could not attach %s: %s", path, exc)

    try:
        response = requests.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
    except Exception as exc:
        return f"Could not reach Resend: {exc}"

    if response.status_code in (200, 201):
        return f"Email sent to {to_address}."

    detail = ""
    try:
        detail = str((response.json() or {}).get("message") or response.text)[:250]
    except Exception:
        detail = response.text[:250]

    lowered = detail.lower()

    if "testing emails" in lowered or "own email address" in lowered:
        return (
            "Resend free accounts can only send to the address you signed up with, until "
            "you verify a domain. Send it to yourself, or add a domain at resend.com/domains."
        )
    if "domain" in lowered and "verif" in lowered:
        return f"Resend needs a verified domain to send from that address. {detail}"
    if response.status_code in (401, 403):
        return f"Resend rejected the API key. Check it at resend.com/api-keys. {detail}"
    return f"Resend returned {response.status_code}: {detail}"


def send_any(to_address: str, subject: str, body: str,
             attachment: str | Path | None = None) -> str:
    """Use whichever transport is configured. Resend first - it's simpler."""
    if config.get_secret("RESEND_API_KEY"):
        return send_via_resend(to_address, subject, body, attachment)
    return send_email(to_address, subject, body, attachment)


def send_itinerary_email(to_address: str, message: str = "") -> str:
    """Agent-facing wrapper: builds the PDF if needed, then sends it."""
    try:
        if not store.get("itinerary"):
            return "No itinerary has been built yet. Call build_itinerary first."
        pdf_path = store.get("pdf_path")
        if not pdf_path or not Path(pdf_path).exists():
            pdf_path = str(build_pdf(narrative=store.get("last_answer", "")))
            store.put("pdf_path", pdf_path)

        itinerary = store.get("itinerary") or {}
        subject = f"Your {itinerary.get('days', '')}-day itinerary for {itinerary.get('city', 'your trip')}".strip()
        return send_any(to_address, subject, message or "Your itinerary is attached. Safe travels!", pdf_path)
    except Exception as exc:
        log.exception("send_itinerary_email failed")
        return f"Email step failed: {exc}"


SEND_ITINERARY_EMAIL_SCHEMA = {
    "name": "send_itinerary_email",
    "description": (
        "Email the generated itinerary PDF to an address. Call this ONLY when the user "
        "explicitly asks to have the plan emailed and has supplied an address."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "to_address": {"type": "string", "description": "Recipient email address."},
            "message": {"type": "string", "description": "Optional short covering note."},
        },
        "required": ["to_address"],
    },
}
