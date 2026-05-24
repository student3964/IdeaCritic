"""
IdeaCritic — Database helpers (MongoDB)
"""
import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGO_CONNECTION_STRING


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


mongo_client       = init_mongo()
_db                = mongo_client["ideacritic_db"]
debates_collection = _db["debates"]
market_cache_col   = _db["market_cache"]
