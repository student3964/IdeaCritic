"""
IdeaCritic — Main Application Entry Point
Run with:  streamlit run app.py
"""
import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(page_title="IdeaCritic", page_icon="🚀", layout="wide")

# ── Inject custom CSS ─────────────────────────────────────────────────────────
from ui_components import inject_css
inject_css()

# ── Import pages ──────────────────────────────────────────────────────────────
from pages_new import show_new_analysis_page
from pages_history import show_history_page
from pages_compare import show_compare_page
from db import debates_collection


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🚀 IdeaCritic")
st.sidebar.markdown(
    "<p style='color:#8080aa;font-size:0.8rem;margin-top:-0.5rem'>"
    "AI-powered multi-agent idea validation</p>",
    unsafe_allow_html=True,
)
st.sidebar.divider()


def _on_page_change():
    if st.session_state.get("radio_nav") == "New Analysis":
        for k in ["clarifying_questions", "idea_title", "idea_desc", "answers", "idea_domain",
                   "analysis_complete", "is_analyzing", "qa_history", "analysis_results"]:
            st.session_state.pop(k, None)


selected = st.sidebar.radio(
    "Navigation",
    ["New Analysis", "Analysis History", "Compare Ideas"],
    key="radio_nav",
    on_change=_on_page_change,
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.subheader("Status")
try:
    n = debates_collection.count_documents({})
    st.sidebar.metric("Saved Analyses", n)
    st.sidebar.success("✅ MongoDB connected")
except Exception:
    st.sidebar.error("❌ DB connection error")

st.sidebar.divider()
st.sidebar.markdown(
    "<small style='color:#8080aa'>"
    "Powered by Gemini 2.5 Flash<br>"
    "LangChain · Tavily RAG · MongoDB · Plotly<br>"
    "© IdeaCritic 2025"
    "</small>",
    unsafe_allow_html=True,
)

# ── Routing ───────────────────────────────────────────────────────────────────
if selected == "New Analysis":
    show_new_analysis_page()
elif selected == "Analysis History":
    show_history_page()
elif selected == "Compare Ideas":
    show_compare_page()
