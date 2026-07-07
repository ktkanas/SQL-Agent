from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from sql_agent.agent import ask_database, extract_agent_trace
from sql_agent.database import engine

WEB_DIR = Path(__file__).parent / "web"

app = FastAPI(title="SQL Agent", version="0.1.0")
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    sql_queries: list[str]
    tool_results: list[dict[str, str]]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/tables")
def tables() -> dict:
    sql = text("""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE='BASE TABLE'
    ORDER BY TABLE_NAME
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(sql).fetchall()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"tables": [row[0] for row in rows]}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict:
    try:
        result = await run_in_threadpool(ask_database, request.question.strip())
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return extract_agent_trace(result)


def main() -> None:
    uvicorn.run("sql_agent.web:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
