"""
IdeaCritic — RAG: Tavily search with 24-hour TTL caching
"""
import datetime
import requests
from config import TAVILY_API_KEY, MARKET_CACHE_TTL_HOURS
from db import market_cache_col


def fetch_market_trends(query: str, max_results: int = 5) -> str:
    """Query Tavily and return concatenated snippets. Caches in MongoDB with TTL."""
    if not TAVILY_API_KEY:
        return "⚠️ TAVILY_API_KEY missing in .env — cannot fetch real-time market data."

    now = datetime.datetime.now(datetime.timezone.utc)
    cached = market_cache_col.find_one({"query": query})
    if cached:
        fetched_at = cached.get("fetched_at", now)
        # Ensure timezone-aware comparison (MongoDB may store naive datetimes)
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=datetime.timezone.utc)
        age_hours = (now - fetched_at).total_seconds() / 3600
        if age_hours < MARKET_CACHE_TTL_HOURS:
            return cached.get("results", "")
        market_cache_col.delete_one({"_id": cached["_id"]})

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
