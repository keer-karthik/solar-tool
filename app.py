import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from modules.theme import apply_theme

st.set_page_config(page_title="Chennai Electricity Dashboard", page_icon="⚡", layout="wide")
apply_theme()

st.title("Chennai Household Electricity Dashboard")
st.markdown("Navigate using the sidebar to view **Historical Consumption** or **Consumption Prediction**.")
