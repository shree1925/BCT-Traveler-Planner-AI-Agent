"""Email panel for the Export tab.

Everything happens in the browser: connect a Gmail sender, compose, preview,
send. No .env editing required. Credentials are session-scoped and never
written to disk.

There is also a no-setup path: a mailto link that opens the user's own mail
client with the subject and body prefilled.
"""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path

import streamlit as st

import config
from tools.email_tool import EMAIL_RE, send_any, send_email, send_via_resend
from tools.pdf_tool import build_pdf
from ui.components import chip

APP_PASSWORD_URL = "https://myaccount.google.com/apppasswords"


def _gmail_ready() -> bool:
    return bool(config.get_secret("GMAIL_ADDRESS") and config.get_secret("GMAIL_APP_PASSWORD"))


def _resend_ready() -> bool:
    return bool(config.get_secret("RESEND_API_KEY"))


def _configured() -> bool:
    return _gmail_ready() or _resend_ready()


def _active_sender() -> str:
    if _resend_ready():
        return "Resend"
    if _gmail_ready():
        return config.get_secret("GMAIL_ADDRESS") or "Gmail"
    return ""


def _resend_setup() -> None:
    st.caption(
        "**Easiest option.** Sign up at resend.com with GitHub or Google, copy the API "
        "key it shows you, paste it here. No 2-factor dance, no app passwords, no SMTP."
    )
    st.markdown("[Get a free API key →](https://resend.com/api-keys)")

    key = st.text_input(
        "Resend API key",
        value="",
        type="password",
        placeholder="re_...",
        key="resend_key_input",
    )
    if key.strip():
        config.set_runtime_key("RESEND_API_KEY", key.strip())

    if _resend_ready():
        st.markdown(chip("active", "ok"), unsafe_allow_html=True)
        st.caption(
            "Free accounts send from `onboarding@resend.dev` and can only mail **the "
            "address you signed up with** until you verify a domain. Fine for testing; "
            "add a domain at resend.com/domains to mail anyone."
        )
        test_to = st.text_input(
            "Send a test to", value="", placeholder="the address you signed up with",
            key="resend_test_to",
        )
        if st.button("Send test email", use_container_width=True, key="resend_test"):
            if not test_to.strip():
                st.warning("Enter an address first.")
            else:
                with st.spinner("Testing..."):
                    result = send_via_resend(
                        test_to.strip(),
                        "Test from AI Travel Planner",
                        "If you are reading this, email delivery works.",
                    )
                (st.success if result.startswith("Email sent") else st.error)(result)


def _gmail_setup() -> None:
    st.caption(
        "Sends from your own Gmail, so it never lands in spam — but Google requires an "
        "**App Password**, which means turning on 2-Step Verification first. "
        "Worth it if you'll use this a lot."
    )
    st.markdown("[Generate an App Password →](%s)" % APP_PASSWORD_URL)

    address = st.text_input(
        "Gmail address",
        value=config.get_secret("GMAIL_ADDRESS") or "",
        placeholder="you@gmail.com",
        key="gmail_address_input",
    )
    password = st.text_input(
        "App password",
        value="",
        type="password",
        placeholder="16 letters, spaces are fine",
        key="gmail_password_input",
        help="Google generates this for you - it is not your account password.",
    )

    config.set_runtime_key("GMAIL_ADDRESS", address)
    if password.strip():
        cleaned = re.sub(r"\s+", "", password)
        config.set_runtime_key("GMAIL_APP_PASSWORD", cleaned)
        if len(cleaned) != 16:
            st.markdown(
                chip(f"{len(cleaned)} characters — app passwords are exactly 16", "warn"),
                unsafe_allow_html=True,
            )
        elif not cleaned.isalnum():
            st.markdown(chip("app passwords are letters only", "warn"), unsafe_allow_html=True)
        else:
            st.markdown(chip("16 characters ✓", "ok"), unsafe_allow_html=True)

    if _gmail_ready() and st.button("Send test email", use_container_width=True, key="gmail_test"):
        with st.spinner("Testing..."):
            result = send_email(
                config.get_secret("GMAIL_ADDRESS"),
                "Test from AI Travel Planner",
                "If you are reading this, email delivery works.",
            )
        (st.success if result.startswith("Email sent") else st.error)(result)


def _setup() -> None:
    ready = _configured()
    label = f"✅ Connected — sending via {_active_sender()}" if ready else (
        "⚙️ Optional: connect an account for one-click send"
    )

    with st.expander(label, expanded=False):
        resend_tab, gmail_tab = st.tabs(["⚡ Resend (easiest)", "📮 Gmail"])
        with resend_tab:
            _resend_setup()
        with gmail_tab:
            _gmail_setup()

        if ready and st.button("Disconnect", use_container_width=True, key="email_disconnect"):
            for name in ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "RESEND_API_KEY"):
                config.set_runtime_key(name, None)
            for widget in ("gmail_address_input", "gmail_password_input", "resend_key_input"):
                st.session_state.pop(widget, None)
            st.rerun()

        st.caption("Stored for this session only — nothing is written to disk.")


def _default_subject(itinerary: dict) -> str:
    city = itinerary.get("city", "your trip")
    days = itinerary.get("days")
    return f"Your {days}-day itinerary for {city}" if days else f"Your itinerary for {city}"


def _default_body(itinerary: dict) -> str:
    lines = [f"Here's the plan for {itinerary.get('city', 'your trip')}.", ""]
    if itinerary.get("start_date"):
        lines.append(f"Starting {itinerary['start_date']} · {itinerary.get('days', '?')} days "
                     f"· {itinerary.get('travellers', '?')} traveller(s)")
        lines.append("")
    for day in (itinerary.get("plan") or [])[:8]:
        lines.append(f"Day {day.get('day')} ({day.get('date')})")
        for slot in ("morning", "afternoon", "evening"):
            if day.get(slot):
                lines.append(f"  {slot.title()}: {day[slot]}")
        lines.append("")

    budget = st.session_state.get("budget") or {}
    if budget.get("total"):
        lines.append(f"Estimated total: INR {budget['total']:,.0f} "
                     f"({budget.get('per_person', 0):,.0f} per person)")
        lines.append("")
    lines.append("Full details are in the attached PDF. Safe travels!")
    return "\n".join(lines)


def _compose_links(to: str, subject: str, body: str) -> dict[str, str]:
    """Web compose URLs plus a mailto fallback.

    A raw mailto: hands off to whatever the OS has registered as the default
    mail handler - which on many machines is nothing, producing a "how do you
    want to open this?" dialog. The web links just open in the browser.
    """
    body = body[:1800]
    enc = lambda v: urllib.parse.quote(v, safe="")  # noqa: E731

    return {
        "Gmail": (
            "https://mail.google.com/mail/?view=cm&fs=1"
            f"&to={enc(to)}&su={enc(subject)}&body={enc(body)}"
        ),
        "Outlook": (
            "https://outlook.live.com/mail/0/deeplink/compose"
            f"?to={enc(to)}&subject={enc(subject)}&body={enc(body)}"
        ),
        "Yahoo": (
            "https://compose.mail.yahoo.com/"
            f"?to={enc(to)}&subject={enc(subject)}&body={enc(body)}"
        ),
        "Default mail app": (
            f"mailto:{to}?subject={enc(subject)}&body={enc(body)}"
        ),
    }


def _quick_send(itinerary: dict, subject: str, body: str) -> None:
    """Zero-setup path: grab the PDF, open a compose window with everything filled in."""
    st.markdown("**Quickest way — no setup at all**")
    st.caption(
        "Download the PDF, then open a prefilled compose window and drag it in. "
        "Sends from your own account, so it won't hit anyone's spam folder."
    )

    to = st.text_input("Send to", key="quick_to", placeholder="friend@example.com")

    col1, col2 = st.columns([1, 1])
    with col1:
        try:
            pdf_path = st.session_state.get("pdf_path")
            if not pdf_path or not Path(pdf_path).exists():
                pdf_path = str(build_pdf(narrative=st.session_state.get("last_answer", "")))
                st.session_state["pdf_path"] = pdf_path
            st.download_button(
                "1 · Download PDF",
                data=Path(pdf_path).read_bytes(),
                file_name=Path(pdf_path).name,
                mime="application/pdf",
                use_container_width=True,
                key="quick_pdf",
            )
        except Exception as exc:
            st.warning(f"PDF not ready: {exc}")

    links = _compose_links(to.strip(), subject, body)
    with col2:
        st.markdown(
            f"<a href='{links['Gmail']}' target='_blank' rel='noopener' "
            f"style='display:block;text-align:center;padding:9px 4px;border-radius:10px;"
            f"border:1px solid #2A8797;background:#2A8797;color:#fff;text-decoration:none;"
            f"font-weight:600;font-size:0.9rem'>2 · Open in Gmail →</a>",
            unsafe_allow_html=True,
        )

    with st.expander("Other mail apps", expanded=False):
        for name in ("Outlook", "Yahoo", "Default mail app"):
            st.markdown(f"[{name}]({links[name]})")


def render(itinerary: dict) -> None:
    st.markdown("#### Email")

    subject_default = _default_subject(itinerary)
    body_default = _default_body(itinerary)

    if not _configured():
        _quick_send(itinerary, subject_default, body_default)
        st.divider()
        _setup()
        return

    _setup()

    recipients = st.text_input(
        "Send to",
        value=st.session_state.get("last_recipient", ""),
        placeholder="someone@example.com, another@example.com",
        key="email_recipients",
        help="Separate several addresses with commas.",
    )
    addresses = [a.strip() for a in re.split(r"[,;]", recipients) if a.strip()]
    invalid = [a for a in addresses if not EMAIL_RE.match(a)]

    subject = st.text_input("Subject", value=subject_default, key="email_subject")

    with st.expander("Message", expanded=False):
        st.text_area(
            "Body", value=body_default, height=240,
            key="email_body", label_visibility="collapsed",
        )
    body = st.session_state.get("email_body") or body_default

    attach = st.checkbox("Attach the itinerary PDF", value=True, key="email_attach")

    if invalid:
        st.markdown(chip("invalid: " + ", ".join(invalid[:3]), "warn"), unsafe_allow_html=True)

    can_send = addresses and not invalid
    if st.button("Send", type="primary", use_container_width=True, disabled=not can_send):
        pdf_path = None
        if attach:
            with st.spinner("Printing your plan..."):
                try:
                    pdf_path = st.session_state.get("pdf_path")
                    if not pdf_path or not Path(pdf_path).exists():
                        pdf_path = str(build_pdf(narrative=st.session_state.get("last_answer", "")))
                        st.session_state["pdf_path"] = pdf_path
                except Exception as exc:
                    st.warning(f"PDF could not be built, sending without it: {exc}")
                    pdf_path = None

        sent, failed = [], []
        with st.spinner("Licking the stamp..."):
            for address in addresses:
                result = send_any(address, subject, body, pdf_path)
                (sent if result.startswith("Email sent") else failed).append((address, result))

        if sent:
            st.success(f"Sent to {', '.join(a for a, _ in sent)}.")
            st.session_state["last_recipient"] = recipients
            st.balloons()
        for address, result in failed:
            st.error(f"{address}: {result}")

    with st.expander("Prefer to send it yourself?", expanded=False):
        _quick_send(itinerary, subject, body)
