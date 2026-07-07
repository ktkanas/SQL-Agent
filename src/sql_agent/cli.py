from sql_agent.agent import ask_database


def main() -> None:
    """Run the interactive SQL agent."""
    print("SQL Agent ready! Type 'exit' to quit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        result = ask_database(question)

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
