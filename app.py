import streamlit as st
import logging
from dotenv import load_dotenv
load_dotenv(".secrets/.env") # this sets db config. Lets work on decrypting the password.

from auth import render_login
from config import init_metadata_store, get_database_schema
from views.chat_view import render_chat_view
from views.dashboard_view import render_dashboard_view
from views.template_view import render_template_view
from logger.app_logger import setup_logging


# Page Configuration
st.set_page_config(
    page_title="Mini-Metabase (Auth & Shared Dashboards)",
    page_icon="📊",
    layout="wide"
)

# Initialize Metadata Store
init_metadata_store()
setup_logging()

logger = logging.getLogger(__name__)

# State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Authentication Gate
if not st.session_state.authenticated:
    render_login()
else:
    # Sidebar Navigation & Settings
    st.sidebar.title(f"👤 Logged in as: `{st.session_state.username}`")
    # openrouter_api_key = st.sidebar.text_input("OpenRouter API Key", type="password", placeholder="sk-or-...")
    app_mode = st.sidebar.radio("Navigation", ["💬 NLP Query & Chat", "📊 Dashboards", "📋 Standard Reports"])
    
    st.sidebar.markdown("---")
    # Context-aware sidebar action: Clear chat history button when in chat mode
    if app_mode == "💬 NLP Query & Chat":
        if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.success("Chat history cleared!")
            st.rerun()
        st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.messages = []
        st.rerun()

    # Main Entry Header
    st.title("📊 Mini-Metabase Roadster")

    # Retrieve schema info
    schema_info = get_database_schema()

    # Route Views
    if app_mode == "💬 NLP Query & Chat":
        render_chat_view(st.session_state.username)
    elif app_mode == "📊 Dashboards":
        render_dashboard_view(st.session_state.username)
    else:
        render_template_view()