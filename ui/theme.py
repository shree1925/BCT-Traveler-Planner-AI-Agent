"""Injected CSS - dark theme.

Paired with .streamlit/config.toml (base = "dark"). Both must agree, or
Streamlit's own widget rendering fights these rules.
"""

from __future__ import annotations

import streamlit as st

BG = "#0E1518"          
CARD = "#172227"        
CARD_HI = "#1E2C32"     
BORDER = "#26383F"
INK = "#E7EEF0"         
MUTED = "#93A6AC"       
PRIMARY = "#38B0C4"     
PRIMARY_DIM = "#2A8797"
ACCENT = "#E0A662"      

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Inter', -apple-system, sans-serif;
}}
.stApp {{ background: {BG}; color: {INK}; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}

h1, h2, h3, h4 {{ color: {INK}; font-weight: 700; letter-spacing: -0.01em; }}

/* ---------- hero ---------- */
.tp-hero {{
    background: linear-gradient(120deg, #123039 0%, #17444F 100%);
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 26px 30px;
    margin-bottom: 18px;
}}
.tp-hero h1 {{ color: #FFFFFF; margin: 0; font-size: 2rem; }}
.tp-hero p {{ color: {MUTED}; margin: 6px 0 0; font-size: 0.96rem; }}

/* ---------- cards ---------- */
.tp-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 12px;
}}
.tp-empty {{
    background: {CARD};
    border: 1px dashed {BORDER};
    border-radius: 14px;
    padding: 34px 20px;
    text-align: center;
    color: {MUTED};
}}

/* ---------- chat bubbles ---------- */
.tp-row {{ display: flex; margin: 10px 0; }}
.tp-row.user {{ justify-content: flex-end; }}
.tp-bubble {{
    max-width: 82%;
    padding: 12px 16px;
    border-radius: 16px;
    line-height: 1.55;
    font-size: 0.94rem;
}}
.tp-bubble.user {{
    background: {PRIMARY_DIM};
    color: #FFFFFF;
    border-bottom-right-radius: 4px;
}}
.tp-bubble.assistant {{
    background: {CARD};
    color: {INK};
    border: 1px solid {BORDER};
    border-bottom-left-radius: 4px;
}}
.tp-bubble.assistant h2, .tp-bubble.assistant h3 {{
    font-size: 1.02rem; margin: 10px 0 4px; color: {PRIMARY};
}}
.tp-bubble p {{ margin: 0 0 6px; }}

/* ---------- chips ---------- */
.tp-chip {{
    display: inline-block;
    padding: 3px 11px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 600;
    margin-right: 6px;
}}
.tp-chip.weather {{ background: #14343B; color: {PRIMARY}; }}
.tp-chip.cost    {{ background: #3A2E1C; color: {ACCENT}; }}
.tp-chip.warn    {{ background: #3D2124; color: #F08A88; }}
.tp-chip.ok      {{ background: #16321F; color: #6FCF97; }}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {{
    background: #121C20;
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] * {{ color: {INK}; }}

/* ---------- widget hardening ---------- */
label, [data-testid="stWidgetLabel"] p {{
    color: {INK} !important;
    font-weight: 500;
}}
.stCaption, [data-testid="stCaptionContainer"] p, small {{ color: {MUTED} !important; }}

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTextArea textarea,
[data-baseweb="select"] > div,
[data-baseweb="input"] {{
    background-color: {CARD_HI} !important;
    color: {INK} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
}}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: {MUTED} !important; }}
.stTextInput input:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
.stTextArea textarea:focus {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 2px rgba(56,176,196,0.20) !important;
}}
[data-baseweb="input"] input {{ background-color: transparent !important; }}
.stNumberInput button {{
    background-color: {CARD_HI} !important;
    color: {PRIMARY} !important;
    border: 1px solid {BORDER} !important;
}}

[data-testid="stRadio"] label {{ color: {INK} !important; }}
[data-baseweb="radio"] div[aria-checked="true"] > div {{
    background-color: {PRIMARY} !important;
    border-color: {PRIMARY} !important;
}}
[data-baseweb="popover"], [role="listbox"] {{
    background-color: {CARD} !important;
    color: {INK} !important;
    border: 1px solid {BORDER} !important;
}}
[role="option"]:hover {{ background-color: {CARD_HI} !important; }}

/* ---------- buttons ---------- */
.stButton > button {{
    background: {CARD_HI};
    color: {INK};
    border-radius: 10px;
    border: 1px solid {BORDER};
    font-weight: 600;
    transition: all .15s ease;
}}
.stButton > button:hover {{ border-color: {PRIMARY}; color: {PRIMARY}; }}
.stButton > button[kind="primary"] {{
    background: {PRIMARY_DIM};
    border-color: {PRIMARY_DIM};
    color: #FFFFFF;
}}
.stButton > button[kind="primary"]:hover {{ background: {PRIMARY}; color: #06171B; }}
.stDownloadButton > button {{
    background: {CARD_HI}; color: {INK}; border: 1px solid {BORDER}; border-radius: 10px;
}}

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px 10px 0 0;
    padding: 8px 16px;
    font-weight: 600;
    color: {MUTED};
}}
.stTabs [aria-selected="true"] {{ background: {CARD}; color: {PRIMARY}; }}

/* ---------- containers ---------- */
[data-testid="stChatInput"] {{
    background-color: {CARD_HI} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
}}
[data-testid="stChatInput"] textarea {{ color: {INK} !important; }}
[data-testid="stExpander"] {{
    background: {CARD};
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
}}
[data-testid="stMetric"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 12px 14px;
}}
[data-testid="stMetricValue"] {{ color: {PRIMARY}; font-weight: 700; }}
[data-testid="stMetricLabel"] p {{ color: {MUTED} !important; }}
[data-testid="stAlert"] {{ border-radius: 12px; }}
code {{ background: {CARD_HI} !important; color: {ACCENT} !important; }}
hr {{ border-color: {BORDER}; }}

.tp-footer {{
    text-align: center;
    color: {MUTED};
    font-size: 0.8rem;
    padding: 22px 0 8px;
    border-top: 1px solid {BORDER};
    margin-top: 26px;
}}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, tagline: str) -> None:
    st.markdown(
        f'<div class="tp-hero"><h1>{title}</h1><p>{tagline}</p></div>',
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        '<div class="tp-footer">Live data from Open-Meteo (weather), OpenStreetMap Nominatim '
        '(places) and Frankfurter (currency) &mdash; all free, no API key required. '
        'Attraction and hotel records come from local Kaggle-sourced datasets.</div>',
        unsafe_allow_html=True,
    )
