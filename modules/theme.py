import streamlit as st

COLORS = {
    "eggshell": "#F7F2DE",
    "light_gold": "#E5CD85",
    "harvest_gold": "#D49622",
    "olive": "#5D765E",
    "black": "#1D282F",
}

# Plotly color sequence for charts
PLOTLY_COLORS = ["#D49622", "#5D765E", "#1D282F", "#E5CD85", "#8B6914"]


def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Lato:wght@300;400;700&display=swap');

    /* Base */
    html, body, [class*="css"] {{
        font-family: 'Lato', sans-serif;
        color: {COLORS["black"]};
    }}
    .stApp {{
        background-color: {COLORS["eggshell"]};
    }}

    /* Headings */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        font-family: 'Instrument Serif', serif !important;
        color: {COLORS["black"]} !important;
        font-weight: 400 !important;
    }}
    h1 {{ font-size: 2.8rem !important; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {COLORS["black"]};
    }}
    section[data-testid="stSidebar"] * {{
        color: {COLORS["eggshell"]} !important;
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        font-family: 'Instrument Serif', serif !important;
    }}
    section[data-testid="stSidebar"] .stSlider label {{
        color: {COLORS["light_gold"]} !important;
    }}

    /* Metrics */
    [data-testid="stMetric"] {{
        background: none;
        border: none;
        padding: 0.5rem 0;
    }}
    [data-testid="stMetricLabel"] {{
        font-family: 'Lato', sans-serif !important;
        font-size: 0.85rem !important;
        color: {COLORS["olive"]} !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    [data-testid="stMetricValue"] {{
        font-family: 'Instrument Serif', serif !important;
        color: {COLORS["black"]} !important;
        font-size: 1.8rem !important;
    }}

    /* Radio buttons as text tabs */
    div[data-testid="stRadio"] > div {{
        flex-direction: row;
        gap: 0;
    }}
    div[data-testid="stRadio"] > div > label {{
        background: none !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0.4rem 1rem !important;
        font-family: 'Lato', sans-serif !important;
        font-weight: 400 !important;
        color: {COLORS["olive"]} !important;
        border-bottom: 2px solid transparent !important;
        cursor: pointer;
    }}
    div[data-testid="stRadio"] > div > label[data-checked="true"],
    div[data-testid="stRadio"] > div > label:has(input:checked) {{
        color: {COLORS["harvest_gold"]} !important;
        border-bottom: 2px solid {COLORS["harvest_gold"]} !important;
        font-weight: 700 !important;
    }}

    /* Buttons as plain text links */
    .stButton > button {{
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        color: {COLORS["harvest_gold"]} !important;
        font-family: 'Lato', sans-serif !important;
        font-weight: 700 !important;
        padding: 0 !important;
        text-decoration: underline;
        text-underline-offset: 3px;
    }}
    .stButton > button:hover {{
        color: {COLORS["black"]} !important;
    }}

    /* Multiselect */
    .stMultiSelect > div > div {{
        background-color: transparent !important;
        border: 1px solid {COLORS["light_gold"]} !important;
    }}

    /* Checkbox */
    .stCheckbox label span {{
        color: {COLORS["eggshell"]} !important;
    }}

    /* Dataframe */
    .stDataFrame {{
        border: none !important;
    }}

    /* Info box */
    .stAlert {{
        background-color: rgba(93, 118, 94, 0.1) !important;
        border-left: 3px solid {COLORS["olive"]} !important;
        color: {COLORS["black"]} !important;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        font-family: 'Lato', sans-serif !important;
        color: {COLORS["olive"]} !important;
        background: none !important;
        border: none !important;
    }}

    /* Hide Streamlit branding */
    #MainMenu, footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)
