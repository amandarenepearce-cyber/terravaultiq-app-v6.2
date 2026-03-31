import streamlit as st


def inject_brand_theme():
    st.markdown(
        """
        <style>
        :root {
            --tv-bg-1: #0f231d;
            --tv-bg-2: #133127;
            --tv-bg-3: #183a2f;
            --tv-panel-1: #132b23;
            --tv-panel-2: #173229;
            --tv-border: rgba(19, 224, 161, 0.16);
            --tv-border-strong: rgba(19, 224, 161, 0.34);
            --tv-green: #13e0a1;
            --tv-green-2: #0fcf93;
            --tv-text: #f4fff9;
            --tv-muted: #afc2ba;
            --tv-input-bg: #183229;
            --tv-shadow: 0 18px 50px rgba(0,0,0,0.18);
        }

        /* Base app shell */
        .stApp {
            background:
                radial-gradient(circle at 12% 10%, rgba(19,224,161,0.10), transparent 24%),
                radial-gradient(circle at 85% 14%, rgba(19,224,161,0.06), transparent 18%),
                linear-gradient(180deg, var(--tv-bg-1) 0%, var(--tv-bg-2) 46%, var(--tv-bg-3) 100%);
            color: var(--tv-text);
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            max-width: 1380px;
            padding-top: 0.9rem;
            padding-bottom: 2.5rem;
        }

        /* Typography */
        h1, h2, h3, h4, h5, h6, label, p {
            color: var(--tv-text) !important;
        }

        .stCaption, .stMarkdown p {
            color: var(--tv-muted) !important;
        }

        /* Tabs */
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

        /* Text inputs / text area / number input */
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {
            background: var(--tv-input-bg) !important;
            color: var(--tv-text) !important;
            border: 1px solid var(--tv-border-strong) !important;
            border-radius: 18px !important;
            box-shadow: none !important;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder,
        .stNumberInput input::placeholder {
            color: #97aea5 !important;
            opacity: 1 !important;
        }

        .stTextArea textarea {
            min-height: 132px !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {
            border-color: rgba(19,224,161,0.52) !important;
            box-shadow: 0 0 0 1px rgba(19,224,161,0.18) !important;
        }

        /* Selectbox */
        .stSelectbox [data-baseweb="select"] > div {
            background: var(--tv-input-bg) !important;
            color: var(--tv-text) !important;
            border: 1px solid var(--tv-border-strong) !important;
            border-radius: 18px !important;
            min-height: 54px !important;
            box-shadow: none !important;
        }

        .stSelectbox [data-baseweb="select"] span {
            color: var(--tv-text) !important;
        }

        .stSelectbox [data-baseweb="select"] svg {
            fill: var(--tv-text) !important;
        }

        /* Dropdown menu */
        [data-baseweb="popover"] [role="listbox"] {
            background: #1a342b !important;
            border: 1px solid rgba(19,224,161,0.24) !important;
            border-radius: 16px !important;
            box-shadow: 0 22px 50px rgba(0,0,0,0.24) !important;
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
            background: rgba(19,224,161,0.10) !important;
        }

        [data-baseweb="popover"] [aria-selected="true"] {
            background: rgba(19,224,161,0.16) !important;
            color: #ffffff !important;
        }

        /* Radio / checkbox */
        .stCheckbox label,
        .stRadio label {
            color: var(--tv-text) !important;
        }

        /* Buttons */
        .stButton > button {
            width: 100%;
            min-height: 54px;
            background: linear-gradient(180deg, #174034 0%, #14362c 100%) !important;
            color: #f6fff9 !important;
            border: 1px solid rgba(19,224,161,0.38) !important;
            border-radius: 18px !important;
            font-weight: 700 !important;
            letter-spacing: 0.02em;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
        }

        .stButton > button:hover {
            border-color: rgba(19,224,161,0.82) !important;
            box-shadow: 0 12px 28px rgba(0,0,0,0.18);
            transform: translateY(-1px);
        }

        /* Slider */
        .stSlider [data-baseweb="slider"] * {
            color: var(--tv-text) !important;
        }

        /* Metric cards */
        [data-testid="metric-container"] {
            background: linear-gradient(180deg, rgba(22,46,38,0.98) 0%, rgba(18,39,32,0.98) 100%);
            border: 1px solid rgba(19,224,161,0.14);
            border-radius: 20px;
            padding: 14px 16px;
        }

        /* Dataframe */
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(19,224,161,0.12);
            border-radius: 20px;
            overflow: hidden;
            background: rgba(18,39,32,0.72);
        }

        /* Hero */
        .tv-hero {
            padding: 34px 38px;
            border-radius: 30px;
            border: 1px solid rgba(19,224,161,0.16);
            background:
                radial-gradient(circle at top right, rgba(19,224,161,0.08), transparent 24%),
                linear-gradient(180deg, rgba(22,45,38,0.98) 0%, rgba(17,35,29,0.98) 100%);
            margin-bottom: 20px;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.015);
        }

        .tv-pill {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            border: 1px solid rgba(19,224,161,0.24);
            color: var(--tv-green);
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 16px;
        }

        .tv-hero h1 {
            margin: 0 0 12px 0 !important;
            font-size: 70px !important;
            line-height: 0.94 !important;
            letter-spacing: -0.04em;
            color: #f6fff9 !important;
        }

        .tv-hero .accent {
            color: var(--tv-green) !important;
        }

        .tv-hero p {
            margin: 0 !important;
            font-size: 20px !important;
            line-height: 1.45 !important;
            color: var(--tv-muted) !important;
            max-width: 980px;
        }

        /* Card block */
        .tv-card {
            padding: 24px;
            border: 1px solid rgba(19,224,161,0.14);
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(22,45,38,0.97) 0%, rgba(18,38,31,0.97) 100%);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.015);
            margin-bottom: 18px;
        }

        .tv-card h2 {
            margin: 0 !important;
            font-size: 28px !important;
            line-height: 1.1 !important;
            color: var(--tv-text) !important;
        }

        .tv-card-sub {
            margin-top: 8px;
            margin-bottom: 18px;
            color: var(--tv-muted) !important;
            font-size: 15px;
        }

        @media (max-width: 900px) {
            .tv-hero h1 {
                font-size: 46px !important;
            }

            .tv-hero p {
                font-size: 17px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )