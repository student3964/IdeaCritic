"""
IdeaCritic — Analysis History Page
"""
import streamlit as st
from pymongo import DESCENDING

try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

from config import DOMAINS
from db import debates_collection


def show_history_page():
    st.title("📚 Analysis Archive")

    all_analyses = list(debates_collection.find().sort("created_at", DESCENDING))

    if not all_analyses:
        st.info("Your archive is empty. Complete your first idea analysis to see it here.")
        return

    total  = len(all_analyses)
    latest = all_analyses[0].get("created_at")

    m1, m2 = st.columns(2)
    m1.metric("Total Analyses", total)
    m2.metric("Most Recent", latest.strftime("%b %d, %Y") if latest else "—")
    st.divider()

    # ── Search & filter ───────────────────────────────────────────────────────
    sc1, sc2 = st.columns([3, 1])
    with sc1:
        search_q = st.text_input("🔍 Search by title", placeholder="Filter by keyword...")
    with sc2:
        filter_domain = st.selectbox("Filter by domain", ["All"] + DOMAINS)

    filtered = all_analyses
    if search_q:
        filtered = [a for a in filtered if search_q.lower() in a.get("idea_title", "").lower()]
    if filter_domain != "All":
        filtered = [a for a in filtered if a.get("idea_domain", "") == filter_domain]

    st.caption(f"Showing **{len(filtered)}** of {total} analyses")
    st.divider()

    if not filtered:
        st.warning("No analyses match your search criteria.")
        return

    # ── Entries ───────────────────────────────────────────────────────────────
    for idx, analysis in enumerate(filtered):
        title    = analysis.get("idea_title", "Untitled")
        domain   = analysis.get("idea_domain", "")
        created  = analysis.get("created_at")
        scores   = analysis.get("scores", {})
        weighted = scores.get("weighted_total")
        verdict  = scores.get("verdict", "")

        header_parts = [f"**{title}**"]
        if domain:
            header_parts.append(f"`{domain}`")
        if weighted is not None:
            header_parts.append(f"— Score: **{weighted:.0f}/100**")
        if created:
            header_parts.append(f"— {created.strftime('%b %d, %Y')}")

        with st.expander("  ".join(header_parts)):
            left_col, right_col = st.columns([3, 1])

            with left_col:
                st.markdown("**📝 Business Analyst Summary:**")
                st.write(analysis.get("final_summary", "—"))
                st.markdown("**🌍 Market Insight:**")
                st.write(analysis.get("market_insight", "—"))

            with right_col:
                if weighted is not None:
                    st.metric("Investor Score", f"{weighted:.0f}/100")
                if verdict:
                    if "Strong Buy" in verdict:
                        st.success(verdict)
                    elif "Caution" in verdict:
                        st.warning(verdict)
                    else:
                        st.error(verdict)

            # Score bar chart (compact)
            if scores and PLOTLY_OK and weighted is not None:
                labels = ["Market", "Innovation", "Scalability", "Feasibility", "Risk"]
                keys   = ["market_potential", "innovation", "scalability", "team_feasibility", "risk"]
                vals   = [scores.get(k, 0) for k in keys]
                colors = ["#667eea", "#c77dff", "#00d084", "#4da3ff", "#ffd700"]
                fig = go.Figure(go.Bar(
                    x=labels, y=vals,
                    marker=dict(color=colors, line=dict(width=0)),
                    text=[f"{v}" for v in vals],
                    textposition="outside",
                    textfont=dict(color="#e6e6ff", size=11),
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e6e6ff", family="Inter"),
                    yaxis=dict(range=[0, 12], showgrid=False, zeroline=False, tickfont=dict(color="#8080aa")),
                    xaxis=dict(showgrid=False, tickfont=dict(color="#e6e6ff", size=11)),
                    margin=dict(l=0, r=0, t=10, b=10),
                    height=180,
                )
                st.plotly_chart(fig, width='stretch')

            # Pivot suggestions (if any)
            pivot = analysis.get("pivot_output", "")
            if pivot:
                with st.expander("🔄 Pivot Suggestions"):
                    st.markdown(pivot)

            # Investor full output
            with st.expander("💼 Full Investor Output"):
                st.markdown(analysis.get("investor_output", "—"))

            # Debate transcript
            show_debate = st.checkbox("Show Full Debate Transcript", key=f"dbt_{idx}")
            if show_debate:
                st.text(analysis.get("debate_transcript", "—"))

            st.divider()

            # Delete with confirmation
            confirm_key = f"confirm_{idx}"
            if st.button("🗑️ Delete this analysis", key=f"del_{idx}"):
                st.session_state[confirm_key] = True

            if st.session_state.get(confirm_key):
                st.warning("⚠️ This will permanently delete the analysis. Are you sure?")
                y_col, n_col, _ = st.columns([1, 1, 5])
                with y_col:
                    if st.button("✅ Yes, delete", key=f"yes_{idx}"):
                        debates_collection.delete_one({"_id": analysis["_id"]})
                        st.session_state.pop(confirm_key, None)
                        st.success("Analysis deleted.")
                        st.rerun()
                with n_col:
                    if st.button("❌ Cancel", key=f"no_{idx}"):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
