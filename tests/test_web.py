from fastapi.testclient import TestClient

from sql_agent import web


client = TestClient(web.app, base_url="http://localhost")


def test_live_health_returns_security_headers():
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "x-request-id" in response.headers


def test_chat_rejects_blank_question():
    response = client.post("/api/chat", json={"question": "   "})

    assert response.status_code == 422
    assert response.json()["detail"] == "Question cannot be blank."


def test_chat_returns_agent_trace(monkeypatch):
    class Message:
        content = "There are 10 customers."
        tool_calls = []

    def fake_ask_database(question: str) -> dict:
        assert question == "How many customers?"
        return {"messages": [Message()]}

    monkeypatch.setattr(web, "ask_database", fake_ask_database)

    response = client.post("/api/chat", json={"question": "How many customers?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "There are 10 customers.",
        "sql_queries": [],
        "tool_results": [],
    }


def test_api_key_required_when_configured(monkeypatch):
    original_key = web.settings.access_key
    object.__setattr__(web.settings, "access_key", "secret")

    try:
        blocked = client.get("/api/tables")
        allowed = client.get("/api/tables", headers={"X-SQL-Agent-Key": "secret"})
    finally:
        object.__setattr__(web.settings, "access_key", original_key)

    assert blocked.status_code == 401
    assert allowed.status_code in {200, 503}
