# executes a readonly query in postgres.
import MySQLdb
import MySQLdb.cursors
import logging
import pandas as pd

from db_utils import get_staging_db_con_dict

logger = logging.getLogger(__name__)
db_dict = get_staging_db_con_dict()

def execute_query_in_mysql(query: str, params: tuple | list | None = None):
	logger.info(f"executing query in mysql: {query}")
	conn = MySQLdb.connect(
		db            = db_dict.get("stg_database"),
		user          = db_dict.get("stg_user"),
		passwd        = db_dict.get("stg_password"),
		host          = db_dict.get("stg_host"),
		port          = int(db_dict.get("stg_port"))
	)
	try:
		cursor = conn.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute("SET SESSION TRANSACTION READ ONLY")
		cursor.execute(query, params or ())
		rows = cursor.fetchall()
		df = pd.DataFrame(rows)
		return df
	except MySQLdb.Error as e:
		logger.error(f"Got error while executing query: {e}")
		raise e
	finally:
		conn.close()
