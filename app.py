"""AI Travel Planner (India) - Streamlit entrypoint.

Run:  streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

import config
from agent.loop import run_agent, strip_system, trim_history
from agent.prompts import SUGGESTED_PROMPTS
from agent.registry import SPINNER_COPY
from providers.base import ProviderError
from providers.factory import get_provider
from tools.pdf_tool import build_pdf
from ui import theme
from ui import email_panel
from ui.components import chat_bubble, day_card, empty_state, trace_panel
from ui.sidebar import render as render_sidebar

st.set_page_config(page_title="AI Travel Planner — India", page_icon="✈️", layout="wide")
theme.inject()

st.session_state.setdefault("messages", [])   
st.session_state.setdefault("history", [])    
st.session_state.setdefault("backend_choice", config.DEFAULT_BACKEND)

theme.hero(
    "✈️ AI Travel Planner",
    "Grounded in local Indian travel datasets, topped up with live weather, places and currency.",
)

trip = render_sidebar()

if not config.available_backends():
    st.error(
        "**No LLM configured yet.** Open the **API keys** panel in the sidebar and paste "
        "either key — or add it to your `.env` file:\n\n"
        "| Key | Unlocks | Get it free |\n|---|---|---|\n"
        "| `GOOGLE_API_KEY` | Every Gemini and Gemma model | https://aistudio.google.com/apikey |\n"
        "| `OPENROUTER_API_KEY` | Every Nemotron model | https://openrouter.ai/keys |"
    )
    theme.footer()
    st.stop()


def submit(message: str) -> None:
    st.session_state["messages"].append(("user", message, None))

    try:
        backend = st.session_state.get("backend_choice", config.DEFAULT_BACKEND)
        provider = get_provider(backend, st.session_state.get(f"model_choice_{backend}"))
    except ProviderError as exc:
        st.session_state["messages"].append(("assistant", f"⚠️ {exc}", None))
        return
    except Exception as exc:  # missing package, bad SDK version, anything else
        st.session_state["messages"].append(
            ("assistant", f"⚠️ Could not start the model provider: {exc}", None)
        )
        return

    status = st.empty()

    def on_tool(name: str) -> None:
        status.info(SPINNER_COPY.get(name, f"Running {name}..."))

    with st.spinner("Thinking..."):
        result = run_agent(
            message,
            history=st.session_state["history"],
            provider=provider,
            on_tool=on_tool,
        )

    status.empty()
    st.session_state["history"] = trim_history(strip_system(result.messages))
    st.session_state["messages"].append(("assistant", result.text, result.trace))


def compose_trip_prompt(t: dict) -> str:
    return (
        f"Plan a {t['days']}-day trip to {t['destination']} starting {t['start'].isoformat()} "
        f"for {t['travellers']} traveller(s), {t['style']} style. Build the full itinerary and "
        f"a budget breakdown, and also show the total in {t['currency']}."
    )


tab_chat, tab_itin, tab_budget, tab_export = st.tabs(
    ["💬 Chat Planner", "🗓️ Itinerary", "💰 Budget", "📄 Export"]
)

with tab_chat:
    if not st.session_state["messages"]:
        empty_state("🧭", "Where are we going?", "Use the sidebar form, or try one of these:")
        cols = st.columns(len(SUGGESTED_PROMPTS[:3]))
        for col, prompt in zip(cols, SUGGESTED_PROMPTS[:3]):
            if col.button(prompt, use_container_width=True):
                submit(prompt)
                st.rerun()

    for role, text, trace in st.session_state["messages"]:
        chat_bubble(role, text)
        if role == "assistant" and trace:
            trace_panel(trace)

    user_input = st.chat_input("Ask about a destination, budget, hotels, or a full plan...")
    if user_input:
        submit(user_input)
        st.rerun()

if trip.get("submitted"):
    submit(compose_trip_prompt(trip))
    st.rerun()

with tab_itin:
    itinerary = st.session_state.get("itinerary")
    if not itinerary or not itinerary.get("plan"):
        empty_state("🗓️", "No itinerary yet", "Plan a trip in the Chat tab and it will appear here.")
    else:
        st.subheader(f"{itinerary['city']} — {itinerary['days']} days")
        head = st.columns(4)
        head[0].metric("Start", itinerary.get("start_date", "—"))
        head[1].metric("Days", itinerary.get("days", "—"))
        head[2].metric("Travellers", itinerary.get("travellers", "—"))
        head[3].metric("Style", itinerary.get("style", "—"))
        st.divider()
        for day in itinerary["plan"]:
            day_card(day)

with tab_budget:
    budget = st.session_state.get("budget")
    if not budget or not budget.get("items"):
        empty_state("💰", "No budget yet", "Ask about cost in the Chat tab to generate a breakdown.")
    else:
        def _fmt(value):
            try:
                return f"{float(value):,.0f}"
            except (TypeError, ValueError):
                return "—"

        cols = st.columns(3)
        cols[0].metric("Total (INR)", _fmt(budget.get("total")))
        cols[1].metric("Per person", _fmt(budget.get("per_person")))
        cols[2].metric("Per person / day", _fmt(budget.get("per_person_per_day")))

        frame = pd.DataFrame(
            {"Category": list(budget["items"]), "INR": list(budget["items"].values())}
        ).set_index("Category")
        st.bar_chart(frame, color="#0F4C5C")
        st.dataframe(frame.style.format("{:,.0f}"), use_container_width=True)
        st.caption(f"Accommodation basis: {budget.get('accommodation_source', 'n/a')}")


with tab_export:
    itinerary = st.session_state.get("itinerary")
    if not itinerary:
        empty_state("📄", "Nothing to export", "Generate an itinerary first.")
    else:
        left, right = st.columns(2)

        with left:
            st.markdown("#### Download")
            if st.button("Build PDF", type="primary", use_container_width=True):
                try:
                    path = build_pdf(narrative=st.session_state.get("last_answer", ""))
                    st.session_state["pdf_path"] = str(path)
                    st.success(f"Created {path.name}")
                except Exception as exc:
                    st.error(f"PDF build failed: {exc}")

            pdf_path = st.session_state.get("pdf_path")
            if pdf_path and Path(pdf_path).exists():
                st.download_button(
                    "Download itinerary PDF",
                    data=Path(pdf_path).read_bytes(),
                    file_name=Path(pdf_path).name,
                    mime="application/pdf",
                    use_container_width=True,
                )

        with right:
            email_panel.render(itinerary)

theme.footer()
