# executes a readonly query in postgres.
import psycopg
import logging
import streamlit as st
from psycopg.rows import dict_row
from db_utils import get_db_con_dict

logger = logging.getLogger(__name__)
db_dict = get_db_con_dict()

def execute_query_in_pg(query):
	logger.info(f"executing query in postgres: {query}")
	try:
		with psycopg.connect(
			dbname        = db_dict.get("database"),
			user          = db_dict.get("user"),
			password      = db_dict.get("password"),
			host          = db_dict.get("host"),
			port          = db_dict.get("port"),
			row_factory   = dict_row # needed to get column names
		) as conn: # DONOT MAKE IT A CACHED RESOURCE
			conn.read_only = True # => Making it READ_ONLY.
			# Some of the views are secured: user belonging to a desk only sees his desk's data.
			# For that, we need to pass the desk id with the connection.
			# We set is_local = false when setting the parameter, because for a readonly transaction,
			# postgres treats every select statement as a transaction, thereby committing the transaction
			# and inturn, wiping the setting.
			# When pooling connections, please be aware of this fact. Though it shouldn't be a problem
			# as the conn is a per session resource (and not cached across session).
			with conn:
				# open cursor
				with conn.cursor() as cur:
					logger.info(f"1. executing query in postgres")
					# check value of dept id in session
					target_desk = st.session_state.dept_ids # read the dept id from session.
					cur.execute("SELECT set_config('app.desk_ids', %s, false);", (target_desk,))
					# Read back setting
					cur.execute("SELECT current_setting('app.desk_ids', false) AS current_setting;")
					setting_result = cur.fetchone()
					logger.info(f"2. Current setting value: {setting_result}")
					# execute query
					cur.execute(query)
					rs = cur.fetchall()
					return rs
	except BaseException as e:
		logger.error(f"Got error while executing query: {e}")
		raise e
