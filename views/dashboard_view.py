import pandas as pd
import streamlit as st
from config import get_db_connection, get_all_dashboards, delete_dashboard_card

def render_dashboard_view(username: str):
    """Renders System Defaults, Team Shared cards, and Personal cards using tabs."""
    st.subheader(f"📊 Dashboard Overview ({username.capitalize()}'s Workspace)")
    
    cards_df = get_all_dashboards()
    if cards_df.empty:
        st.info("No dashboards found.")
        return

    # Categorize cards
    system_cards = cards_df[cards_df["is_system"] == 1]
    team_cards = cards_df[(cards_df["is_system"] == 0) & (cards_df["is_public"] == 1) & (cards_df["username"] != username)]
    personal_cards = cards_df[(cards_df["is_system"] == 0) & (cards_df["username"] == username)]

    tab1, tab2, tab3 = st.tabs(["🌐 System Defaults", "👥 Team Shared Dashboards", "📁 My Personal Dashboards"])

    with tab1:
        st.markdown("### System Default Dashboards")
        if system_cards.empty:
            st.write("No system defaults available.")
        else:
            for _, card in system_cards.iterrows():
                render_card(card, is_deletable=False, username=username)

    with tab2:
        st.markdown("### Public Dashboards Shared by Team")
        if team_cards.empty:
            st.info("No shared team dashboards available yet. Check the public toggle when pinning a query to share it here!")
        else:
            for _, card in team_cards.iterrows():
                st.caption(f"Shared by: `{card['username']}`")
                render_card(card, is_deletable=False, username=username)

    with tab3:
        st.markdown(f"### My Personal Dashboards ({username})")
        if personal_cards.empty:
            st.info("You haven't pinned any custom cards yet! Head over to **NLP Query & Chat** to create one.")
        else:
            for _, card in personal_cards.iterrows():
                visibility = "🌐 Public (Team Shared)" if card["is_public"] == 1 else "🔒 Private"
                st.caption(f"Status: {visibility}")
                render_card(card, is_deletable=True, username=username)

def render_card(card, is_deletable: bool, username: str):
    """Helper to render individual card charts and data grids."""
    with st.container():
        st.markdown(f"Question:")
        st.code(card["sql_query"], language="sql")
        
        try:
            conn = get_db_connection()
            df = pd.read_sql(card["sql_query"], conn)
            conn.close()
            
            st.dataframe(df, use_container_width=True)
            if len(df.columns) >= 2:
                st.bar_chart(df.set_index(df.columns[0]))
        except Exception as e:
            st.error(f"Error executing card query: {e}")
            
        if is_deletable:
            if st.button(f"🗑️ Delete Card", key=f"del_{card['id']}"):
                delete_dashboard_card(card["id"], username)
                st.success("Card deleted!")
                st.rerun()
        st.markdown("---")