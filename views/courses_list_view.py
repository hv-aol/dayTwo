import pandas as pd
import streamlit as st

data = {
	"Course_Id": [1, 12, 122],
	"Course Name": ["A", "B c", "dfg"],
	"Course Label": ["df", "dd", "FF"]
}

def render_courses_list(username: str):
    st.markdown(f"Welcome **{username}**! Below is the list of courses associated with your assigned Desk Id {st.session_state.dept_ids}")
    df1 = pd.read_csv('views/courses_list.tsv', sep='\t')
    st.dataframe(df1, hide_index=True,
    	column_config={
        "Course_Id": st.column_config.TextColumn("Course_Id")
    })
