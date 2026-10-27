import requests
import re

from config import LLM_BASE_URL

import logging

logger = logging.getLogger(__name__)

def query_llm_with_history(query: str, tenant_id: int) -> str:
    """Sends conversation history and database schema to LLM service wrapper endpoint. 
    The service has the schema context"""

    headers = {"Content-Type": "application/json"}
    payload = {"tenantId": tenant_id, "query": query}

    response = requests.post(LLM_BASE_URL, json=payload, headers=headers)
    # print(f"Got response code: {response.status_code} and response = {response.json()}")
    llm_sql = response.json().get("sql")
    logger.debug(f"Extracted value = {llm_sql}")

    # remove '''sql <> ''' thing if present.
    match = re.search(
        r"```\s*(?:sql)?\s*(.*?)\s*```", llm_sql, re.IGNORECASE | re.DOTALL
    )
    returnSQL = ""
    if match:
        returnSQL = match.group(1)
    else:
        returnSQL = llm_sql

    logger.info(f"SQL generated from LLM: {returnSQL}")
    return returnSQL
