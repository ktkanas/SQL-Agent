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

The web app has two parts in one Python service:

```text
Browser UI -> FastAPI backend -> SQL Agent -> SQL Server
```

The browser never connects directly to SQL Server. FastAPI owns the database
connection, read-only SQL validation, Ollama/LangGraph agent calls, health
checks, and API errors.

## Configuration

Copy `.env.example` into your deployment environment and set the values as
environment variables. By default the app connects to `localhost/visaDB_copy`
with Windows trusted authentication.

Common settings:

```text
SQL_AGENT_DATABASE_URL          SQLAlchemy connection URL
SQL_AGENT_OLLAMA_MODEL          Ollama model name, default qwen3:8b
SQL_AGENT_HOST                  Bind host, default 127.0.0.1
SQL_AGENT_PORT                  Bind port, default 8000
SQL_AGENT_RELOAD                Enable reload only for local development
SQL_AGENT_ALLOWED_HOSTS         Comma-separated allowed Host headers
SQL_AGENT_ALLOWED_ORIGINS       Comma-separated CORS origins, if needed
SQL_AGENT_AGENT_TIMEOUT_SECONDS Max time for one agent request
SQL_AGENT_MAX_QUESTION_CHARS    Max user question length
SQL_AGENT_MAX_REQUEST_BYTES     Max HTTP request body size
SQL_AGENT_ACCESS_KEY            Optional API access key for browser users
```

PowerShell example:

```powershell
$env:SQL_AGENT_DATABASE_URL = "mssql+pyodbc://localhost/YourDatabase?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
python -m uvicorn sql_agent.web:app --host 127.0.0.1 --port 8000
```

## Production Notes

- Use a read-only SQL Server login. The app validates SQL, but database
  permissions are the real safety boundary.
- Set `SQL_AGENT_ACCESS_KEY` for any shared environment. Users enter this key
  in the browser before API calls are allowed.
- Put the FastAPI app behind a reverse proxy such as IIS, Nginx, or a managed
  platform proxy for TLS, compression, and public routing.
- Set `SQL_AGENT_ALLOWED_HOSTS` to the real domain names used in production.
- Set `SQL_AGENT_ALLOWED_ORIGINS` only if the frontend is served from a
  different origin than the API.
- Keep `SQL_AGENT_RELOAD=false` in production.
- Monitor `/health/live` for process liveness and `/health/ready` for database
  readiness.

## Verification

Run tests with the same Python interpreter used for the app:

```powershell
python -m pytest -q
```
