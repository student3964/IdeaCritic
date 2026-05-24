"""
IdeaCritic — New Analysis Page
"""
import re
import datetime
import streamlit as st

from config import DOMAINS
from db import debates_collection
from agents import (
    generate_clarifying_questions,
    get_agent_response,
    get_summary,
    parse_investor_output,
)
from ui_components import (
    render_stepper,
    render_agent_turn,
    render_agent_card_static,
    display_score_dashboard,
    build_export_md,
)


def show_new_analysis_page():
    if "qa_history" not in st.session_state:
        st.session_state["qa_history"] = []
        
    has_questions = "clarifying_questions" in st.session_state

    step = 0 if not has_questions else 1
    render_stepper(step)
    st.title("🚀 New Idea Analysis")

    # ── STEP 1: Idea input ────────────────────────────────────────────────────
    if not has_questions:
        st.subheader("Describe your startup idea")
        c1, c2 = st.columns([3, 1])
        with c1:
            idea_title = st.text_input(
                "Short title for your idea",
                placeholder="e.g., EcoSnap — AI litter detection app",
            )
        with c2:
            domain = st.selectbox("Domain / Industry", DOMAINS)

        # Custom domain input when "Other" is selected
        custom_domain = ""
        if domain == "Other":
            custom_domain = st.text_input(
                "Specify your domain",
                placeholder="e.g., PropTech, SpaceTech, FoodTech...",
            )

        idea_desc = st.text_area(
            "Describe your idea in detail",
            placeholder="My startup will solve [problem] for [audience] by [solution] ...",
            height=190,
        )

        if st.button("Generate Clarifying Questions →", type="primary"):
            if idea_title.strip() and idea_desc.strip():
                if len(idea_desc.strip()) < 30:
                    st.error("Please describe your idea in at least a few sentences.")
                else:
                    st.session_state["idea_title"]  = idea_title.strip()
                    st.session_state["idea_desc"]   = idea_desc.strip()
                    final_domain = custom_domain.strip() if (domain == "Other" and custom_domain.strip()) else domain
                    st.session_state["idea_domain"] = final_domain
                    with st.spinner("Generating clarifying questions..."):
                        st.session_state["clarifying_questions"] = generate_clarifying_questions(
                            idea_title, idea_desc
                        )
                    st.session_state["answers"] = {}
                    st.rerun()
            else:
                st.error("Please fill in both the title and description.")

    # ── STEP 2 & 3: Q&A + Analysis ───────────────────────────────────────────
    else:
        st.subheader("Answer the clarifying questions")
        for i, q in enumerate(st.session_state["clarifying_questions"], start=1):
            q_clean = re.sub(r"^\d+\.\s*", "", q)
            st.session_state["answers"][f"Q{i}"] = st.text_area(
                f"**{q_clean}**", key=f"q{i}", height=80
            )

        st.divider()
        col_l, col_r = st.columns([3, 1])
        with col_l:
            st.subheader("Launch the analysis")
            st.caption("Runs 3 debate agents (Optimist · Critic · Devil's Advocate), Business Analyst, Market Analyst, Investor Bot, and Pivot Suggester.")
        with col_r:
            num_rounds = st.slider("Debate rounds", 1, 5, 2)

        if not st.session_state.get("analysis_complete"):
            if st.button("🚀 Start Full Analysis", type="primary"):
                render_stepper(2)
                st.session_state["is_analyzing"] = True
                
        if st.session_state.get("is_analyzing") and not st.session_state.get("analysis_complete"):

            # Build full context
            context = st.session_state["idea_desc"] + "\n\n--- Founder Clarifications ---\n"
            for i, q in enumerate(st.session_state["clarifying_questions"], start=1):
                q_clean = re.sub(r"^\d+\.\s*", "", q)
                ans = st.session_state["answers"].get(f"Q{i}", "Not answered.")
                context += f"Q: {q_clean}\nA: {ans}\n"

            db_log     = ""
            transcript = ""
            last_resp  = ""
            debate_entries = []  # Store individual entries for re-rendering

            # ── Debate ────────────────────────────────────────────────────────
            st.divider()
            st.subheader("💬 Multi-Agent Debate")
            debate_agents = ["Optimist", "Critic", "Devil's Advocate"]

            for r in range(num_rounds):
                st.markdown(f'<div class="round-badge">Round {r + 1}</div>', unsafe_allow_html=True)
                for persona in debate_agents:
                    with st.spinner(f"{persona} is thinking..."):
                        resp = render_agent_turn(
                            persona,
                            get_agent_response(persona, context, history_context=transcript, last_statement=last_resp),
                        )
                    entry = f"\nRound {r + 1} — {persona}:\n{resp}"
                    db_log     += entry
                    transcript += entry
                    last_resp   = resp
                    debate_entries.append({"round": r + 1, "persona": persona, "response": resp})
                st.divider()

            # ── Business Analyst ──────────────────────────────────────────────
            st.subheader("⚖️ Business Analyst Summary")
            with st.spinner("Business Analyst synthesizing..."):
                final_summary = render_agent_turn(
                    "Business Analyst",
                    get_summary(context, transcript),
                )
            db_log += f"\n\nBusiness Analyst Summary:\n{final_summary}"
            st.divider()

            # ── Market Analyst ────────────────────────────────────────────────
            st.subheader("🌍 Market Intelligence (RAG-powered)")
            with st.spinner("Fetching real-time market data..."):
                market_insight = render_agent_turn(
                    "Market Analyst",
                    get_agent_response("Market Analyst", context),
                )
            db_log += f"\n\nMarket Analyst:\n{market_insight}"
            st.divider()

            # ── Investor Bot ──────────────────────────────────────────────────
            st.subheader("💼 Investor Evaluation")
            investor_context = context + "\n\nMarket Intelligence:\n" + market_insight
            with st.spinner("Investor Bot evaluating..."):
                investor_output = render_agent_turn(
                    "Investor",
                    get_agent_response("Investor", investor_context),
                )
            db_log += f"\n\nInvestor Bot:\n{investor_output}"
            st.divider()

            # ── Score dashboard ───────────────────────────────────────────────
            render_stepper(3)
            st.subheader("📊 Investment Score Dashboard")
            scores = parse_investor_output(investor_output)
            display_score_dashboard(scores)
            st.divider()

            # ── Pivot Suggester (if score < 70 or not "Strong Buy") ───────────
            pivot_output = ""
            weighted = scores.get("weighted_total", 0)
            verdict = scores.get("verdict", "")
            if weighted < 70 or "Strong Buy" not in verdict:
                st.subheader("🔄 Pivot Suggestions")
                st.caption("Score below 70 or cautious verdict detected — generating pivot ideas...")
                critic_feedback = ""
                for line in db_log.splitlines():
                    if "Critic:" in line or "Devil" in line:
                        critic_feedback += line + "\n"
                pivot_context = (
                    context
                    + "\n\nInvestor Evaluation:\n" + investor_output
                    + "\n\nCritical Feedback:\n" + critic_feedback
                )
                with st.spinner("Pivot Suggester brainstorming..."):
                    pivot_output = render_agent_turn(
                        "Pivot Suggester",
                        get_agent_response("Pivot Suggester", pivot_context, last_statement=investor_output),
                    )
                db_log += f"\n\nPivot Suggester:\n{pivot_output}"
                st.divider()

            # ── Save to MongoDB ───────────────────────────────────────────────
            try:
                doc = {
                    "idea_title":        st.session_state.get("idea_title", "Untitled"),
                    "idea_description":  st.session_state.get("idea_desc", ""),
                    "idea_domain":       st.session_state.get("idea_domain", "Other"),
                    "clarifying_answers": st.session_state.get("answers", {}),
                    "debate_transcript": db_log.strip(),
                    "final_summary":     final_summary,
                    "market_insight":    market_insight,
                    "investor_output":   investor_output,
                    "pivot_output":      pivot_output,
                    "scores":            scores,
                    "created_at":        datetime.datetime.now(datetime.timezone.utc),
                }
                res = debates_collection.insert_one(doc)
                st.success(f"💾 Analysis saved to archive! (ID: `{res.inserted_id}`)")
            except Exception as e:
                st.error(f"Failed to save analysis: {e}")

            st.session_state["analysis_results"] = {
                "db_log": db_log,
                "transcript": transcript,
                "debate_entries": debate_entries,
                "final_summary": final_summary,
                "market_insight": market_insight,
                "investor_output": investor_output,
                "pivot_output": pivot_output,
                "scores": scores,
                "context": context,
                "num_rounds": num_rounds,
            }
            st.session_state["analysis_complete"] = True
            st.session_state["is_analyzing"] = False
            st.rerun()

        # ── Render static results if complete ─────────────────────────────────
        if st.session_state.get("analysis_complete"):
            res = st.session_state["analysis_results"]
            
            render_stepper(3)
            st.success("✅ Analysis Complete!")
            
            # ── Re-render full debate ────────────────────────────────────────
            st.divider()
            st.subheader("💬 Multi-Agent Debate")
            prev_round = 0
            for entry in res.get("debate_entries", []):
                if entry["round"] != prev_round:
                    st.markdown(f'<div class="round-badge">Round {entry["round"]}</div>', unsafe_allow_html=True)
                    prev_round = entry["round"]
                render_agent_card_static(entry["persona"], entry["response"])
                if entry["persona"] == "Devil's Advocate":
                    st.divider()
            
            # ── Business Analyst Summary ──────────────────────────────────────
            st.subheader("⚖️ Business Analyst Summary")
            render_agent_card_static("Business Analyst", res["final_summary"])
            st.divider()
            
            # ── Market Intelligence ───────────────────────────────────────────
            st.subheader("🌍 Market Intelligence (RAG-powered)")
            render_agent_card_static("Market Analyst", res["market_insight"])
            st.divider()
            
            # ── Investor Evaluation ───────────────────────────────────────────
            st.subheader("💼 Investor Evaluation")
            render_agent_card_static("Investor", res["investor_output"])
            st.divider()
            
            # ── Score Dashboard ───────────────────────────────────────────────
            st.subheader("📊 Investment Score Dashboard")
            display_score_dashboard(res["scores"])
            st.divider()
            
            # ── Pivot Suggestions (if any) ────────────────────────────────────
            if res.get("pivot_output"):
                st.subheader("🔄 Pivot Suggestions")
                render_agent_card_static("Pivot Suggester", res["pivot_output"])
                st.divider()
                
            # ── Export ────────────────────────────────────────────────────────
            from ui_components import build_export_pdf
            report_md = build_export_md(
                st.session_state.get("idea_title", "Idea"),
                st.session_state.get("idea_desc", ""),
                st.session_state.get("idea_domain", "Other"),
                st.session_state.get("clarifying_questions", []),
                st.session_state.get("answers", {}),
                res["db_log"],
                res["final_summary"],
                res["market_insight"],
                res["investor_output"],
                res["scores"],
            )
            safe_name = re.sub(r"[^\w]", "_", st.session_state.get("idea_title", "report")).lower()
            
            c1, c2, _ = st.columns([1, 1, 2])
            with c1:
                st.download_button(
                    "📄 Download .md",
                    data=report_md,
                    file_name=f"ideacritic_{safe_name}.md",
                    mime="text/markdown",
                )
            with c2:
                try:
                    pdf_bytes = build_export_pdf(report_md)
                    st.download_button(
                        "📄 Download .pdf",
                        data=pdf_bytes,
                        file_name=f"ideacritic_{safe_name}.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"PDF error: {e}")
                    
            # ── Follow-up Q&A ─────────────────────────────────────────────────
            st.divider()
            st.subheader("🗣️ Ask the Panel")
            st.caption("Ask follow-up questions to any agent about the analysis.")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                agent_selection = st.selectbox(
                    "Direct question to:",
                    ["General Panel", "Optimist", "Critic", "Devil's Advocate", "Market Analyst", "Business Analyst", "Custom Persona..."]
                )
                if agent_selection == "Custom Persona...":
                    custom_agent = st.text_input("Enter persona (e.g. Legal Expert)")
                    target_agent = custom_agent if custom_agent else "Expert"
                else:
                    target_agent = agent_selection
            
            for msg in st.session_state["qa_history"]:
                role = "user" if msg["role"] == "user" else "assistant"
                with st.chat_message(role):
                    st.markdown(msg["content"])
                    
            if prompt := st.chat_input("Ask a follow-up doubt..."):
                st.session_state["qa_history"].append({"role": "user", "content": f"**To {target_agent}:** {prompt}"})
                with st.chat_message("user"):
                    st.markdown(f"**To {target_agent}:** {prompt}")
                    
                with st.chat_message("assistant"):
                    with st.spinner(f"{target_agent} is thinking..."):
                        qa_context = res["context"] + "\n\nFull Debate Transcript:\n" + res["transcript"]
                        from agents import stream_generator
                        
                        sys_prompt = f"You are acting as {target_agent}. Answer the user's follow-up question based on the provided startup idea and debate transcript. Keep it concise, actionable, and formatted in markdown."
                        full_prompt = f"{sys_prompt}\n\nContext:\n{qa_context}\n\nUser Question:\n{prompt}"
                        
                        placeholder = st.empty()
                        full_ans = ""
                        for chunk in stream_generator(full_prompt):
                            full_ans += chunk
                            placeholder.markdown(full_ans)
                            
                        st.session_state["qa_history"].append({"role": "assistant", "content": full_ans})
