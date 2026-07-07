from typing import TypedDict, Optional

class AgentState(TypedDict, total=False):
    question: str

    tables: str
    schema: str

    sql_query: str
    sql_result: str

    answer: str
    error: str