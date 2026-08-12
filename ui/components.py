"""Reusable presentation widgets."""

from __future__ import annotations

import html

import streamlit as st


def chat_bubble(role: str, content: str) -> None:
    """Assistant bubbles render markdown; user bubbles are escaped plain text."""
    if role == "user":
        safe = html.escape(content).replace("\n", "<br>")
        st.markdown(
            f'<div class="tp-row user"><div class="tp-bubble user">{safe}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="tp-row"><div class="tp-bubble assistant">', unsafe_allow_html=True)
        st.markdown(content)
        st.markdown("</div></div>", unsafe_allow_html=True)


def empty_state(icon: str, title: str, hint: str) -> None:
    st.markdown(
        f'<div class="tp-empty"><div style="font-size:2.2rem">{icon}</div>'
        f'<div style="font-weight:600;margin-top:6px;color:#0F4C5C">{title}</div>'
        f'<div style="margin-top:4px">{hint}</div></div>',
        unsafe_allow_html=True,
    )


def chip(text: str, kind: str = "weather") -> str:
    return f'<span class="tp-chip {kind}">{html.escape(str(text))}</span>'


def day_card(day: dict) -> None:
    chips = chip(day.get("weather_summary", "no forecast"), "weather")
    cost = day.get("estimated_entry_cost_inr")
    if cost:
        chips += chip(f"entry approx INR {cost:,}", "cost")
    if day.get("notes"):
        chips += chip("rain plan", "warn")

    title = f"Day {day.get('day')} - {day.get('date', '')}"
    with st.expander(title, expanded=day.get("day") == 1):
        st.markdown(chips, unsafe_allow_html=True)
        st.markdown(
            f"**Morning:** {day.get('morning', '-')}\n\n"
            f"**Afternoon:** {day.get('afternoon', '-')}\n\n"
            f"**Evening:** {day.get('evening', '-')}"
        )
        if day.get("notes"):
            st.caption(day["notes"])


def trace_panel(trace) -> None:
    if not trace:
        return
    with st.expander(f"Agent trace - {len(trace)} tool call(s)", expanded=False):
        for step in trace:
            status = "ok" if step.ok else "warn"
            st.markdown(
                f"{chip(f'step {step.step}', status)} **{step.tool}**", unsafe_allow_html=True
            )
            st.code(str(step.args), language="json")
            st.text(step.result[:900])
            st.divider()
