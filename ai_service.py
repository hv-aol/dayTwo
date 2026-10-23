import requests
import re

from config import LLM_BASE_URL

def query_qwen_with_history(messages: list, schema: str) -> str:
    """Sends conversation history and database schema to LLM service wrapper endpoint. 
    The service has the schema context"""

    headers = {"Content-Type": "application/json"}
    payload = {"tenantId": tenant_id, "query": que_en}

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


    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
    
    system_prompt = {
        "role": "system",
        "content": f"You are an expert SQL data analyst assistant. Given the following database schema:\n{schema}\n\nAnswer user requests conversationally. When a data query is needed, provide a brief explanation followed by a valid SQL SELECT query enclosed in a markdown code block (```sql ... ```)."
    }
    
    full_payload = [system_prompt] + [m for m in messages if m["role"] != "system"]
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=full_payload,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error communicating with OpenRouter endpoint: {str(e)}"