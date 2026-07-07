# SQL Agent

A local analytical SQL agent that uses LangGraph, Ollama, and Microsoft SQL Server.

## Project structure

```text
.
|-- src/sql_agent/       # Application package
|   |-- nodes/           # LangGraph workflow nodes
|   |-- tools/           # Database tools exposed to the agent
|   |-- cli.py           # Interactive command-line application
|   |-- database.py      # SQLAlchemy connection
|   |-- safety.py        # Shared read-only SQL validation
|   `-- state.py         # Workflow state types
|-- scripts/             # Data-loading and maintenance scripts
|-- data/raw/            # Source datasets
|-- docs/                # Requirements and sample questions
|-- tests/               # Automated tests
|-- main.py              # Local convenience entry point
`-- pyproject.toml       # Package metadata and dependencies
```

## Setup

1. Create and activate a virtual environment.
2. Run `pip install -e .`.
3. Ensure Ollama and SQL Server are running and configured.
4. Start the agent with `sql-agent` or `python main.py`.

