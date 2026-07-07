import re
from langchain_ollama import ChatOllama

llm = ChatOllama(model="Qwen2.5-Coder:latest")

def clean_sql(sql: str) -> str:
    # Remove markdown
    sql = re.sub(r"```sql|```", "", sql)
    # Remove LIMIT (MySQL syntax)
    sql = re.sub(r"\bLIMIT\s+\d+", "", sql, flags=re.IGNORECASE)
    # Remove misplaced TOP at end
    sql = re.sub(r"\bTOP\s+\d+\s*;?\s*$", "", sql, flags=re.IGNORECASE)
    # Remove OFFSET/FETCH
    sql = re.sub(r"OFFSET\s+\d+\s+ROWS.*", "", sql, flags=re.IGNORECASE)
    # Fix SELECT without TOP when ORDER BY + limiting is implied
    sql = sql.strip().rstrip(";")
    return sql

def generate_sql(state):

    prompt = f"""Write a T-SQL query for SQL Server.

Strict rules:
- Output ONLY valid SQL, absolutely nothing else
- No explanations, no markdown, no natural language
- To limit rows use: SELECT TOP N ... not LIMIT or OFFSET/FETCH
- TOP must come right after SELECT, example: SELECT TOP 1 col FROM table
- Use consistent aliases

Tables: {state['tables']}

Schema:
{state['schema']}

Question: {state['question']}

SQL query:"""

    sql = llm.invoke(prompt).content
    sql = clean_sql(sql)
    print(f"Generated SQL:\n{sql}\n")

    return {
        "sql_query": sql
    }
