import logging
import streamlit as st

logger = logging.getLogger(__name__)


# Configure basic settings globally
@st.cache_resource
def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # Minimum log level to capture
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # logging.FileHandler("app.log"),  # Write logs to a file
            logging.StreamHandler()  # Also print logs to the console
        ],
    )
    logger.info(f"Logging setup ready!")
