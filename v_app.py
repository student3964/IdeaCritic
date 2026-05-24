"""
IdeaCritic — Enhanced Version
Improvements over v1:
 - Premium dark UI with custom CSS & agent-colored cards
 - Visual step-progress indicator
 - Domain / industry tagging
 - 3-agent debate: Optimist · Critic · Devil's Advocate
 - 24-hour TTL on Tavily market cache
 - Investor score parsing → Plotly bar chart + color-coded verdict badge
 - Structured score storage in MongoDB
 - History: keyword search, domain filter, delete with confirmation
 - Export full report as Markdown download
"""

import os
import re
import datetime
import requests
from dotenv import load_dotenv

import streamlit as st
from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from google import genai

try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

# ── Env ────────────────────────────────────────────────────────────────────────
load_dotenv()
GOOGLE_API_KEY          = os.getenv("GOOGLE_API_KEY")
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
TAVILY_API_KEY          = os.getenv("TAVILY_API_KEY")

DOMAINS = [
    "HealthTech", "EdTech", "FinTech", "CleanTech / Climate",
    "B2B SaaS", "Consumer App", "DeepTech / AI",
    "E-commerce", "AgriTech", "LegalTech", "Other",
]

MARKET_CACHE_TTL_HOURS = 24

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="IdeaCritic", page_icon="🚀", layout="wide")

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Tokens ── */
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

/* ── Global ── */
.stApp { background: var(--bg) !important; font-family: 'Inter', sans-serif !important; }
.stApp * { color: var(--text); }
html, body { background: var(--bg) !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Headings ── */
h1 {
  background: linear-gradient(135deg, #667eea 0%, #c77dff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  letter-spacing: -0.02em;
}
h2, h3, h4 { color: var(--text) !important; font-weight: 700; }

/* ── Buttons ── */
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

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
  background: linear-gradient(135deg, #11998e, #38ef7d) !important;
  color: #000 !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
}

/* ── Inputs / selects ── */
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

/* ── Slider ── */
.stSlider [data-baseweb="slider"] { color: var(--accent) !important; }

/* ── Metrics ── */
[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1rem 1.25rem;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.8rem; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700; }

/* ── Divider ── */
hr { border-color: var(--border) !important; opacity: 1 !important; }

/* ── Expanders ── */
summary {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 0.5rem 1rem !important;
}

/* ── Alert / info ── */
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

/* ── Domain pill ── */
.domain-pill {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  background: rgba(102,126,234,0.15);
  border: 1px solid rgba(102,126,234,0.3);
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent);
  margin-left: 0.5rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)


# ── Init Gemini ────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"

@st.cache_resource
def init_gemini():
    if not GOOGLE_API_KEY:
        st.error("GOOGLE_API_KEY missing in .env.")
        st.stop()
    try:
        return genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        st.stop()


# ── Init MongoDB ───────────────────────────────────────────────────────────────
@st.cache_resource
def init_mongo():
    if not MONGO_CONNECTION_STRING:
        st.error("MONGO_CONNECTION_STRING missing in .env.")
        st.stop()
    try:
        client = MongoClient(MONGO_CONNECTION_STRING, server_api=ServerApi("1"))
        client.admin.command("ping")
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        st.stop()


gemini_client = init_gemini()
mongo_client  = init_mongo()
db = mongo_client["ideacritic_db"]
debates_collection = db["debates"]
market_cache_col   = db["market_cache"]


# ── Stepper ────────────────────────────────────────────────────────────────────
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


# ── Agent label ────────────────────────────────────────────────────────────────
_LABEL_CSS = {
    "Optimist":         ("🟢", "lbl-optimist"),
    "Critic":           ("🔴", "lbl-critic"),
    "Devil's Advocate": ("🟠", "lbl-devils"),
    "Business Analyst": ("🔵", "lbl-analyst"),
    "Market Analyst":   ("🟣", "lbl-market"),
    "Investor":         ("💛", "lbl-investor"),
}

def agent_label(persona: str):
    emoji, css = _LABEL_CSS.get(persona, ("💬", "lbl-analyst"))
    st.markdown(
        f'<div class="agent-lbl {css}">{emoji} {persona}</div>',
        unsafe_allow_html=True,
    )


# ── RAG: Tavily with 24-hour TTL ───────────────────────────────────────────────
def fetch_market_trends(query: str, max_results: int = 5) -> str:
    if not TAVILY_API_KEY:
        return "⚠️ TAVILY_API_KEY missing in .env — cannot fetch real-time market data."

    now = datetime.datetime.now(datetime.timezone.utc)
    cached = market_cache_col.find_one({"query": query})
    if cached:
        age_hours = (now - cached.get("fetched_at", now)).total_seconds() / 3600
        if age_hours < MARKET_CACHE_TTL_HOURS:
            return cached.get("results", "")
        market_cache_col.delete_one({"_id": cached["_id"]})  # stale — purge

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {TAVILY_API_KEY}"},
            json={"query": query, "num_results": max_results},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        snippets = [r.get("content", "") for r in data.get("results", []) if r.get("content")]
        combined = "\n\n".join(snippets[:max_results])
        market_cache_col.insert_one({"query": query, "results": combined, "fetched_at": now})
        return combined
    except Exception as e:
        return f"Error fetching market data: {e}"


# ── Streaming wrapper ──────────────────────────────────────────────────────────
def stream_generator(prompt: str):
    try:
        for chunk in gemini_client.models.generate_content_stream(
            model=GEMINI_MODEL, contents=prompt
        ):
            if getattr(chunk, "text", None):
                yield chunk.text
    except Exception as e:
        yield f"[Model Error] {e}"


# ── Agent prompts ──────────────────────────────────────────────────────────────
def get_agent_response(persona: str, idea: str, last_statement: str = "") -> str:
    """Returns a generator of text chunks for the given persona."""

    if persona == "Market Analyst":
        query = f"Market trends, competitors, funding, pricing for: {idea[:280]}"
        market_data = fetch_market_trends(query)
        prompt = f"""You are a Market Analyst. Use the following real-time data to produce an evidence-backed report.

Startup Idea:
{idea}

Retrieved Market Data (RAG):
{market_data}

Deliver:
- A 3–5 sentence evidence-based market summary
- Key competitor and funding/traction signals
- Market growth or saturation assessment
- Go-to-market and pricing cues

Be factual, concise, and cite any numbers from the data."""
        return stream_generator(prompt)

    if persona == "Investor":
        prompt = f"""You are an experienced early-stage investor. Evaluate the following startup idea.

Startup Idea:
{idea}

Respond EXACTLY in this format (no extra text before or after):
Market Potential: <score 0-10> — <one-line justification>
Innovation: <score 0-10> — <one-line justification>
Scalability: <score 0-10> — <one-line justification>
Team Feasibility: <score 0-10> — <one-line justification>
Risk: <score 0-10> — <one-line justification (10=very low risk, 0=very high risk)>
Weighted Score (0-100): <integer>
Verdict: <exactly one of: Strong Buy | Consider with Caution | Not Investable Yet>
Recommendations:
1. <recommendation>
2. <recommendation>
3. <recommendation>

Scoring weights: Market Potential 30%, Innovation 25%, Scalability 20%, Team Feasibility 15%, Risk 10%"""
        return stream_generator(prompt)

    base_prompts = {
        "Optimist": (
            "You are a passionate startup Optimist on an expert panel. "
            "Highlight the most compelling strengths, market opportunities, and early traction signals. "
            "Be enthusiastic but specific and data-grounded. Output exactly 3 bullet points."
        ),
        "Critic": (
            "You are a hard-nosed startup Critic on an expert panel. "
            "Identify the most serious structural risks, competitive threats, and execution challenges. "
            "Be rigorous and direct. Output exactly 3 bullet points."
        ),
        "Devil's Advocate": (
            "You are a Devil's Advocate on a startup evaluation panel. "
            "Challenge the core assumptions made by both the Optimist and the Critic. "
            "Raise the single most overlooked risk or the most contrarian valid perspective neither has addressed. "
            "Be bold but logical. Output exactly 2–3 bullet points."
        ),
        "Business Analyst": (
            "You are an expert Business Analyst. Synthesize the debate and provide a balanced, "
            "actionable assessment for the founder."
        ),
    }

    base = base_prompts.get(persona, f"You are a startup {persona}.")
    if last_statement:
        prompt = (
            f"{base}\n\n"
            f"Startup idea:\n{idea}\n\n"
            f"Previous panelist statement (respond to this directly):\n{last_statement}"
        )
    else:
        prompt = f"{base}\n\nStartup idea:\n{idea}"

    return stream_generator(prompt)


# ── Summary ────────────────────────────────────────────────────────────────────
def get_summary(idea: str, transcript: str):
    prompt = f"""You are an expert Business Analyst. Based on this debate transcript for the idea '{idea}':

Write:
1. A short, actionable paragraph (3–4 sentences) synthesizing the key insights from the debate.
2. Exactly 3 concise, actionable bullet points the founder should act on immediately.

Transcript:
{transcript}"""
    return stream_generator(prompt)


# ── Clarifying questions ───────────────────────────────────────────────────────
@st.cache_data
def generate_clarifying_questions(title: str, desc: str):
    prompt = f"""You are a seasoned startup mentor. For this idea:
Title: {title}
Description: {desc}

Generate exactly 4 clarifying questions as a numbered list:
1. <question>
2. <question>
3. <question>
4. <question>

Focus areas: target market segment, key differentiator, revenue/business model, biggest execution risk.
Output ONLY the numbered list, no extra text."""
    try:
        r = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        lines = [l.strip() for l in r.text.strip().splitlines() if re.match(r"^\d+\.", l.strip())]
        return lines if lines else [r.text.strip()]
    except Exception as e:
        return [f"Error generating questions: {e}"]


# ── Investor output parser ─────────────────────────────────────────────────────
def parse_investor_output(text: str) -> dict:
    patterns = {
        "market_potential": r"Market Potential:\s*([\d.]+)",
        "innovation":       r"Innovation:\s*([\d.]+)",
        "scalability":      r"Scalability:\s*([\d.]+)",
        "team_feasibility": r"Team Feasibility:\s*([\d.]+)",
        "risk":             r"Risk:\s*([\d.]+)",
        "weighted_total":   r"Weighted Score \(0-100\):\s*([\d.]+)",
    }
    scores: dict = {}
    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            scores[key] = float(m.group(1))

    verdict_m = re.search(r"Verdict:\s*(.+)", text, re.IGNORECASE)
    scores["verdict"] = verdict_m.group(1).strip() if verdict_m else "N/A"

    recs = re.findall(r"^\s*\d+\.\s+(.+)", text, re.MULTILINE)
    scores["recommendations"] = recs[:3]
    return scores


# ── Score dashboard ────────────────────────────────────────────────────────────
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
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback: progress-bar style
            labels = ["Market Potential", "Innovation", "Scalability", "Team Feasibility", "Risk"]
            keys   = ["market_potential", "innovation", "scalability", "team_feasibility", "risk"]
            for label, key in zip(labels, keys):
                val = scores.get(key, 0)
                st.markdown(f"**{label}**: {val}/10")
                st.progress(val / 10)


# ── Render a streaming agent turn ─────────────────────────────────────────────
def render_agent_turn(persona: str, generator) -> str:
    agent_label(persona)
    placeholder = st.empty()
    response = ""
    for chunk in generator:
        response += chunk
        placeholder.markdown(response)
    return response


# ── Markdown export builder ────────────────────────────────────────────────────
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
            f"| Dimension | Score |",
            f"|-----------|-------|",
            f"| Market Potential | {scores.get('market_potential', 'N/A')}/10 |",
            f"| Innovation | {scores.get('innovation', 'N/A')}/10 |",
            f"| Scalability | {scores.get('scalability', 'N/A')}/10 |",
            f"| Team Feasibility | {scores.get('team_feasibility', 'N/A')}/10 |",
            f"| Risk | {scores.get('risk', 'N/A')}/10 |",
            f"| **Weighted Total** | **{weighted}/100** |",
            f"",
            f"**Verdict: {verdict}**",
        ]
        recs = scores.get("recommendations", [])
        if recs:
            lines += ["", "### Next Steps"]
            for r in recs:
                lines.append(f"- {r}")

    return "\n".join(lines)


# ── New Analysis page ──────────────────────────────────────────────────────────
def show_new_analysis_page():
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
                    st.session_state["idea_domain"] = domain
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
            st.caption("Runs 3 debate agents (Optimist · Critic · Devil's Advocate), Business Analyst, Market Analyst, and Investor Bot.")
        with col_r:
            num_rounds = st.slider("Debate rounds", 1, 5, 2)

        if st.button("🚀 Start Full Analysis", type="primary"):
            render_stepper(2)

            # Build full context
            context = st.session_state["idea_desc"] + "\n\n--- Founder Clarifications ---\n"
            for i, q in enumerate(st.session_state["clarifying_questions"], start=1):
                q_clean = re.sub(r"^\d+\.\s*", "", q)
                ans = st.session_state["answers"].get(f"Q{i}", "Not answered.")
                context += f"Q: {q_clean}\nA: {ans}\n"

            db_log     = ""
            transcript = ""
            last_resp  = ""

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
                            get_agent_response(persona, context, last_resp),
                        )
                    entry = f"\nRound {r + 1} — {persona}:\n{resp}"
                    db_log     += entry
                    transcript += entry
                    last_resp   = resp
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
                    "scores":            scores,
                    "created_at":        datetime.datetime.now(datetime.timezone.utc),
                }
                res = debates_collection.insert_one(doc)
                st.success(f"💾 Analysis saved to archive! (ID: `{res.inserted_id}`)")
            except Exception as e:
                st.error(f"Failed to save analysis: {e}")

            # ── Export ────────────────────────────────────────────────────────
            report_md = build_export_md(
                st.session_state.get("idea_title", "Idea"),
                st.session_state.get("idea_desc", ""),
                st.session_state.get("idea_domain", "Other"),
                st.session_state.get("clarifying_questions", []),
                st.session_state.get("answers", {}),
                db_log,
                final_summary,
                market_insight,
                investor_output,
                scores,
            )
            safe_name = re.sub(r"[^\w]", "_", st.session_state.get("idea_title", "report")).lower()
            st.download_button(
                "📄 Download Full Report (.md)",
                data=report_md,
                file_name=f"ideacritic_{safe_name}.md",
                mime="text/markdown",
            )


# ── History page ───────────────────────────────────────────────────────────────
def show_history_page(all_analyses: list):
    st.title("📚 Analysis Archive")

    if not all_analyses:
        st.info("Your archive is empty. Complete your first idea analysis to see it here.")
        return

    total  = len(all_analyses)
    latest = all_analyses[0].get("created_at")
    domains_set = {a.get("idea_domain", "Other") for a in all_analyses}

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Analyses", total)
    m2.metric("Most Recent", latest.strftime("%b %d, %Y") if latest else "—")
    m3.metric("Domains Covered", len(domains_set))
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

        # Build expander header
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
                st.plotly_chart(fig, use_container_width=True)

            # Investor full output
            with st.expander("💼 Full Investor Output"):
                st.text(analysis.get("investor_output", "—"))

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


# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🚀 IdeaCritic")
st.sidebar.markdown(
    "<p style='color:#8080aa;font-size:0.8rem;margin-top:-0.5rem'>"
    "AI-powered multi-agent idea validation</p>",
    unsafe_allow_html=True,
)
st.sidebar.divider()

def _on_page_change():
    if st.session_state.get("radio_nav") == "New Analysis":
        for k in ["clarifying_questions", "idea_title", "idea_desc", "answers", "idea_domain"]:
            st.session_state.pop(k, None)

selected = st.sidebar.radio(
    "Navigation",
    ["New Analysis", "Analysis History"],
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
    "Tavily RAG · MongoDB · Plotly<br>"
    "© IdeaCritic 2025"
    "</small>",
    unsafe_allow_html=True,
)

# ── Routing ────────────────────────────────────────────────────────────────────
if selected == "New Analysis":
    show_new_analysis_page()
else:
    all_docs = list(debates_collection.find().sort("created_at", DESCENDING))
    show_history_page(all_docs)
