import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(
    page_title="Aadityaa Hospital",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remove all Streamlit chrome so only our hospital page shows
st.markdown("""
<style>
    [data-testid="stHeader"]      { display: none !important; }
    [data-testid="stToolbar"]     { display: none !important; }
    [data-testid="stDecoration"]  { display: none !important; }
    [data-testid="stStatusWidget"]{ display: none !important; }
    footer                        { display: none !important; }
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    .stApp { margin: 0 !important; }
    iframe { display: block; width: 100%; border: none; }
</style>
""", unsafe_allow_html=True)

html_file = os.path.join(os.path.dirname(__file__), "hospital_page.html")

with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

# height is set large enough so Streamlit's own page scrolls (no nested iframe scrollbar)
components.html(html_content, height=4700, scrolling=False)
