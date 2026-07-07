import pandas as pd
from langchain_core.tools import tool
from sql_agent.database import engine
from sql_agent.safety import MAX_ROWS, clean_sql, validate_sql

@tool
def run_sql(sql: str) -> str:
    """Validates and executes a T-SQL query against the database. Returns the result as a table."""

    sql = clean_sql(sql)

    is_valid, error = validate_sql(sql)
    if not is_valid:
        return f"Error: {error}"

    try:
        df = pd.read_sql(sql, engine)
        if len(df) > MAX_ROWS:
            df = df.head(MAX_ROWS)
            return f"{df.to_string()}\n\nResult truncated to {MAX_ROWS} rows."
        return df.to_string()
    except Exception as e:
        return f"Error: {str(e)}"
