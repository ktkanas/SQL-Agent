import os
import secrets
from dataclasses import dataclass, field


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


def _get_list(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("SQL_AGENT_APP_NAME", "SQL Agent")
    app_version: str = os.getenv("SQL_AGENT_APP_VERSION", "0.1.0")
    environment: str = os.getenv("SQL_AGENT_ENV", "local")
    database_url: str = os.getenv(
        "SQL_AGENT_DATABASE_URL",
        "mssql+pyodbc://localhost/visaDB_copy"
        "?driver=ODBC+Driver+17+for+SQL+Server"
        "&trusted_connection=yes",
    )
    ollama_model: str = os.getenv("SQL_AGENT_OLLAMA_MODEL", "qwen3:8b")
    host: str = os.getenv("SQL_AGENT_HOST", "127.0.0.1")
    port: int = _get_int("SQL_AGENT_PORT", 8000)
    reload: bool = _get_bool("SQL_AGENT_RELOAD", False)
    log_level: str = os.getenv("SQL_AGENT_LOG_LEVEL", "info")
    max_question_chars: int = _get_int("SQL_AGENT_MAX_QUESTION_CHARS", 2000)
    max_request_bytes: int = _get_int("SQL_AGENT_MAX_REQUEST_BYTES", 16_384)
    agent_timeout_seconds: int = _get_int("SQL_AGENT_AGENT_TIMEOUT_SECONDS", 120)
    access_key: str = os.getenv("SQL_AGENT_ACCESS_KEY", "")
    allowed_origins: list[str] = field(default_factory=list)
    allowed_hosts: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_origins", _get_list("SQL_AGENT_ALLOWED_ORIGINS"))
        hosts = _get_list("SQL_AGENT_ALLOWED_HOSTS")
        if not hosts:
            hosts = ["127.0.0.1", "localhost"]
        object.__setattr__(self, "allowed_hosts", hosts)

    def access_key_matches(self, value: str) -> bool:
        if not self.access_key:
            return True
        return secrets.compare_digest(value, self.access_key)


settings = Settings()
