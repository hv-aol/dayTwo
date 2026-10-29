import streamlit as st
from bcrypt_auth import verify_user

def render_login():
    """Renders user login form."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Mini-Metabase Login")
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Log In", use_container_width=True)
            
            if submit_button:
                if verify_user(username_input, password_input):
                    st.session_state.authenticated = True
                    st.session_state.username = username_input
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        
        st.info("💡 **Demo Credentials:** `alice` / `password123` or `bob` / `securepass`")
