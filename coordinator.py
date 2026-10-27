# This coordinates the backend utilities: takes in the original prompt, calls the LLM query gen API,
# validates/executes the query and handles retries
import logging
from db_postgres_executor import execute_query_in_pg
from ai_service import query_llm_with_history

MAX_RETRY_COUNT = 2
# init logger.
logger = logging.getLogger(__name__)

def generate_query_and_execute(prompt: str, tenant_id: int):
	query = generate_query(tenant_id, prompt)
	# query = generate_query(prompt) # HACKY WAY TO FAIL FAST. DELETE IT.
	return execute_with_retries(query, prompt, tenant_id)

def execute_query(query):
	return execute_query_in_pg(query)

def execute_with_retries(query, original_prompt, tenant_id):
	retry_count  = 0
	query_to_use = query
	while True:
		# attempt to execute.
		logger.info(f"Parameters: query_to_use {query_to_use}, retry_count = {retry_count}")
		retry_count += 1
		try :
			rs = execute_query(query_to_use)
			return query_to_use, rs
		except BaseException as e:
			logger.warn(f"Got error while trying to execute the query, retry count = {retry_count}")
			if retry_count >= MAX_RETRY_COUNT:
				logger.warn(f"Retries exhausted. Bailing out with last receieved error ")
				raise e
			p1 = " Original Question: " + original_prompt
			f1 = " Failed Query Attempt: " + query_to_use
			e1 = " Database Error: " + str(e)
			c1 = "Constraint: Only use columns explicitly listed in the Database Schema above. Do not infer or extrapolate column names."

			new_prompt = p1 + f1 + e1 + c1
			query_to_use = query_llm_with_history(tenant_id = tenant_id, query = new_prompt)
