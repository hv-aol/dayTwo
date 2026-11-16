import streamlit as st
import pandas as pd
import datetime
import logging
from views.template_teacher_view import run_template_execution, validate_dates
from db_mysql_utils import read_courses, read_apex
from views.chat_view import render_flexible_chart
# This template is for Courses related view, for example,
# one template is for viewing all the courses in a given list of apex bodies

logger = logging.getLogger(__name__)

def render_template_courses_view():
    """Renders a library of independent pre-built report templates."""
    st.subheader("📋 Standard Course Templates Library")
    st.markdown(
        "Select a standardized report below. These queries run instantly without LLM translation errors."
    )

    # 1. Template Selector
    template_options = {
        "Apex-wise Course List": render_courses_template,
    }

    selected_template_name = st.selectbox(
        "Choose a Report Template", list(template_options.keys())
    )
    st.markdown("---")

    # 2. Invoke the specific template's independent UI and execution block
    template_func = template_options[selected_template_name]
    template_func()


# --- TEMPLATE 1 ----
def render_courses_template():
    desk_ids = st.session_state.dept_ids
    print(f"Desk ids = {desk_ids}")
    if desk_ids is None:
        st.error("User has no desk_ids!")
        return
    courses_df = read_courses(username=st.session_state.username, desk_ids=desk_ids)
    apex_df = read_apex()
    col1, col2 = st.columns(2)

    if "courses_k" not in st.session_state:
        st.session_state["courses_k"] = {"selection": {"rows": [2]}}

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

    if "apex_k" not in st.session_state:
        st.session_state["apex_k"] = {"selection": {"rows": [2]}}

    with col2:
        apex_df1 = st.dataframe(
            apex_df,
            key="apex_k",
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            height=280
            )
        sel_apex_names = apex_df1.selection.rows

    
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)
    col21, col22 = st.columns(2)
    with col21:
        st_date = st.date_input("start date:", key="perf_st", value=seven_days_ago)
    with col22:
        ed_date = st.date_input("end date:", key="perf_ed", value = today)


    # Validate them
    picked_course_ids = courses_df.iloc[sel_courses_ids]["Course_Id"].tolist()
    picked_apex_names = apex_df.iloc[sel_apex_names]["center_name"].tolist()
    print(f"picked_apex_names: {picked_apex_names}")
    print(f"picked_course_ids: {picked_course_ids}")
    if not validate_inputs(picked_course_ids, picked_apex_names, st_date, ed_date):
        return

    sql_query = f"""SELECT
    c.course_name AS course_name,
    e.program_id,
    e.apex_name,
    e.event_start_date,
    e.event_city,
    e.event_district,
    COUNT(e.global_event_id) AS number_of_courses,
    SUM(e.total_registered_participants) AS total_participants
    FROM v_llm_secure_event_summary e
    JOIN llm_course_id_mapping c ON e.course_type_id = c.course_type_id 
    WHERE e.apex_name = ANY(%s)
    AND e.course_type_id = ANY(%s)
    AND e.event_start_date BETWEEN '{st_date}' AND '{ed_date}' 
    AND e.event_status != 'Cancelled' 
    GROUP BY c.course_name, e.program_id, e.apex_name, e.event_start_date, e.event_city, e.event_district
    """
    logger.info(f"type of selected apex ds: {type(picked_apex_names)}")
    logger.info(f"type of selected course ds: {type(picked_course_ids)}")

    # UNFORTUNATELY, course_type_ids are varchar in db. Convert the int id list to varchar
    picked_course_ids_str = [str(x) for x in picked_course_ids]
    chart_key="courses_chart"
    df = run_template_execution(sql_query=sql_query,
        template_title="Courses Details",
        chart_key=chart_key,params=(picked_apex_names, picked_course_ids_str))
    # Show the df on a graph
    render_flexible_chart(df, unique_key_prefix=chart_key)


def validate_inputs(course_ids, apex_ids, st_date, ed_date):
    # ensure at least one course_ids and apex_ids are picked
    if len(course_ids) <= 0:
        st.error("Please select at least one course")
        return False
    if len(apex_ids) <= 0:
        st.error("Please select at least one Apex region")
        return False
    return validate_dates(st_date, ed_date)
