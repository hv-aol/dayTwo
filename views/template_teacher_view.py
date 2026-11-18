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
        "Full Time Teachers Performance": render_ft_teachers_performance_template,
    }

    selected_template_name = st.selectbox(
        "Choose a Report Template", list(template_options.keys())
    )
    st.markdown("---")

    # 2. Invoke the specific template's independent UI and execution block
    template_func = template_options[selected_template_name]
    template_func()

# --- TEMPLATE 1 ---
def render_teacher_performance_template():
    st.markdown("### 📚 Teacher Performance Summary")
    st.caption("Analyze Teacher Performance for a given period of time")
    courses_df, sel_courses_ids = helper_fn_list_courses()
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)
    col1, col2, col3 = st.columns(3)
    with col1:
        teacher_code = st.text_input("Enter Teacher code:", key="perf_tc")
    with col2:
        st_date = st.date_input("start date:", key="perf_st", value=thirty_days_ago)
    with col3:
        ed_date = st.date_input("end date:", key="perf_ed", value = today)

    # validate the inputs.
    if not validate_perf_inputs(st_date, ed_date, teacher_code):
        return
    # if user has selected courses, add them to the filter, else just get all the courses
    sql_query_0 = f"""
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

    sql_query_1 = f"""
		SELECT
        vstp.teacher_code,
        vstp.teacher_name,
        COUNT(e.global_event_id) AS number_of_courses,
        SUM(vstp.participants_attended ) AS total_participants
        FROM
            v_llm_secure_teacher_performance vstp
        JOIN
            v_llm_secure_event_summary e
        ON
            vstp.global_event_id = e.global_event_id
		WHERE 
		    vstp.teacher_code = '{teacher_code}'
		    AND vstp.event_start_month BETWEEN '{st_date}' AND '{ed_date}'
            AND vstp.event_status != 'Cancelled'
            """
    add_course_filter = len(courses_df) > len(sel_courses_ids)
    params = None

    if add_course_filter:
        sql_query_1 += " AND vstp.course_type = ANY(%s) "
        sql_query_0 += " AND a.course_type = ANY(%s) "
        picked_course_ids = courses_df.iloc[sel_courses_ids]["Course_Id"].tolist()
        picked_courses_ids_str = helper_fn_int_str(picked_course_ids)
        #logger.info(f"Selected course ids {picked_courses_ids_str}")
        params = (picked_courses_ids_str,)

    ## Add the group by clause
    sql_query_1 += """
    GROUP BY
        vstp.teacher_code,
        vstp.teacher_name
    """
    # Create a batch for both the queries, and execute.
    k0 = "c_dtl"
    k1 = "o_dtl"

    args = [(sql_query_0, params, k0), (sql_query_1, params, k1)]
    dfs_with_key = helper_sql_executor(args, "Performance Details", "perf_turbo_key")

    for df, k in dfs_with_key:
        st.session_state[k] = df

    # Now, render what is present in session state.
    if k0 not in st.session_state or k1 not in st.session_state:
        return
    df0 = st.session_state[k0]
    df1 = st.session_state[k1]

    if df0 is None and df1 is None:
        return
    if df0.empty and df1.empty:
        st.info("No data returned for the selected parameters.")
        return

    st.markdown("#### 📅 Overall Details")
    st.dataframe(st.session_state[k1], use_container_width=True, hide_index=True)
    st.markdown("#### 📅 Individual Course level Details")
    st.dataframe(st.session_state[k0], use_container_width=True, hide_index=True)
    # Show the df on a graph
    # group the df by course type and sum the number of participants
    #df1 = df.groupby('course_type')['total_participants'].sum().reset_index()
    render_flexible_chart(df0, unique_key_prefix="fchart_key_{k1}")

def helper_fn_int_str(int_ids: list):
    # UNFORTUNATELY, course_type_ids are varchar in db. Convert the int id list to varchar
    course_ids_str = [str(x) for x in int_ids]
    return course_ids_str

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

# --- TEMPLATE 2 ---
def render_teacher_details_template():
    st.markdown("### 📅 Teacher Details")
    st.caption("List personal details of a teacher")
    k3 = "dtls_tc"
    teacher_code = st.text_input("Enter Teacher code:", key=k3)

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

    k0 = "p_dtl"
    k1 = "t_dtl"

    args = [(sql_query, None, k0), (ttc_sql_query, None, k1)]
    dfs_with_key = helper_sql_executor(args, "Teacher Details", "dtls_turbo_key")
    for df, k in dfs_with_key:
        st.session_state[k] = df

    # Now, render what is present in session state.
    if k0 not in st.session_state or k1 not in st.session_state:
        return
    df0 = st.session_state[k0]
    df1 = st.session_state[k1]

    if df0 is None and df1 is None:
        return
    if df0.empty and df1.empty:
        st.info("No data returned for the selected parameters.")
        return
    st.markdown("#### 📅 Personal Details")
    st.dataframe(st.session_state[k0], use_container_width=True, hide_index=True)
    st.markdown("#### 📅 TTC Details")
    st.dataframe(st.session_state[k1], use_container_width=True, hide_index=True)


def validate_dtls_inputs(teacher_code):
    if teacher_code is None:
        st.error("Please enter teacher code.")
        return False
    return True

def helper_fn_list_courses():
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
        return courses_df, sel_courses_ids


# --- INDEPENDENT TEMPLATE 3 ---
def render_ft_teachers_performance_template():
    st.markdown("### 📚 Full Time Teacher Performance Summary")
    st.caption("**Analyze Teacher Performance for a given period of time**")
    courses_df, sel_courses_ids = helper_fn_list_courses()
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=30)

    col2, col3 = st.columns(2)
    with col2:
        st_date = st.date_input("Start date:", key="ft_perf_st", value=seven_days_ago)
    with col3:
        ed_date = st.date_input("End date:", key="ft_perf_ed", value = today)

    # validate the inputs.
    picked_course_ids = courses_df.iloc[sel_courses_ids]["Course_Id"].tolist()
    
    if not validate_ft_perf_inputs(picked_course_ids, st_date, ed_date):
        return
    ft_query = f"""
WITH full_time_teachers AS (
    -- Guarantees strictly 1 row per global_teacher_id even if name/status changed over time
    SELECT DISTINCT ON (global_teacher_id)
        global_teacher_id,
        teacher_code,
        teacher_name,
        teacher_status
    FROM v_llm_secure_teacher_performance
    WHERE employment_type = 'FullTime'
    and teacher_status = 'Active'
    ORDER BY global_teacher_id, event_start_date DESC NULLS LAST
),
eligible_teachers AS (
    -- Collapses all matched course types into 1 row per teacher
    SELECT DISTINCT
        global_teacher_id
    FROM public.teacher_course_type
    WHERE COALESCE(is_deleted_prod, 0) = 0
          AND course_type_id = ANY(%s)
),
recent_activity AS (
    -- Sums all courses and pax across the passed course types into 1 row per teacher
    SELECT
        global_teacher_id,
        COUNT(DISTINCT global_event_id) AS total_courses_taught,
        COALESCE(SUM(participants_attended), 0) AS total_participants
    FROM v_llm_secure_teacher_performance
    WHERE employment_type = 'FullTime'
      AND event_status = 'Not Cancelled'
      AND event_start_date BETWEEN '{st_date}' AND '{ed_date}'
      AND course_type = ANY(%s)
    GROUP BY global_teacher_id
)
SELECT
    t.global_teacher_id,
    t.teacher_code,
    t.teacher_name,
    t.teacher_status,
    COALESCE(a.total_courses_taught, 0) AS total_courses,
    COALESCE(a.total_participants, 0) AS total_pax
FROM full_time_teachers t
INNER JOIN eligible_teachers e
    ON t.global_teacher_id = e.global_teacher_id
LEFT JOIN recent_activity a
    ON t.global_teacher_id = a.global_teacher_id
ORDER BY total_courses DESC, t.teacher_name ASC
    """
    logger.info(f"type of selected course ds: {type(picked_course_ids)}")
    # UNFORTUNATELY, course_type_ids are varchar in db. Convert the int id list to varchar
    picked_course_ids_str = [str(x) for x in picked_course_ids]
    chart_key="ft_courses_chart"
    # logger.info(f"picked_course_ids_str: {picked_course_ids_str}")
    df = run_template_execution(
        sql_query=ft_query,
        template_title="Full Time Teacher Performance Details",
        chart_key=chart_key,
        params=(picked_course_ids_str, picked_course_ids_str,))
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


def helper_sql_executor(sql_with_params: list, template_title: str, but_key: str):
    res_df = []
    if st.button(f"🚀 Run '{template_title}'", type="primary", key = but_key):
        try:
            for (q, p, k) in sql_with_params:
                #logger.info(f"Executing query: {q}, with params {p}")
                rs = execute_query_in_pg(q, p)
                df = pd.DataFrame(rs)
                res_df.append((df, k))
        except Exception as e:
            logger.error(f"Error executing query {e}")
    return res_df
