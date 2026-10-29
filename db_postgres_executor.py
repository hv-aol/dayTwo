# executes a readonly query in postgres.
import psycopg
import logging
from psycopg.rows import dict_row
from db_utils import get_db_con_dict

logger = logging.getLogger(__name__)
MAX_RETRY_COUNT = 5

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
		logger.error(f"Got error while executing query: {e}")
		raise e
	finally:
		conn.close()
