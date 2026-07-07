from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from sql_agent.settings import settings
from sql_agent.tools.execute_sql import run_sql
from sql_agent.tools.get_schema import get_schema
from sql_agent.tools.list_tables import list_tables

SYSTEM_PROMPT = """You are an analytical SQL agent. Your job is to fully investigate questions, not just run one query.

Rules:
- Never guess or assume. If you don't have data to support a claim, run another query to get it.
- For analytical questions (why, what factors, compare, explain), run multiple queries from different angles before answering.
- Always verify your conclusions with actual query results.
- Only give a final answer when every claim you make is backed by data.
- If a query fails, analyze the error, fix the SQL, and try again.

Your reasoning pattern:
1. What does the question need me to find out?
2. Run a query to get initial data.
3. Look at the result - what follow-up questions does it raise?
4. Run more queries to answer those follow-up questions.
5. Only when all claims are backed by data, give the final answer."""

llm = ChatOllama(model=settings.ollama_model)
tools = [list_tables, get_schema, run_sql]
agent = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)


def ask_database(question: str) -> dict:
    """Ask the SQL agent a natural-language question."""
    return agent.invoke({"messages": [("human", question)]})


def extract_agent_trace(result: dict) -> dict:
    """Pull user-facing SQL and tool output from a LangGraph result."""
    sql_queries = []
    tool_results = []

    for message in result.get("messages", []):
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call["name"] == "run_sql":
                    sql_queries.append(tool_call["args"].get("sql", ""))

        if hasattr(message, "name") and message.name:
            tool_results.append(
                {
                    "name": message.name,
                    "content": message.content,
                }
            )

    answer = result["messages"][-1].content if result.get("messages") else ""

    return {
        "answer": answer,
        "sql_queries": sql_queries,
        "tool_results": tool_results,
    }
