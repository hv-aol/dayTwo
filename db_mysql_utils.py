import pandas as pd
import streamlit as st
from db_mysql_executor import execute_query_in_mysql

@st.cache_data(ttl=600)
def read_courses(username: str, desk_ids: str):
#	st.markdown(f"Welcome **{username}**! Below is the list of courses associated with your assigned Desk Id {desk_ids}")
	ids_int_list = [int(x.strip()) for x in desk_ids.split(",") if x.strip()]
	place_holders = ", ".join(["%s"] * len(ids_int_list))
	print(f"int_ids_list: {ids_int_list}, Place holders: {place_holders}")
	print([type(x) for x in ids_int_list])
	query = f"""
	SELECT
		cov.label as Course_Label,
		cov.name as Course_Name,
		s.course_type_id as Course_Id,
		s.course_desk_id as Desk_Id
		FROM civicrm_course_desk_courses s, civicrm_option_value cov 
		WHERE s.course_desk_id in ({place_holders}) 
		AND s.refresh_type = 'U'
		AND cov.refresh_type = 'U'
		AND cov.option_group_id = 14
		AND cov.value = s.course_type_id
		ORDER BY Course_Label """
	df = execute_query_in_mysql(query, ids_int_list)
	return df

@st.cache_data(ttl=600)
def read_apex():
	query = f"""
	SELECT 
		center_name 
		FROM 
		civicrm_aol_center cac
		WHERE cac.is_apex = 1
		ORDER BY center_name """
	df = execute_query_in_mysql(query)
	return df
