import streamlit as st

def inject_brand_theme():
    st.markdown("""
    <style>
    :root {
        --tv-bg: #081512;
        --tv-bg-2: #0b1c17;
        --tv-panel: #0d1f19;
        --tv-panel-2: #10241d;
        --tv-border: rgba(18, 227, 159, 0.18);
        --tv-border-strong: rgba(18, 227, 159, 0.34);
        --tv-green: #12e39f;
        --tv-text: #f4fff9;
        --tv-muted: #a7bdb4;
        --tv-input-bg: #10211b;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 10%, rgba(18,227,159,0.09), transparent 28%),
            radial-gradient(circle at 85% 12%, rgba(18,227,159,0.05), transparent 18%),
            linear-gradient(180deg, #081512 0%, #0b1b17 52%, #0e211b 100%);
        color: var(--tv-text);
    }

    header[data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1380px; padding-top: 0.8rem; padding-bottom: 2.5rem; }

    h1, h2, h3, h4, h5, h6, label, p {
        color: var(--tv-text) !important;
    }

    .stCaption, .stMarkdown p {
        color: var(--tv-muted) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 1.15rem;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .stTabs [data-baseweb="tab"] {
        color: var(--tv-muted);
        font-weight: 600;
        padding-left: 0;
        padding-right: 0;
    }

    .stTabs [aria-selected="true"] {
        color: var(--tv-text) !important;
        border-bottom: 2px solid var(--tv-green) !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background: var(--tv-input-bg) !important;
        color: var(--tv-text) !important;
        border: 1px solid var(--tv-border-strong) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }

    .stTextArea textarea { min-height: 132px !important; }

    .stSelectbox [data-baseweb="select"] > div {
        background: var(--tv-input-bg) !important;
        color: var(--tv-text) !important;
        border: 1px solid var(--tv-border-strong) !important;
        border-radius: 16px !important;
        min-height: 52px !important;
        box-shadow: none !important;
    }

    .stSelectbox [data-baseweb="select"] span { color: var(--tv-text) !important; }
    .stSelectbox [data-baseweb="select"] svg { fill: var(--tv-text) !important; }

    [data-baseweb="popover"] [role="listbox"] {
        background: #13241e !important;
        border: 1px solid rgba(18,227,159,0.22) !important;
        border-radius: 16px !important;
        box-shadow: 0 18px 40px rgba(0,0,0,0.28) !important;
        padding: 6px !important;
    }

    [data-baseweb="popover"] [role="option"] {
        color: var(--tv-text) !important;
        background: transparent !important;
        border-radius: 12px !important;
        margin: 2px 0 !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }

    [data-baseweb="popover"] [role="option"]:hover {
        background: rgba(18,227,159,0.10) !important;
    }

    [data-baseweb="popover"] [aria-selected="true"] {
        background: rgba(18,227,159,0.16) !important;
        color: #ffffff !important;
    }

    .stButton > button {
        width: 100%;
        min-height: 52px;
        background: linear-gradient(180deg, #133127 0%, #0f261f 100%) !important;
        color: #f6fff9 !important;
        border: 1px solid rgba(18,227,159,0.45) !important;
        border-radius: 16px !important;
        font-weight: 700 !important;
    }

    .stButton > button:hover {
        border-color: rgba(18,227,159,0.85) !important;
        box-shadow: 0 10px 28px rgba(0,0,0,0.18);
    }

    [data-testid="metric-container"] {
        background: linear-gradient(180deg, rgba(16,34,28,0.96) 0%, rgba(13,28,23,0.96) 100%);
        border: 1px solid rgba(18,227,159,0.14);
        border-radius: 18px;
        padding: 14px 16px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(18,227,159,0.12);
        border-radius: 18px;
        overflow: hidden;
        background: rgba(15,31,25,0.72);
    }

    .tv-hero {
        padding: 30px 34px;
        border-radius: 28px;
        border: 1px solid rgba(18,227,159,0.16);
        background:
            radial-gradient(circle at top right, rgba(18,227,159,0.07), transparent 24%),
            linear-gradient(180deg, rgba(18,38,31,0.96) 0%, rgba(14,29,24,0.96) 100%);
        margin-bottom: 20px;
    }

    .tv-pill {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        border: 1px solid rgba(18,227,159,0.24);
        color: var(--tv-green);
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 16px;
    }

    .tv-hero h1 {
        margin: 0 0 12px 0 !important;
        font-size: 64px !important;
        line-height: 0.96 !important;
        letter-spacing: -0.03em;
        color: #f6fff9 !important;
    }

    .tv-hero .accent { color: var(--tv-green) !important; }

    .tv-hero p {
        margin: 0 !important;
        font-size: 19px !important;
        line-height: 1.45 !important;
        color: var(--tv-muted) !important;
        max-width: 980px;
    }
    </style>
    """, unsafe_allow_html=True)