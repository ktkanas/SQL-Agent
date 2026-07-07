from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from sql_agent.tools.list_tables import list_tables
from sql_agent.tools.get_schema import get_schema
from sql_agent.tools.execute_sql import run_sql

llm = ChatOllama(model="qwen3:8b")

tools = [list_tables, get_schema, run_sql]

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

agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


def main() -> None:
    """Run the interactive SQL agent."""
    print("SQL Agent ready! Type 'exit' to quit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        result = agent.invoke({"messages": [("human", question)]})

        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc["name"] == "run_sql":
                        print(f"\nSQL Query:\n{tc['args'].get('sql', '')}")
            if hasattr(msg, "name") and msg.name == "run_sql":
                print(f"\nSQL Result:\n{msg.content}")

        print(f"\nAgent: {result['messages'][-1].content}\n")


if __name__ == "__main__":
    main()
