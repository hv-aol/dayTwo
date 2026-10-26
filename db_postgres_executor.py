# executes a readonly query in postgres.
import psycopg
import logging
from psycopg.rows import dict_row


DB_SERVER_IP="65.0.186.33"
DB_SERVER_PORT="5432"
DB_USER_NAME="aolt_user" # Keep it in secrets
DB_USER_PWD="stYnWfBTNKW" #Keep it in secrets
DB_NAME="analytics_dev"

logger = logging.getLogger(__name__)
MAX_RETRY_COUNT = 5

def execute_query_in_pg1(query):
	logger.warn(f"Returning a hardcoded dataframe!!!")
	data = {
		"Name": ["Alice", "Bob", "Charlie", "David", "Eva"],
		"Age": [25, 30, 35, 40, 45],
		"City": ["New York", "London", "Paris", "Tokyo", "Sydney"],
	}
	return data


def execute_query_in_pg(query):
	logger.info(f"executing query in postgres {query}")
	try:
		with psycopg.connect(
			dbname        = DB_NAME,
			user          = DB_USER_NAME,
			password      = DB_USER_PWD,
			host          = DB_SERVER_IP,
			port          = DB_SERVER_PORT,
			# IMP: Make it READ_ONLY.
			autocommit    = True,
			row_factory   = dict_row # needed to get column names
		) as conn:
			conn.read_only = True 

			# open cursor
			with conn.cursor() as cur:
				# execute query
				cur.execute(query)
				rs = cur.fetchall()
				return rs
	except BaseException as e:
		logger.error(f"Got error while executing query {e}")
		raise e
	finally:
		conn.close()
