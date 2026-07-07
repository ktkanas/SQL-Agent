import asyncio
import logging
import time
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from sql_agent.agent import ask_database, extract_agent_trace
from sql_agent.database import engine
from sql_agent.settings import settings

WEB_DIR = Path(__file__).parent / "web"
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version=settings.app_version)

if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=settings.max_question_chars)


class ChatResponse(BaseModel):
    answer: str
    sql_queries: list[str]
    tool_results: list[dict[str, str]]


@app.middleware("http")
async def production_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    content_length = request.headers.get("content-length")
    try:
        request_bytes = int(content_length) if content_length else 0
    except ValueError:
        request_bytes = 0

    if request_bytes > settings.max_request_bytes:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body is too large.", "request_id": request_id},
        )

    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error", extra={"request_id": request_id})
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error.", "request_id": request_id},
        )

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        "%s %s -> %s in %sms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        extra={"request_id": request_id},
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health/live")
def health_live() -> dict:
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/ready")
def health_ready() -> dict:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc

    return {"status": "ok", "database": "ready"}


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
        logger.warning("Could not list database tables: %s", exc)
        raise HTTPException(status_code=503, detail="Database is not available.") from exc

    return {"tables": [row[0] for row in rows]}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be blank.")

    try:
        result = await asyncio.wait_for(
            run_in_threadpool(ask_database, question),
            timeout=settings.agent_timeout_seconds,
        )
    except asyncio.TimeoutError as exc:
        logger.warning("Agent timed out after %s seconds", settings.agent_timeout_seconds)
        raise HTTPException(status_code=504, detail="The agent timed out.") from exc
    except Exception as exc:
        logger.warning("Agent request failed: %s", exc)
        raise HTTPException(status_code=503, detail="The agent is not available.") from exc

    return extract_agent_trace(result)


def main() -> None:
    uvicorn.run(
        "sql_agent.web:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
