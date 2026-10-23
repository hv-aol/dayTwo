import streamlit as st
from auth import render_login
from config import init_metadata_store, get_database_schema
from views.chat_view import render_chat_view
from views.dashboard_view import render_dashboard_view

# Page Configuration
st.set_page_config(
    page_title="Mini-Metabase (Auth & Shared Dashboards)",
    page_icon="📊",
    layout="wide"
)

# Initialize Metadata Store
init_metadata_store()

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
    app_mode = st.sidebar.radio("Navigation", ["💬 NLP Query & Chat", "📊 Dashboards"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.messages = []
        st.rerun()

    # Main Entry Header
    st.title("📊 Mini-Metabase (Qwen + OpenRouter)")

    # Retrieve schema info
    schema_info = get_database_schema()

    # Route Views
    if app_mode == "💬 NLP Query & Chat":
        render_chat_view(openrouter_api_key, schema_info, st.session_state.username)
    elif app_mode == "📊 Dashboards":
        render_dashboard_view(st.session_state.username)