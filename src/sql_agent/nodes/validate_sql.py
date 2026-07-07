from sql_agent.safety import validate_sql as check_sql

def validate_sql(state):
    is_valid, error = check_sql(state["sql_query"])
    return {"error": "" if is_valid else error}
