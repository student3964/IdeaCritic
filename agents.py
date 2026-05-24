"""
IdeaCritic — Agents: All LLM prompting, streaming, clarifying questions, parsing.
Uses string-based memory for coherent multi-round debates.
Supports Gemini as primary LLM with Groq (LLaMA) as automatic fallback.
"""
import re
import time
import streamlit as st
from google import genai
from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
from rag import fetch_market_trends


# ── Gemini client ──────────────────────────────────────────────────────────────
@st.cache_resource
def _init_gemini():
    if not GOOGLE_API_KEY:
        st.error("GOOGLE_API_KEY missing in .env.")
        st.stop()
    try:
        return genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        st.stop()

gemini_client = _init_gemini()


# ── Groq fallback client ──────────────────────────────────────────────────────
@st.cache_resource
def _init_groq():
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except ImportError:
        st.warning("groq package not installed. Fallback disabled. Run: pip install groq")
        return None
    except Exception as e:
        st.warning(f"Groq init failed: {e}. Fallback disabled.")
        return None

groq_client = _init_groq()


# ── Groq streaming helper ────────────────────────────────────────────────────
def _groq_stream(prompt: str):
    """Stream text chunks from Groq API (LLaMA 3.1)."""
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=2048,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except Exception as e:
        yield f"\n\n[Groq Error] {e}"


def _groq_generate(prompt: str) -> str:
    """Non-streaming Groq call for clarifying questions."""
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Groq Error] {e}"


# ── Streaming wrapper with fallback ──────────────────────────────────────────
def stream_generator(prompt: str, max_retries: int = 2):
    """Yield text chunks from Gemini with automatic Groq fallback on failure."""
    retries = 0
    while retries <= max_retries:
        try:
            for chunk in gemini_client.models.generate_content_stream(
                model=GEMINI_MODEL, contents=prompt
            ):
                if getattr(chunk, "text", None):
                    yield chunk.text
            return  # Success, exit loop
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                retries += 1
                if retries <= max_retries:
                    time.sleep(5 * retries)
                    continue
            # All retries exhausted or non-rate-limit error — try Groq
            if groq_client:
                yield from _groq_stream(prompt)
                return
            yield f"[Model Error] {e}"
            return

    # If we exit the while loop (all retries exhausted), try Groq
    if groq_client:
        yield from _groq_stream(prompt)
    else:
        yield f"\n\n[Error] Gemini rate limit exceeded and no Groq fallback configured. Add GROQ_API_KEY to .env."


# ── Clarifying questions ──────────────────────────────────────────────────────
@st.cache_data
def generate_clarifying_questions(title: str, desc: str) -> list[str]:
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
    retries = 0
    while retries <= 2:
        try:
            r = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            lines = [l.strip() for l in r.text.strip().splitlines() if re.match(r"^\d+\.", l.strip())]
            return lines if lines else [r.text.strip()]
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                retries += 1
                if retries <= 2:
                    time.sleep(5 * retries)
                    continue
            # Fallback to Groq
            if groq_client:
                text = _groq_generate(prompt)
                lines = [l.strip() for l in text.strip().splitlines() if re.match(r"^\d+\.", l.strip())]
                return lines if lines else [text.strip()]
            return [f"Error generating questions: {e}"]

    # All retries exhausted — try Groq
    if groq_client:
        text = _groq_generate(prompt)
        lines = [l.strip() for l in text.strip().splitlines() if re.match(r"^\d+\.", l.strip())]
        return lines if lines else [text.strip()]
    return ["Error: Rate limit exceeded and no Groq fallback configured."]


# ── Agent prompts ─────────────────────────────────────────────────────────────
_PERSONA_PROMPTS = {
    "Optimist": (
        "You are a passionate startup **Optimist** on an expert panel.\n"
        "Highlight the most compelling strengths, market opportunities, and early traction signals.\n"
        "Be enthusiastic but specific and data-grounded.\n"
        "**Bold** key phrases, metrics, and insight headlines.\n"
        "Output exactly 3 bullet points using markdown bullet syntax (- )."
    ),
    "Critic": (
        "You are a hard-nosed startup **Critic** on an expert panel.\n"
        "Identify the most serious structural risks, competitive threats, and execution challenges.\n"
        "Be rigorous and direct.\n"
        "**Bold** key phrases, risk labels, and critical data points.\n"
        "Output exactly 3 bullet points using markdown bullet syntax (- )."
    ),
    "Devil's Advocate": (
        "You are a **Devil's Advocate** on a startup evaluation panel.\n"
        "Challenge the core assumptions made by both the Optimist and the Critic.\n"
        "Raise the single most overlooked risk or the most contrarian valid perspective neither has addressed.\n"
        "Be bold but logical.\n"
        "**Bold** key phrases and contrarian insights.\n"
        "Output exactly 2–3 bullet points using markdown bullet syntax (- )."
    ),
    "Business Analyst": (
        "You are an expert **Business Analyst**. Synthesize the debate and provide a balanced, "
        "actionable assessment for the founder.\n"
        "**Bold** key conclusions and action items."
    ),
}


def get_agent_response(
    persona: str,
    idea: str,
    history_context: str = "",
    last_statement: str = "",
):
    """Returns a generator of text chunks for the given persona."""

    # ── Market Analyst (RAG) ──
    if persona == "Market Analyst":
        query = f"Market trends, competitors, funding, pricing for: {idea[:280]}"
        market_data = fetch_market_trends(query)
        prompt = f"""You are a **Market Analyst**. Use the following real-time data to produce an evidence-backed report.

Startup Idea:
{idea}

Retrieved Market Data (RAG):
{market_data}

Format your response with clear **bold section headers** and use markdown:

**📈 Market Summary**
3–5 sentences with evidence-based market assessment. **Bold** key numbers and market size figures.

**🏢 Competitor & Funding Signals**
IMPORTANT: You MUST wrap any real, named market competitor in this exact HTML tag to highlight them: 
<span style='color: #ff4757; font-weight: bold; background: rgba(255,71,87,0.15); padding: 2px 6px; border-radius: 4px;'>Competitor Name</span>
List funding rounds and traction indicators as bullet points.

**📊 Growth vs Saturation**
Is the market growing or saturated? **Bold** the verdict.

**🎯 Go-to-Market & Pricing Cues**
Actionable GTM and pricing insights as bullet points.

Be factual, concise, and cite any numbers from the data."""
        return stream_generator(prompt)

    # ── Investor ──
    if persona == "Investor":
        prompt = f"""You are an experienced early-stage investor. Evaluate the following startup idea.

Startup Idea:
{idea}

Respond EXACTLY in this format. Use a NEW LINE for each score. Do NOT combine scores on one line:

**Market Potential:** <score 0-10> — <one-line justification>

**Innovation:** <score 0-10> — <one-line justification>

**Scalability:** <score 0-10> — <one-line justification>

**Team Feasibility:** <score 0-10> — <one-line justification>

**Risk:** <score 0-10> — <one-line justification (10=very low risk, 0=very high risk)>

---

**Weighted Score (0-100):** <integer>

**Verdict:** <exactly one of: Strong Buy | Consider with Caution | Not Investable Yet>

---

**Recommendations:**
1. <recommendation>
2. <recommendation>
3. <recommendation>

Scoring weights: Market Potential 30%, Innovation 25%, Scalability 20%, Team Feasibility 15%, Risk 10%"""
        return stream_generator(prompt)

    # ── Pivot Suggester ──
    if persona == "Pivot Suggester":
        prompt = f"""You are a **Pivot Strategist**. The following startup idea received a cautious or negative investor evaluation.

Startup Idea & Analysis Context:
{idea}

Previous critical feedback:
{last_statement}

Based on the harshest criticisms and the lowest-scoring dimensions, suggest exactly 3 concrete, actionable **pivot directions** the founder could explore.

For each pivot:
- **Bold the pivot name** (e.g., "**Pivot 1: B2B SaaS Model**")
- Explain in 2–3 sentences why this pivot addresses the specific weaknesses identified
- Mention what stays the same vs. what changes

Be creative, specific, and practical. Use markdown formatting."""
        return stream_generator(prompt)

    # ── Default debate agents ──
    base = _PERSONA_PROMPTS.get(persona, f"You are a startup {persona}.")

    if history_context and last_statement:
        prompt = (
            f"{base}\n\n"
            f"Startup idea:\n{idea}\n\n"
            f"Full debate history so far:\n{history_context}\n\n"
            f"Most recent panelist statement (respond to this directly):\n{last_statement}"
        )
    elif last_statement:
        prompt = (
            f"{base}\n\n"
            f"Startup idea:\n{idea}\n\n"
            f"Previous panelist statement (respond to this directly):\n{last_statement}"
        )
    else:
        prompt = f"{base}\n\nStartup idea:\n{idea}"

    return stream_generator(prompt)


# ── Summary ───────────────────────────────────────────────────────────────────
def get_summary(idea: str, transcript: str):
    prompt = f"""You are an expert **Business Analyst**. Based on this debate transcript for the idea:

{idea}

Write:
1. A short, actionable paragraph (3–4 sentences) synthesizing the key insights. **Bold** the most important conclusions.
2. Exactly 3 concise, actionable bullet points the founder should act on immediately. **Bold** the action verb at the start of each.

Transcript:
{transcript}"""
    return stream_generator(prompt)


# ── Investor output parser ────────────────────────────────────────────────────
def parse_investor_output(text: str) -> dict:
    """Extract structured scores from investor text output."""
    patterns = {
        "market_potential": r"Market Potential[:\*]*\s*([\d.]+)",
        "innovation":       r"Innovation[:\*]*\s*([\d.]+)",
        "scalability":      r"Scalability[:\*]*\s*([\d.]+)",
        "team_feasibility": r"Team Feasibility[:\*]*\s*([\d.]+)",
        "risk":             r"Risk[:\*]*\s*([\d.]+)",
        "weighted_total":   r"Weighted Score[^:]*[:\*]*\s*([\d.]+)",
    }
    scores: dict = {}
    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            scores[key] = float(m.group(1))

    verdict_m = re.search(r"Verdict[:\*]*\s*(.+)", text, re.IGNORECASE)
    scores["verdict"] = verdict_m.group(1).strip().strip("*") if verdict_m else "N/A"

    # Get recommendations (skip the score lines that also match "N." pattern)
    recs = []
    in_recs = False
    for line in text.splitlines():
        line_s = line.strip()
        if re.match(r"(?i)\*{0,2}recommendations", line_s):
            in_recs = True
            continue
        if in_recs and re.match(r"^\d+\.\s+(.+)", line_s):
            recs.append(re.match(r"^\d+\.\s+(.+)", line_s).group(1))
    scores["recommendations"] = recs[:3]
    return scores
