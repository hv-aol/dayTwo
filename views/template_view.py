import pandas as pd
import streamlit as st
from db_postgres_executor import execute_query_in_pg
from config import TENANT_ID
import datetime
from views.chat_view import render_flexible_chart, show_sql

def render_template_view():
    """Renders a library of independent pre-built report templates."""
    st.subheader("📋 Standard Report Templates Library")
    st.markdown(
        "Select a standardized report below. These queries run instantly without LLM translation errors."
    )

    # 1. Template Selector
    template_options = {
        "Teacher Performance": render_teacher_performance_template,
        "Teacher Details": render_teacher_details_template,
        "Revenue & Billing Overview": render_revenue_template,
    }

    selected_template_name = st.selectbox(
        "Choose a Report Template", list(template_options.keys())
    )
    st.markdown("---")

    # 2. Invoke the specific template's independent UI and execution block
    template_func = template_options[selected_template_name]
    template_func()


# --- INDEPENDENT TEMPLATE 1 ---
def render_teacher_performance_template():
    st.markdown("### 📚 Teacher Performance Summary")
    st.caption("Analyze Teacher Performance for a given period of time")

    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)
    col1, col2, col3 = st.columns(3)
    with col1:
        teacher_code = st.text_input("Enter Teacher code:", key="perf_tc")
    with col2:
        st_date = st.date_input("start date:", key="perf_st", value=seven_days_ago)
    with col3:
        ed_date = st.date_input("end date:", key="perf_ed", value = today)

    # validate the inputs.
    if not validate_perf_inputs(st_date, ed_date, teacher_code):
        return

    sql_query = f"""
		SELECT 
		    v_llm_teacher_performance.course_event_name,
            llm_course_id_mapping.name AS course_type,
		    v_llm_teacher_performance.event_start_date,
		    v_llm_teacher_performance.event_start_month,
		    v_llm_teacher_performance.event_state,
		    v_llm_teacher_performance.event_city,
		    v_llm_teacher_performance.event_district,
		    v_llm_teacher_performance.participants_attended 
		FROM 
		    v_llm_teacher_performance
		JOIN 
		    llm_course_id_mapping 
		ON 
		    v_llm_teacher_performance.course_type = llm_course_id_mapping.course_type_id
		WHERE 
		    v_llm_teacher_performance.teacher_code = '{teacher_code}' 
		    AND v_llm_teacher_performance.event_start_month BETWEEN '{st_date}' AND '{ed_date}'"""

    
    run_template_execution(sql_query, "Teacher Performance Summary", "perf_chart")


def validate_perf_inputs(st_date, ed_date, teacher_code):
    if teacher_code is None:
        st.error("Please enter teacher code.")
        return False
    if st_date is None or ed_date is None:
        st.error("Please select both Start Date and End Date.")
        return False

        # Check 2: Ensure Start Date < End Date
    elif st_date >= ed_date:
        st.error("Invalid Date Range: **Start Date must be earlier than End Date**.")
        return False
    return True


# --- INDEPENDENT TEMPLATE 2 ---
def render_teacher_details_template():
    st.markdown("### 📅 Teacher Details")
    st.caption("List personal details of a teacher")

    teacher_code = st.text_input("Enter Teacher code:", key="dtls_tc")

    # validate the inputs.
    if not validate_dtls_inputs(teacher_code):
        return

    sql_query = f"""
    SELECT 
        vt.teacher_code,
        vt.teacher_name,
        vt."full_time/part_time",
        vt.ttc_year,
        vt.teacher_gender,
        vt.teacher_phone,
        vt.teacher_email,
        vt.teacher_birth_date,
        vt.teacher_city,
        vt.teacher_apex
            from view_teacher vt where vt.teacher_code = '{teacher_code}'
    """

    run_template_execution(sql_query, "Teacher Details", "dtls_chart")

def validate_dtls_inputs(teacher_code):
    if teacher_code is None:
        st.error("Please enter teacher code.")
        return False
    return True


# --- INDEPENDENT TEMPLATE 3 ---
def render_revenue_template():
    st.markdown("### 💰 Revenue & Billing Overview")
    st.caption("Summarize financial inflows broken down by category.")

    category = st.selectbox(
        "Billing Category",
        ["All Categories", "Tuition", "Lab Fees", "Materials"],
        key="rev_cat",
    )

    cat_filter = (
        "" if category == "All Categories" else f"WHERE category = '{category}'"
    )

    sql_query = f"""
        SELECT category, SUM(amount) as total_revenue, COUNT(invoice_id) as invoice_count
        FROM billing_records
        {cat_filter}
        GROUP BY category
        ORDER BY total_revenue DESC;
    """

    run_template_execution(sql_query, "Revenue & Billing Overview", "rev_chart")


# --- HELPER: SHARED EXECUTION RENDERER ---
def run_template_execution(sql_query: str, template_title: str, chart_key: str):
    # store the result and query in session.
    data_key = f"data_{chart_key}"
    query_key = f"query_{chart_key}"

    """Executes template queries independently and renders data/charts."""
    if st.button(f"🚀 Run '{template_title}'", type="primary", key=f"btn_{chart_key}"):
        try:
            rs = execute_query_in_pg(sql_query)
            df = pd.DataFrame(rs)

            if df.empty:
                st.info("No data returned for the selected parameters.")
                return
            st.session_state[data_key] = df            
            st.session_state[query_key] = sql_query


        except Exception as e:
            st.error(f"Error executing template query: {e}")

    if data_key not in st.session_state :
        return
    # Now, render what is present in session state.
    df = st.session_state[data_key]
    query = st.session_state[query_key]

    if df is None:
        return
    if df.empty:
        st.info("No data returned for the selected parameters.")
        return

    show_sql(st.session_state[query_key])
    st.dataframe(st.session_state[data_key], use_container_width=True)

    # Render flexible chart component imported from chat_view
    render_flexible_chart(df, unique_key_prefix=chart_key)
