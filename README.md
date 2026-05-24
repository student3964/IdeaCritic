## 🚀 IdeaCritic

Many ideas fail not because they are bad, but because they are never validated properly at an early stage. 

IdeaCritic is an AI-powered multi-agent idea evaluation system designed to help students, founders, and innovators critically analyze ideas before execution. It simulates expert-level discussions using AI agents and grounds feedback with real-world market data using structured debates, real-time market intelligence, and investor-style scoring.

## 📌 Project Overview

Traditional idea validation is subjective and often biased. IdeaCritic simulates a panel of multiple specialized AI agents that collaboratively analyze an idea from different perspectives.

The system:
- **Challenges assumptions** through multi-perspective debate.
- **Grounds feedback with real-world data (RAG)** to avoid hallucinations and outdated market research.
- **Produces actionable, investor-ready insights** and evaluates real-world viability.

## 🔄 System Workflow

1. **Describe Idea:** User enters an idea, title, and domain.
2. **Clarify:** The system generates clarifying questions; user answers them to narrow the scope.
3. **Multi-Agent Debate:** A structured, multi-round debate occurs between the Optimist, Critic, and Devil's Advocate agents.
4. **Business Analysis:** The Business Analyst synthesizes a balanced final summary.
5. **Market Intelligence:** The Market Analyst fetches real-world market data using RAG (Tavily).
6. **Investor Evaluation:** The Investor Bot evaluates the idea, generates a score (0-100), and gives a verdict.
7. **Pivot Suggestions:** If the idea scores poorly, the Pivot Suggester offers alternative business models.
8. **Export & Compare:** The complete analysis is stored in MongoDB. Users can export reports to Markdown/PDF or compare multiple ideas side-by-side.

## ✨ Key Features

- **Advanced Multi-Agent Debate System**
  - 🟢 **Optimist Agent** – highlights strengths and opportunities
  - 🔴 **Critic Agent** – identifies risks and weaknesses
  - 🟠 **Devil's Advocate** – challenges fundamental assumptions
  - ⚖️ **Business Analyst** – synthesizes a balanced summary
  - 🔄 **Pivot Suggester** – offers strategic pivots for low-scoring ideas

- **Market Analyst (RAG-powered)**
  - Fetches real-time competitor and market insights using Tavily API.

- **Investor Bot & Score Dashboard**
  - Scores ideas across 5 key dimensions (Market, Innovation, Scalability, Team, Risk).
  - Generates a final investment verdict.
  - Interactive UI with Plotly radar and bar charts.

- **Analysis History & Comparison**
  - View all past analyses backed by MongoDB.
  - Compare two different ideas side-by-side to see which is a better investment.

- **Exporting**
  - Download full reports as `.md` or `.pdf` files.

- **Resilient AI Infrastructure**
  - Primary LLM: **Google Gemini (3.1 Pro / 2.5 Flash)**
  - Fallback LLM: **Groq (LLaMA 3.1 8B)** for zero-downtime during rate limits.

## 🏗️ Tech Stack

### AI & LLMs
- **Primary Model:** Google Gemini API
- **Fallback Model:** Groq API (LLaMA 3)
- **Framework:** Custom Streamlit streaming architecture

### Backend & UI
- **Frontend:** Streamlit (Multi-page app)
- **Data Viz:** Plotly (Radar & Bar charts)
- **Language:** Python 3.9+

### RAG & Market Intelligence
- **Search:** Tavily API for real-time market data retrieval

### Database
- **Storage:** MongoDB (analysis storage and caching)

## 🛠️ How to Run the Project

**Prerequisites:**
- Python 3.9+
- MongoDB instance (local or Atlas)

**API Keys Required in `.env`:**
- `GEMINI_API_KEY`
- `GROQ_API_KEY` (Optional, for fallback)
- `TAVILY_API_KEY`
- `MONGO_URI`

```bash
# Clone the repository
git clone https://github.com/student3964/ideacritic-pbl-sem6.git
cd ideacritic-pbl-sem6

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```
