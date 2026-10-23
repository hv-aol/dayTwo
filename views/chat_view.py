import pandas as pd
import streamlit as st
from ai_service import query_qwen_with_history
from config import get_db_connection, save_dashboard_card
from config import TENANT_ID


def render_chat_view(api_key: str, schema_info: str, username: str):
    """Renders NLP chat with public/private dashboard pinning options."""
    st.markdown(f"Welcome back, **{username}**! Ask natural language questions to analyze your data and pin insights.")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "df_result" in message and message["df_result"] is not None:
                st.dataframe(message["df_result"], use_container_width=True)
                if len(message["df_result"].columns) >= 2:
                    try:
                        st.bar_chart(message["df_result"].set_index(message["df_result"].columns[0]))
                    except Exception:
                        pass

    if user_prompt := st.chat_input("e.g., Show total monthly sales for this year"):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Qwen is writing and optimizing your query..."):
                assistant_reply = query_qwen_with_history(
                    messages=st.session_state.messages,
                    tenantId=TENANT_ID
                )

            st.markdown(assistant_reply)
            
            df_result = None
            sql_query = None
            if "```sql" in assistant_reply:
                try:
                    parts = assistant_reply.split("```sql")
                    sql_query = parts[1].split("```")[0].strip()
                    
                    if sql_query.upper().startswith("SELECT"):
                        conn = get_db_connection()
                        df_result = pd.read_sql(sql_query, conn)
                        conn.close()
                        
                        st.code(sql_query, language="sql")
                        st.dataframe(df_result, use_container_width=True)
                        
                        if len(df_result.columns) >= 2:
                            st.bar_chart(df_result.set_index(df_result.columns[0]))
                        
                        # Pinning Controls with Team Sharing Toggle
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            make_public = st.checkbox("🌐 Share with Team (Public Dashboard)", key=f"pub_{len(st.session_state.messages)}")
                        with col2:
                            if st.button("📌 Pin to Dashboard", key=f"pin_{len(st.session_state.messages)}"):
                                is_public_val = 1 if make_public else 0
                                save_dashboard_card(username, user_prompt, sql_query, is_public_val)
                                target_msg = "Team Shared Dashboards" if make_public else "your Personal Dashboard"
                                st.success(f"Successfully pinned to {target_msg}!")
                    else:
                        st.warning("Only SELECT queries are permitted for execution safety.")
                except Exception as ex:
                    st.error(f"Error executing generated SQL query: {ex}")
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_reply,
                "df_result": df_result,
                "sql": sql_query
            })