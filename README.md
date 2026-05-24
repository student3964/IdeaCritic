## 🚀 IdeaCritic


Many ideas fail not because they are bad, but because they are never validated properly at an early stage. 

IdeaCritic is an AI-powered multi-agent idea evaluation system designed to help students, founders, and innovators critically analyze ideas before execution. It simulates expert-level discussions using AI agents and grounds feedback with real-world market data using structured debates, real-time market intelligence, and investor-style scoring.

## 📌 Project Overview

Traditional idea validation is subjective and often biased.
IdeaCritic simulates a panel of multiple specialized AI agents that collaboratively analyze an idea from different perspectives.

The system:

Challenges assumptions

Grounds feedback with real-world data (RAG) so to avoid limited or outdated market research

Produces actionable, investor-ready insights & evaluates its real-world viability

## 🔄 System Workflow

1. User enters an idea
2. The system generates clarifying questions
3. User answers the clarifying questions
4. Multi-round debate between Optimist and Critic agents
5. Business Analyst synthesizes a balanced final summary
6. Market Analyst fetches real-world market data using RAG
7. Investor Bot evaluates the idea and generates a score with recommendations
8. The complete analysis is stored and can be revisited later

## ✨ Key Features

- **Multi-Agent Debate System**
  - 🟢 **Optimist Agent** – highlights strengths and opportunities
  - 🔴 **Critic Agent** – identifies risks and weaknesses
  - ⚖️ **Business Analyst** – synthesizes a balanced summary

- **Market Analyst (RAG-powered)**
  - Fetches real-time competition and market insights 

- **Investor Bot**
  - Scores ideas across key evaluation dimensions
  - Generates a final investment verdict (0–100 score)

- **Clarifying Questions**
  - Improves idea clarity and quality before evaluation

- **Analysis History**
  - Stores past idea evaluations using MongoDB

 ## 🏗️ Tech Stack

### AI & LLMs
- Google Gemini (Gemini 2.5 Flash / Gemma-based reasoning)
- LangChain (agent orchestration)

### Backend & UI
- Streamlit (full-stack application)
- Python

### RAG & Market Intelligence
- Tavily Search API / Serper.dev API for real-time market data retrieval

### Database
- MongoDB (analysis storage and caching)

### Utilities
- pandas
- numpy

## 🎥 Demo Video (Running Module)

- 📽️ **Project Walkthrough Video**
- 👉 [Click here to watch the demo](https://drive.google.com/file/d/1NuGf4yaD0dDeyH-p_7VZ235TchN9VV2-/view?usp=sharing)

## 🛠️ How to Run the Project

Prerequisites

- Python 3.9+
- MongoDB
API Keys:
- Google Gemini API
- Tavily API

```bash
# Clone the repository
git clone https://github.com/student3964/IdeaCritic.git
cd IdeaCritic

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run v_app.py



