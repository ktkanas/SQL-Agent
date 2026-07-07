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

## Web app

Start the browser UI:

```powershell
python -m uvicorn sql_agent.web:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.

By default the app connects to `localhost/visaDB_copy` with Windows trusted
authentication. To use a different SQL Server connection, set
`SQL_AGENT_DATABASE_URL` before starting the server:

```powershell
$env:SQL_AGENT_DATABASE_URL = "mssql+pyodbc://localhost/YourDatabase?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
python -m uvicorn sql_agent.web:app --host 127.0.0.1 --port 8000
```
