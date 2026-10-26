import sqlglot
import streamlit as st
import logging

logger = logging.getLogger(__name__)
def validate_query_gen_by_llm(query, target_db):
    logger.debug(f"Target db = {target_db}, SQL to validate: {query}")
    try:
        parsed_query = sqlglot.parse_one(query, dialect=target_db)
        logger.info(f"SQL validation passed!")
    except ParseError as e:
        logger.error(f"SQL Validation failed with error {e}")

