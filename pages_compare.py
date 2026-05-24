"""
IdeaCritic — Compare Ideas Page (dual-radar chart)
"""
import streamlit as st
from pymongo import DESCENDING

import re
from db import debates_collection
from ui_components import display_comparison_radar, display_comparison_bar_chart
from ui_components import render_agent_card_static


def show_compare_page():
    st.title("🆚 Compare Ideas")
    st.caption("Select two past analyses to compare their Investor scores side-by-side.")

    all_analyses = list(debates_collection.find().sort("created_at", DESCENDING))

    if len(all_analyses) < 2:
        st.info("You need at least **2 completed analyses** in your archive to use this feature.")
        return

    # Build options
    options = {}
    for a in all_analyses:
        title = a.get("idea_title", "Untitled")
        created = a.get("created_at")
        date_str = created.strftime("%b %d, %Y") if created else ""
        score = a.get("scores", {}).get("weighted_total")
        score_str = f" — {score:.0f}/100" if score is not None else ""
        label = f"{title} ({date_str}){score_str}"
        options[label] = a

    labels = list(options.keys())

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔵 Idea A")
        sel_a = st.selectbox("Select first idea", labels, key="cmp_a")
    with col2:
        st.markdown("#### 🟣 Idea B")
        default_b = 1 if len(labels) > 1 else 0
        sel_b = st.selectbox("Select second idea", labels, index=default_b, key="cmp_b")

    if sel_a == sel_b:
        st.warning("Please select two different ideas to compare.")
        return

    idea_a = options[sel_a]
    idea_b = options[sel_b]
    scores_a = idea_a.get("scores", {})
    scores_b = idea_b.get("scores", {})

    if not scores_a or not scores_b:
        st.error("One or both selected analyses don't have valid scores. Please select ideas with complete evaluations.")
        return

    st.divider()

    # ── Score charts ───────────────────────────────────────────────────────────
    st.subheader("📊 Score Comparison")
    tab1, tab2 = st.tabs(["🎯 Radar Chart", "📊 Bar Chart"])
    with tab1:
        display_comparison_radar(
            scores_a, scores_b,
            idea_a.get("idea_title", "Idea A"),
            idea_b.get("idea_title", "Idea B"),
        )
    with tab2:
        display_comparison_bar_chart(
            scores_a, scores_b,
            idea_a.get("idea_title", "Idea A"),
            idea_b.get("idea_title", "Idea B"),
        )

    # ── Side-by-side metrics ──────────────────────────────────────────────────
    st.divider()
    left, right = st.columns(2)

    with left:
        st.markdown(f"#### 🔵 {idea_a.get('idea_title', 'Idea A')}")
        w_a = scores_a.get("weighted_total", 0)
        v_a = scores_a.get("verdict", "N/A")
        st.metric("Weighted Score", f"{w_a:.0f}/100")
        if "Strong Buy" in v_a:
            st.success(v_a)
        elif "Caution" in v_a:
            st.warning(v_a)
        else:
            st.error(v_a)
        st.markdown(f"**Domain:** {idea_a.get('idea_domain', '—')}")
        st.markdown("**Summary:**")
        st.write(idea_a.get("final_summary", "—"))

    with right:
        st.markdown(f"#### 🟣 {idea_b.get('idea_title', 'Idea B')}")
        w_b = scores_b.get("weighted_total", 0)
        v_b = scores_b.get("verdict", "N/A")
        st.metric("Weighted Score", f"{w_b:.0f}/100")
        if "Strong Buy" in v_b:
            st.success(v_b)
        elif "Caution" in v_b:
            st.warning(v_b)
        else:
            st.error(v_b)
        st.markdown(f"**Domain:** {idea_b.get('idea_domain', '—')}")
        st.markdown("**Summary:**")
        st.write(idea_b.get("final_summary", "—"))

    # ── Score breakdown table ─────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Detailed Score Breakdown")
    dims = ["market_potential", "innovation", "scalability", "team_feasibility", "risk"]
    labels_nice = ["Market Potential", "Innovation", "Scalability", "Team Feasibility", "Risk"]

    import pandas as pd
    df = pd.DataFrame({
        "Dimension": labels_nice,
        idea_a.get("idea_title", "A"): [scores_a.get(d, "—") for d in dims],
        idea_b.get("idea_title", "B"): [scores_b.get(d, "—") for d in dims],
    })
    st.dataframe(df, hide_index=True, use_container_width=True)

    # ── Market Competitors ────────────────────────────────────────────────────
    st.divider()
    st.subheader("🏢 Market Competitors")
    
    def extract_competitors(insight_md: str) -> str:
        if not insight_md: return "No market data available."
        if "🏢 Competitor" in insight_md:
            parts = insight_md.split("🏢 Competitor", 1)
            if len(parts) > 1:
                comp_section = "🏢 Competitor" + parts[1]
                # Split at the next major emoji heading if exists
                match = re.search(r'\n(?:📊|🎯|📈) ', comp_section)
                if match:
                    comp_section = comp_section[:match.start()]
                return comp_section.strip()
        return "Competitor section not found."

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{idea_a.get('idea_title', 'Idea A')}**")
        render_agent_card_static("Market Analyst", extract_competitors(idea_a.get("market_insight", "")))
    with c2:
        st.markdown(f"**{idea_b.get('idea_title', 'Idea B')}**")
        render_agent_card_static("Market Analyst", extract_competitors(idea_b.get("market_insight", "")))
