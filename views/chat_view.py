import pandas as pd
import streamlit as st
from ai_service import query_llm_with_history
from config import save_dashboard_card
from config import TENANT_ID
from db_utils import validate_query_gen_by_llm
import logging
from coordinator import execute_with_retries

logger = logging.getLogger(__name__)

def render_flexible_chart(df, unique_key_prefix):
    """Allows users to pick and choose fields and chart types dynamically."""
    if df.empty or len(df.columns) < 1:
        return
        
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Area", "None"], key=f"{unique_key_prefix}_type")
    
    if chart_type != "None":
        with col2:
            x_col = st.selectbox("X-Axis Column", options=df.columns, key=f"{unique_key_prefix}_x")
        with col3:
            numeric_cols = [c for c in df.columns if c != x_col]
            y_cols = st.multiselect("Y-Axis Column(s)", options=numeric_cols, default=numeric_cols[:1] if numeric_cols else [], key=f"{unique_key_prefix}_y")
            
        if x_col and y_cols:
            try:
                chart_data = df.set_index(x_col)[y_cols]
                if chart_type == "Bar":
                    st.bar_chart(chart_data)
                elif chart_type == "Line":
                    st.line_chart(chart_data)
                elif chart_type == "Area":
                    st.area_chart(chart_data)
            except Exception as e:
                st.warning(f"Could not render chart with selected fields: {e}")

def render_chat_view(username: str):
    """Renders NLP chat with public/private dashboard pinning options."""
    st.markdown(f"Welcome back, **{username}**! Ask natural language questions to analyze your data and pin insights.")    
    # Render message history
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "system":
            continue
            
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "df_result" in message and message["df_result"] is not None:
                df = message["df_result"]
                sql = message.get("sql")
                if sql:
                    st.code(sql, language="sql")
                st.dataframe(df, use_container_width=True)
                
                # Flexible chart picker for history
                render_flexible_chart(df, unique_key_prefix=f"hist_{idx}")
                
                # Pinning controls for assistant messages in history
                if message["role"] == "assistant":
                    st.markdown("---")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        make_public = st.checkbox("🌐 Share with Team (Public Dashboard)", key=f"pub_hist_{idx}")
                    with col2:
                        if st.button("📌 Pin to Dashboard", key=f"pin_hist_{idx}"):
                            is_public_val = 1 if make_public else 0
                            prompt_to_save = message.get("prompt", "Custom Query")
                            sql_to_save = message.get("sql")
                            if sql_to_save:
                                save_dashboard_card(username, prompt_to_save, sql_to_save, is_public_val)
                                target_msg = "Team Shared Dashboards" if make_public else "your Personal Dashboard"
                                st.success(f"Successfully pinned to {target_msg}!")
                            else:
                                st.error("No valid SQL query found to pin.")

    if user_prompt := st.chat_input("e.g., Show all courses for this year"):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("LLM is writing and optimizing your query..."):
                logger.info(f"messages: {st.session_state.messages}")
                prompt_to_use = st.session_state.messages[-1]['content'] # using last prompt
                logger.info(f"Using query: {prompt_to_use}")
                assistant_reply = query_llm_with_history(
                    query=prompt_to_use,
                    tenant_id=TENANT_ID
                )

            st.markdown(assistant_reply)
            df_result = None
            sql_query = None
            query_used = None
            # obtained the sql from LLM.
            # validate it.
            try:
                validate_query_gen_by_llm(assistant_reply, 'duckdb')
                sql_query = assistant_reply
                query_used, rs = execute_with_retries(sql_query, prompt_to_use, TENANT_ID)
                df_result = pd.DataFrame(rs)
                st.code(query_used, language="sql")
                st.dataframe(df_result, use_container_width=True)
                
                msg_idx = len(st.session_state.messages)
                render_flexible_chart(df_result, unique_key_prefix=f"live_{msg_idx}")

                # Pinning Controls with Team Sharing Toggle
                st.markdown("---")
                col1, col2 = st.columns([2, 1])
                with col1:
                    make_public = st.checkbox("🌐 Share with Team (Public Dashboard)", key=f"pub_live_{msg_idx}")
                with col2:
                    if st.button("📌 Pin to Dashboard", key=f"pin_live_{msg_idx}"):
                        is_public_val = 1 if make_public else 0
                        save_dashboard_card(username, user_prompt, query_used, is_public_val)
                        target_msg = "Team Shared Dashboards" if make_public else "your Personal Dashboard"
                        st.success(f"Successfully pinned to {target_msg}!")

            except Exception as ex:
                st.error(f"Error executing generated SQL query : {ex}")
            
            # Save message state with metadata so history renders and pinning works correctly on rerun
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_reply,
                "df_result": df_result,
                "sql": query_used or sql_query,
                "prompt": prompt_to_use
            })