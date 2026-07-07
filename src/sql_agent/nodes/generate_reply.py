from langchain_ollama import ChatOllama

llm = ChatOllama(model="Qwen2.5-Coder:latest")

def generate_reply(state):

    error = state.get("error", "")
    sql_result = state.get("sql_result", "")

    if error:
        return {"answer": f"Query failed: {error}"}

    if not sql_result:
        return {"answer": "No results found."}

    prompt = f"""You are given a question and the exact query result. Summarize the result in 1-2 sentences only. Do not make up data.

Question: {state['question']}

Query Result:
{sql_result}

Summary:"""

    summary = llm.invoke(prompt).content.strip()

    return {"answer": f"{summary}\n\n{sql_result}"}
