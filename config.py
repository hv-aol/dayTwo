import sqlite3
import pandas as pd

LLM_BASE_URL = "http://localhost:7070/getQuery/"
TENANT_ID=202
METADATA_DB = "metabase_metadata.db"
SQL_APRIL_COURSES = "SELECT c.name AS course_name, e.apex_name, COUNT(e.global_event_id) AS number_of_courses, SUM (e.total_registered_participants) AS total_participants FROM v_llm_event_summary e JOIN llm_course_id_mapping c ON e.course_type_id = c.course_type_id WHERE e.course_type_id IN ('911', '912', '914') AND e.event_start_date BETWEEN '2026-04-01' AND '2026-04-30' GROUP BY c.name, e.apex_name "

def get_metadata_connection():
    """Returns connection to the metadata store."""
    return sqlite3.connect(METADATA_DB, check_same_thread=False)

def init_metadata_store():
    """Initializes metadata tables, adds public support columns, and seeds system defaults."""
    conn = get_metadata_connection()
    cursor = conn.cursor()
    
    # Create dashboards table with is_public flag
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            question TEXT,
            sql_query TEXT,
            is_system INTEGER DEFAULT 0,
            is_public INTEGER DEFAULT 0
        )
    """)
    
    # Safe fallback migration if table already existed without is_public column
    try:
        cursor.execute("ALTER TABLE dashboards ADD COLUMN is_public INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass 

    # Seed system default dashboards if empty
    cursor.execute("SELECT COUNT(*) FROM dashboards WHERE is_system = 1;")
    if cursor.fetchone()[0] == 0:
        default_cards = [
            ("system", "Courses overview in April 2026", SQL_APRIL_COURSES, 1, 1)
        ]
        cursor.executemany("INSERT INTO dashboards (username, question, sql_query, is_system, is_public) VALUES (?, ?, ?, ?, ?)", default_cards)
        conn.commit()
    conn.close()

def get_all_dashboards():
    """Fetches all dashboard cards from metadata store."""
    conn = get_metadata_connection()
    df = pd.read_sql("SELECT * FROM dashboards", conn)
    conn.close()
    return df

def save_dashboard_card(username: str, question: str, sql_query: str, is_public: int):
    """Saves a dashboard card with public/private status."""
    conn = get_metadata_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO dashboards (username, question, sql_query, is_system, is_public) VALUES (?, ?, ?, 0, ?)",
        (username, question, sql_query, is_public)
    )
    conn.commit()
    conn.close()

def delete_dashboard_card(card_id: int, username: str):
    """Deletes a user's custom dashboard card."""
    conn = get_metadata_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dashboards WHERE id = ? AND username = ? AND is_system = 0", (card_id, username))
    conn.commit()
    conn.close()

def get_database_schema() -> str:
    """Returns the schema description string passed to Qwen."""
    return """
    Table: users (user_id, name, email, signup_date)
    Table: orders (order_id, user_id, product_name, amount, order_date)
    Table: analytics_events (event_id, user_id, event_type, timestamp)
    """