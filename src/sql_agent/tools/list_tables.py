from langchain_core.tools import tool
from sqlalchemy import text
from sql_agent.database import engine

@tool
def list_tables(query: str = "") -> str:
    """Lists all available tables in the database. Call this first to know what tables exist."""

    sql = """
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE='BASE TABLE'
    """

    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()

    return "\n".join(r[0] for r in rows)
