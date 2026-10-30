import pandas as pd
import streamlit as st
from config import get_all_dashboards, delete_dashboard_card
from db_postgres_executor import execute_query_in_pg
from views.chat_view import render_flexible_chart, show_sql

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
                render_card(card, is_deletable=False, username=username, prefix=f"sys_{card['id']}")

    with tab2:
        st.markdown("### Public Dashboards Shared by Team")
        if team_cards.empty:
            st.info("No shared team dashboards available yet. Check the public toggle when pinning a query to share it here!")
        else:
            for _, card in team_cards.iterrows():
                st.caption(f"Shared by: `{card['username']}`")
                render_card(card, is_deletable=False, username=username, prefix=f"team_{card['id']}")

    with tab3:
        st.markdown(f"### My Personal Dashboards ({username})")
        if personal_cards.empty:
            st.info("You haven't pinned any custom cards yet! Head over to **NLP Query & Chat** to create one.")
        else:
            for _, card in personal_cards.iterrows():
                visibility = "🌐 Public (Team Shared)" if card["is_public"] == 1 else "🔒 Private"
                st.caption(f"Status: {visibility}")
                render_card(card, is_deletable=True, username=username, prefix=f"pers_{card['id']}")

def render_card(card, is_deletable: bool, username: str, prefix: str):
    """Renders individual saved cards with execute_with_retries and flexible chart support."""
    with st.container():
        st.markdown(f"Question: {card['question']}")
        show_sql(card["sql_query"])
        # define a cache of cards. If present in cachem use the cached df otherwise load it.
        card_id = card['id']
        cache_key = f"df_cache_{card_id}"

        if "card_dfs" not in st.session_state:
            st.session_state["card_dfs"] = {}

        try:
            # check if card is already loaded
            if cache_key not in st.session_state["card_dfs"]:
                rs = execute_query_in_pg(card["sql_query"])
                df0 = pd.DataFrame(rs)
                st.session_state["card_dfs"][cache_key] = df0

            df = st.session_state["card_dfs"][cache_key]
            st.dataframe(df, use_container_width=True)

            # Render flexible chart component imported from chat_view
            render_flexible_chart(df, unique_key_prefix=prefix)

            # Optional: Add a refresh button if user explicitly wants to re-run the query against DB
            if st.button("🔄 Refresh Data", key=f"refresh_{card_id}"):
                if cache_key in st.session_state["card_dfs"]:
                    del st.session_state["card_dfs"][cache_key]
                st.rerun()
        except Exception as e:
            st.error(f"Error executing card query: {e}")
            
        if is_deletable:
            if st.button(f"🗑️ Delete Card", key=f"del_{card['id']}"):
                delete_dashboard_card(card["id"], username)
                st.success("Card deleted!")
                st.rerun()
        st.markdown("---")
