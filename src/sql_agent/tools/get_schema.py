from langchain_core.tools import tool
from sqlalchemy import bindparam, text
from sql_agent.database import engine

@tool
def get_schema(tables: str) -> str:
    """Gets the columns and foreign key relationships for the given comma-separated table names."""

    table_list = [t.strip() for t in tables.split(",") if t.strip()]
    if not table_list:
        return "Error: provide at least one table name."

    col_sql = text("""
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME IN :table_names
    """).bindparams(bindparam("table_names", expanding=True))

    fk_sql = """
    SELECT
        fk.TABLE_NAME,
        cu.COLUMN_NAME,
        pk.TABLE_NAME AS REFERENCED_TABLE,
        pt.COLUMN_NAME AS REFERENCED_COLUMN
    FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
    JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS fk ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
    JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS pk ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE cu ON rc.CONSTRAINT_NAME = cu.CONSTRAINT_NAME
    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pt ON rc.UNIQUE_CONSTRAINT_NAME = pt.CONSTRAINT_NAME
    """

    with engine.connect() as conn:
        col_rows = conn.execute(col_sql, {"table_names": table_list}).fetchall()
        fk_rows = conn.execute(text(fk_sql)).fetchall()

    schema_text = "\n".join(f"{r[0]}.{r[1]} ({r[2]})" for r in col_rows)
    fk_text = "\n".join(f"{r[0]}.{r[1]} -> {r[2]}.{r[3]}" for r in fk_rows)

    return f"Columns:\n{schema_text}\n\nRelationships:\n{fk_text}"
