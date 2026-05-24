"""
IdeaCritic — Reusable UI components (stepper, agent labels, score dashboard, export)
"""
import re
import datetime
import streamlit as st

try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False


# ── CSS injection ─────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
  --bg:        #0c0c1a;
  --bg2:       #11112a;
  --card:      #181830;
  --border:    rgba(130,130,220,0.13);
  --text:      #e6e6ff;
  --muted:     #8080aa;
  --optimist:  #00d084;
  --critic:    #ff4757;
  --devils:    #ff9f43;
  --analyst:   #4da3ff;
  --market:    #c77dff;
  --investor:  #ffd700;
  --accent:    #667eea;
  --accent2:   #764ba2;
}

.stApp { background: var(--bg) !important; font-family: 'Inter', sans-serif !important; }
.stApp * { color: var(--text); }
html, body { background: var(--bg) !important; }

section[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

h1 {
  background: linear-gradient(135deg, #667eea 0%, #c77dff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  letter-spacing: -0.02em;
}
h2, h3, h4 { color: var(--text) !important; font-weight: 700; }

.stButton > button {
  background: linear-gradient(135deg, #667eea, #764ba2) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
  padding: 0.55rem 1.5rem !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.45) !important;
}

[data-testid="stDownloadButton"] button {
  background: linear-gradient(135deg, #11998e, #38ef7d) !important;
  color: #000 !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(102,126,234,0.2) !important;
}

.stSlider [data-baseweb="slider"] { color: var(--accent) !important; }

[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1rem 1.25rem;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.8rem; }
[data-testid="stMetricValue"] { color: var(--investor) !important; font-weight: 700; }

hr { border-color: var(--border) !important; opacity: 1 !important; }

summary {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 0.5rem 1rem !important;
}

[data-testid="stAlert"] {
  background: var(--card) !important;
  border-radius: 10px !important;
}

/* ── Stepper ── */
.stepper {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 2rem;
  margin-top: 0.5rem;
}
.stp {
  padding: 0.4rem 1.2rem;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
  background: var(--card);
  border: 1px solid var(--border);
  white-space: nowrap;
}
.stp.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
}
.stp.done {
  background: rgba(0, 208, 132, 0.15);
  color: var(--optimist);
  border: 1px solid rgba(0,208,132,0.3);
}
.stp-conn { flex: 1; height: 2px; background: var(--border); min-width: 12px; }

/* ── Agent label ── */
.agent-lbl {
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 0.35rem 0.8rem;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 0.6rem;
}
.lbl-optimist { background: rgba(0,208,132,0.15); color: var(--optimist); border: 1px solid rgba(0,208,132,0.3); }
.lbl-critic   { background: rgba(255,71,87,0.15);  color: var(--critic);   border: 1px solid rgba(255,71,87,0.3); }
.lbl-devils   { background: rgba(255,159,67,0.15); color: var(--devils);   border: 1px solid rgba(255,159,67,0.3); }
.lbl-analyst  { background: rgba(77,163,255,0.15); color: var(--analyst);  border: 1px solid rgba(77,163,255,0.3); }
.lbl-market   { background: rgba(199,125,255,0.15);color: var(--market);   border: 1px solid rgba(199,125,255,0.3); }
.lbl-investor { background: rgba(255,215,0,0.15);  color: var(--investor); border: 1px solid rgba(255,215,0,0.3); }
.lbl-pivot    { background: rgba(56,239,125,0.15); color: #38ef7d;         border: 1px solid rgba(56,239,125,0.3); }

/* ── Round badge ── */
.round-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: linear-gradient(135deg,#667eea,#764ba2);
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.75rem;
}

/* ── Verdict badges ── */
.vbadge {
  display: inline-block;
  padding: 0.35rem 1rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.85rem;
}
.vbadge-buy     { background: rgba(0,208,132,0.2); color:#00d084; border:1px solid rgba(0,208,132,0.4); }
.vbadge-caution { background: rgba(255,159,67,0.2);color:#ff9f43; border:1px solid rgba(255,159,67,0.4); }
.vbadge-no      { background: rgba(255,71,87,0.2); color:#ff4757; border:1px solid rgba(255,71,87,0.4); }

/* ── Score big number ── */
.score-big { font-size: 3.8rem; font-weight: 800; line-height: 1; }
.score-green  { color: var(--optimist); }
.score-yellow { color: var(--investor); }
.score-red    { color: var(--critic); }

/* ── Agent card ── */
.agent-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.2rem 1.4rem;
  margin-bottom: 1rem;
  animation: fadeIn 0.35s ease-out;
}
.agent-card-optimist  { border-left: 3px solid var(--optimist); }
.agent-card-critic    { border-left: 3px solid var(--critic); }
.agent-card-devils    { border-left: 3px solid var(--devils); }
.agent-card-analyst   { border-left: 3px solid var(--analyst); }
.agent-card-market    { border-left: 3px solid var(--market); }
.agent-card-investor  { border-left: 3px solid var(--investor); }
.agent-card-pivot     { border-left: 3px solid #38ef7d; }

.agent-card p { margin: 0.4rem 0; }
.agent-card ul, .agent-card ol { margin: 0.5rem 0; padding-left: 1.5rem; }
.agent-card li { margin-bottom: 0.5rem; }
.agent-card h1, .agent-card h2, .agent-card h3, .agent-card h4, .agent-card h5, .agent-card h6 {
  margin: 1rem 0 0.5rem 0;
  font-weight: 700;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)


# ── Stepper ───────────────────────────────────────────────────────────────────
def render_stepper(active: int):
    steps = ["1. Describe", "2. Clarify", "3. Analyze", "4. Results"]
    parts = []
    for i, label in enumerate(steps):
        if i < active:
            cls = "stp done"
        elif i == active:
            cls = "stp active"
        else:
            cls = "stp"
        parts.append(f'<div class="{cls}">{label}</div>')
        if i < len(steps) - 1:
            parts.append('<div class="stp-conn"></div>')
    st.markdown(f'<div class="stepper">{"".join(parts)}</div>', unsafe_allow_html=True)


# ── Agent label ───────────────────────────────────────────────────────────────
_LABEL_CSS = {
    "Optimist":         ("🟢", "lbl-optimist",  "agent-card-optimist"),
    "Critic":           ("🔴", "lbl-critic",    "agent-card-critic"),
    "Devil's Advocate": ("🟠", "lbl-devils",    "agent-card-devils"),
    "Business Analyst": ("🔵", "lbl-analyst",   "agent-card-analyst"),
    "Market Analyst":   ("🟣", "lbl-market",    "agent-card-market"),
    "Investor":         ("💛", "lbl-investor",  "agent-card-investor"),
    "Pivot Suggester":  ("🔄", "lbl-pivot",     "agent-card-pivot"),
}


def agent_label(persona: str):
    emoji, css, _ = _LABEL_CSS.get(persona, ("💬", "lbl-analyst", "agent-card-analyst"))
    st.markdown(
        f'<div class="agent-lbl {css}">{emoji} {persona}</div>',
        unsafe_allow_html=True,
    )


def get_card_class(persona: str) -> str:
    _, _, card = _LABEL_CSS.get(persona, ("", "", "agent-card-analyst"))
    return card


# ── Render a streaming agent turn inside a styled card ────────────────────────
def render_agent_turn(persona: str, generator) -> str:
    """Render an agent response with label + card styling."""
    agent_label(persona)
    card_cls = get_card_class(persona)
    placeholder = st.empty()
    response = ""
    for chunk in generator:
        response += chunk
        placeholder.markdown(
            f'<div class="agent-card {card_cls}">{_md_to_html_simple(response)}</div>',
            unsafe_allow_html=True,
        )
    # Final render with proper HTML conversion
    placeholder.markdown(
        f'<div class="agent-card {card_cls}">{_md_to_html_simple(response)}</div>',
        unsafe_allow_html=True,
    )
    return response


def render_agent_card_static(persona: str, content: str):
    """Render a static agent card for previously-generated content."""
    agent_label(persona)
    card_cls = get_card_class(persona)
    st.markdown(
        f'<div class="agent-card {card_cls}">{_md_to_html_simple(content)}</div>',
        unsafe_allow_html=True,
    )


def _md_to_html_simple(md: str) -> str:
    """Convert markdown text to HTML for rendering inside styled agent cards."""
    import markdown2
    return markdown2.markdown(md)


# ── Score dashboard ───────────────────────────────────────────────────────────
def display_score_dashboard(scores: dict):
    if not scores:
        return

    verdict  = scores.get("verdict", "N/A")
    weighted = scores.get("weighted_total", 0)

    if "Strong Buy" in verdict:
        score_cls  = "score-green"
        badge_cls  = "vbadge vbadge-buy"
    elif "Caution" in verdict:
        score_cls  = "score-yellow"
        badge_cls  = "vbadge vbadge-caution"
    else:
        score_cls  = "score-red"
        badge_cls  = "vbadge vbadge-no"

    left, right = st.columns([1, 2])

    with left:
        st.markdown(
            f'<p style="color:var(--muted);font-size:0.8rem;margin-bottom:0.2rem">WEIGHTED SCORE</p>'
            f'<div class="score-big {score_cls}">{weighted:.0f}</div>'
            f'<p style="color:var(--muted);margin-top:0.1rem">/ 100</p>'
            f'<div class="{badge_cls}">{verdict}</div>',
            unsafe_allow_html=True,
        )
        recs = scores.get("recommendations", [])
        if recs:
            st.markdown("**Next Steps for Founder:**")
            for r in recs:
                st.markdown(f"- {r}")

    with right:
        if PLOTLY_OK:
            labels = ["Market Potential", "Innovation", "Scalability", "Team Feasibility", "Risk"]
            keys   = ["market_potential", "innovation", "scalability", "team_feasibility", "risk"]
            vals   = [scores.get(k, 0) for k in keys]
            colors = ["#667eea", "#c77dff", "#00d084", "#4da3ff", "#ffd700"]

            fig = go.Figure(go.Bar(
                x=vals, y=labels, orientation="h",
                marker=dict(color=colors, line=dict(width=0)),
                text=[f"{v}/10" for v in vals],
                textposition="outside",
                textfont=dict(color="#e6e6ff", size=12),
                hovertemplate="%{y}: %{x}/10<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e6e6ff", family="Inter"),
                xaxis=dict(
                    range=[0, 12], showgrid=False, zeroline=False,
                    tickfont=dict(color="#8080aa", size=11),
                ),
                yaxis=dict(
                    showgrid=False,
                    tickfont=dict(color="#e6e6ff", size=12),
                ),
                margin=dict(l=0, r=60, t=10, b=10),
                height=230,
            )
            st.plotly_chart(fig, width='stretch')
        else:
            labels = ["Market Potential", "Innovation", "Scalability", "Team Feasibility", "Risk"]
            keys   = ["market_potential", "innovation", "scalability", "team_feasibility", "risk"]
            for label, key in zip(labels, keys):
                val = scores.get(key, 0)
                st.markdown(f"**{label}**: {val}/10")
                st.progress(val / 10)


# ── Comparison radar chart ────────────────────────────────────────────────────
def display_comparison_radar(scores_a: dict, scores_b: dict, title_a: str, title_b: str):
    """Render a dual-radar chart comparing two ideas."""
    if not PLOTLY_OK:
        st.warning("Install `plotly` for radar chart comparison.")
        return

    categories = ["Market Potential", "Innovation", "Scalability", "Team Feasibility", "Risk"]
    keys       = ["market_potential", "innovation", "scalability", "team_feasibility", "risk"]

    vals_a = [scores_a.get(k, 0) for k in keys]
    vals_b = [scores_b.get(k, 0) for k in keys]
    # Close the radar polygon
    vals_a += [vals_a[0]]
    vals_b += [vals_b[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_a, theta=categories_closed, fill='toself',
        name=title_a[:30],
        line=dict(color="#667eea", width=2),
        fillcolor="rgba(102,126,234,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals_b, theta=categories_closed, fill='toself',
        name=title_b[:30],
        line=dict(color="#c77dff", width=2),
        fillcolor="rgba(199,125,255,0.15)",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 10],
                tickfont=dict(color="#8080aa", size=10),
                gridcolor="rgba(130,130,220,0.13)",
            ),
            angularaxis=dict(
                tickfont=dict(color="#e6e6ff", size=11),
                gridcolor="rgba(130,130,220,0.13)",
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6e6ff", family="Inter"),
        legend=dict(font=dict(color="#e6e6ff", size=12)),
        margin=dict(l=60, r=60, t=40, b=40),
        height=380,
    )
    st.plotly_chart(fig, width='stretch')


# ── Comparison bar chart ──────────────────────────────────────────────────────
def display_comparison_bar_chart(scores_a: dict, scores_b: dict, title_a: str, title_b: str):
    """Render a grouped bar chart comparing two ideas."""
    if not PLOTLY_OK:
        return

    categories = ["Market Potential", "Innovation", "Scalability", "Team Feasibility", "Risk"]
    keys       = ["market_potential", "innovation", "scalability", "team_feasibility", "risk"]

    vals_a = [scores_a.get(k, 0) for k in keys]
    vals_b = [scores_b.get(k, 0) for k in keys]

    fig = go.Figure(data=[
        go.Bar(name=title_a[:30], x=categories, y=vals_a, marker_color="#667eea", text=[f"{v}/10" for v in vals_a], textposition="auto"),
        go.Bar(name=title_b[:30], x=categories, y=vals_b, marker_color="#c77dff", text=[f"{v}/10" for v in vals_b], textposition="auto")
    ])
    
    fig.update_layout(
        barmode='group',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6e6ff", family="Inter"),
        legend=dict(
            font=dict(color="#e6e6ff", size=12),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            range=[0, 10],
            showgrid=True,
            gridcolor="rgba(130,130,220,0.13)",
            tickfont=dict(color="#8080aa", size=11),
        ),
        xaxis=dict(
            tickfont=dict(color="#e6e6ff", size=12),
        ),
        margin=dict(l=0, r=0, t=40, b=20),
        height=380,
    )
    st.plotly_chart(fig, width='stretch')


# ── Markdown export builder ───────────────────────────────────────────────────
def build_export_md(
    title: str, desc: str, domain: str,
    questions: list, answers: dict,
    transcript: str, summary: str,
    market: str, investor_text: str, scores: dict,
) -> str:
    now_str = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
    lines = [
        f"# IdeaCritic Report — {title}",
        f"> **Domain:** {domain} | **Generated:** {now_str}",
        "",
        "---",
        "## Idea Description",
        desc,
        "",
        "## Clarifying Q&A",
    ]
    for i, q in enumerate(questions, start=1):
        q_clean = re.sub(r"^\d+\.\s*", "", q)
        lines += [f"**Q{i}:** {q_clean}", f"**A:** {answers.get(f'Q{i}', 'Not answered.')}", ""]

    lines += [
        "---",
        "## Debate Transcript",
        transcript.strip(),
        "",
        "---",
        "## Business Analyst Summary",
        summary.strip(),
        "",
        "---",
        "## Market Intelligence (RAG-powered)",
        market.strip(),
        "",
        "---",
        "## Investor Evaluation",
        investor_text.strip(),
    ]
    if scores:
        weighted = scores.get("weighted_total", "N/A")
        verdict  = scores.get("verdict", "N/A")
        lines += [
            "",
            "### Score Breakdown",
            "| Dimension | Score |",
            "|-----------|-------|",
            f"| Market Potential | {scores.get('market_potential', 'N/A')}/10 |",
            f"| Innovation | {scores.get('innovation', 'N/A')}/10 |",
            f"| Scalability | {scores.get('scalability', 'N/A')}/10 |",
            f"| Team Feasibility | {scores.get('team_feasibility', 'N/A')}/10 |",
            f"| Risk | {scores.get('risk', 'N/A')}/10 |",
            f"| **Weighted Total** | **{weighted}/100** |",
            "",
            f"**Verdict: {verdict}**",
        ]
        recs = scores.get("recommendations", [])
        if recs:
            lines += ["", "### Next Steps"]
            for r in recs:
                lines.append(f"- {r}")

    return "\n".join(lines)


# ── PDF export builder ────────────────────────────────────────────────────────
def build_export_pdf(md_text: str) -> bytes:
    from fpdf import FPDF
    import markdown2
    
    html = markdown2.markdown(md_text)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    try:
        pdf.write_html(html)
    except Exception as e:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        pdf.multi_cell(0, 10, f"Error rendering PDF HTML: {e}\n\nFalling back to plain text:")
        pdf.multi_cell(0, 10, md_text.encode('latin-1', 'replace').decode('latin-1'))
        
    return pdf.output()
