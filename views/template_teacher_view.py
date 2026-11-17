import pandas as pd
import streamlit as st
from db_postgres_executor import execute_query_in_pg
import datetime
from views.chat_view import render_flexible_chart, show_sql
from db_mysql_utils import read_courses
import logging

logger = logging.getLogger(__name__)

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
        "Full Time Teacher Performance": render_ft_teacher_performance_template,
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
		    a.course_name,
            a.program_id,
            b.course_name AS course_type,
		    a.event_start_date,
		    a.event_start_month,
		    a.event_state,
		    a.event_city,
		    a.event_district,
		    a.participants_attended 
		FROM 
		    v_llm_secure_teacher_performance a
		JOIN 
		    llm_course_id_mapping b
		ON 
		    a.course_type = b.course_type_id
		WHERE 
		    a.teacher_code = '{teacher_code}' 
		    AND a.event_start_month BETWEEN '{st_date}' AND '{ed_date}'
            AND a.event_status != 'Cancelled'"""

    chart_key = "perf_chart"
    df = run_template_execution(sql_query, "Teacher Performance Summary", chart_key)
    if df is None:
        return
    # Show the df on a graph
    # group the df by course type and sum the number of participants
    df1 = df.groupby('course_type')['participants_attended'].sum().reset_index()
    render_flexible_chart(df1, unique_key_prefix=chart_key)


def validate_perf_inputs(st_date, ed_date, teacher_code):
    if teacher_code is None:
        st.error("Please enter teacher code.")
        return False
    return validate_dates(st_date, ed_date)

def validate_dates(st_date, ed_date):
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
    chart_key1 = "dtls_chart"
    df = run_template_execution(
        sql_query = sql_query,
        template_title = "Personal Details",
        chart_key = chart_key1)

    # Fetch elegible courses and their TTC/elegibility dates
    ttc_sql_query = f"""
    SELECT
    b.teacher_code,
    a.global_teacher_id ,
    a.course_type,
    a.ttc_year,
    a.course_type_id
FROM
    teacher_course_type a,
    teacher b
WHERE
    a.global_teacher_id = b.global_teacher_id
    and b.teacher_code = '{teacher_code}'
    and (a.course_type_id != null
        or a.course_type_id != '')
ORDER BY
    a.ttc_year,
    b.teacher_code desc
    """
    key = "ft_dtls_chart"
    ttc_df = run_template_execution(
        sql_query = ttc_sql_query,
        template_title = "TTC Details",
        chart_key = key)
    # Show the df on a graph
    render_flexible_chart(ttc_df, unique_key_prefix = key)

def validate_dtls_inputs(teacher_code):
    if teacher_code is None:
        st.error("Please enter teacher code.")
        return False
    return True

# --- INDEPENDENT TEMPLATE 3 ---
def render_ft_teacher_performance_template():
    st.markdown("### 📚 Full Time Teacher Performance Summary")
    st.caption("**Analyze Teacher Performance for a given period of time**")
    desk_ids = st.session_state.dept_ids
    courses_df = read_courses(username=st.session_state.username, desk_ids=desk_ids)

    st.markdown("##### Please select courses #####")
    if "courses_k" not in st.session_state:
        st.session_state["courses_k"] = {"selection": {"rows": [2]}}

    col1, = st.columns(1)
    with col1:
        courses_df1 = st.dataframe(
            courses_df,
            key="courses_k",
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            height=280
            )
        sel_courses_ids = courses_df1.selection.rows

    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)

    col2, col3 = st.columns(2)
    with col2:
        st_date = st.date_input("Start date:", key="ft_perf_st", value=seven_days_ago)
    with col3:
        ed_date = st.date_input("End date:", key="ft_perf_ed", value = today)

    # validate the inputs.
    picked_course_ids = courses_df.iloc[sel_courses_ids]["Course_Id"].tolist()
    print(f"picked_course_ids: {picked_course_ids}")

    if not validate_ft_perf_inputs(picked_course_ids, st_date, ed_date):
        return
    sql_query = f"""SELECT
        vstp.teacher_code,
        vstp.teacher_name,
        vstp.course_name,
        vstp.course_type,
        COUNT(e.global_event_id) AS number_of_courses,
        SUM(vstp.participants_attended ) AS total_participants
        FROM
            v_llm_teacher_performance vstp
        JOIN
            v_llm_event_summary e
        ON
            vstp.global_event_id = e.global_event_id
        WHERE
            vstp.employment_type = 'FullTime'
            AND e.event_start_date BETWEEN '{st_date}' AND '{ed_date}'
            AND e.event_status != 'Cancelled'
            and vstp.course_type = ANY(%s)
        GROUP BY
            vstp.course_type,
            vstp.teacher_code,
            vstp.course_name,
            vstp.teacher_code,
            vstp.teacher_name
        order by teacher_code
    """
    logger.info(f"type of selected course ds: {type(picked_course_ids)}")
    # UNFORTUNATELY, course_type_ids are varchar in db. Convert the int id list to varchar
    picked_course_ids_str = [str(x) for x in picked_course_ids]
    chart_key="ft_courses_chart"
    logger.info(f"picked_course_ids_str: {picked_course_ids_str}")
    df = run_template_execution(
        sql_query=sql_query,
        template_title="Full Time Teacher Performance Details",
        chart_key=chart_key,
        params=(picked_course_ids_str,))
    # Show the df on a graph
    render_flexible_chart(df, unique_key_prefix=chart_key)

def validate_ft_perf_inputs(course_ids, st_date, ed_date):
    if len(course_ids) <=0:
        st.error("Please select at least one courses")
        return False
    return validate_dates(st_date, ed_date)

def render_revenue_template():
    st.markdown("### 💰 Revenue & Billing Overview")
    st.caption("Summarize financial inflows broken down by category.")
    st.subheader("Not Implememnted Yet")


# --- HELPER: SHARED EXECUTION RENDERER ---
def run_template_execution(
    sql_query: str,
    template_title: str,
    chart_key: str,
    params: tuple | list | None = None):
    # store the result and query in session.
    data_key = f"data_{chart_key}"
    query_key = f"query_{chart_key}"

    """Executes template queries independently and renders data/charts."""
    if st.button(f"🚀 Run '{template_title}'", type="primary", key=f"btn_{chart_key}"):
        try:
            rs = execute_query_in_pg(sql_query, params)
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
    return df
