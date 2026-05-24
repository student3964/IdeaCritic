"""
IdeaCritic — Configuration & Constants
"""
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY          = os.getenv("GOOGLE_API_KEY")
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
TAVILY_API_KEY          = os.getenv("TAVILY_API_KEY")
GROQ_API_KEY            = os.getenv("GROQ_API_KEY")

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL   = "llama-3.1-8b-instant"  # Fast & free on Groq

MARKET_CACHE_TTL_HOURS = 24

DOMAINS = [
    "HealthTech", "EdTech", "FinTech", "CleanTech / Climate",
    "B2B SaaS", "Consumer App", "DeepTech / AI",
    "E-commerce", "AgriTech", "LegalTech", "Other",
]
