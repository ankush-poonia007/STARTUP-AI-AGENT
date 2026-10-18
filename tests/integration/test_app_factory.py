"""Integration tests for application startup wiring and health routes."""

import importlib

from fastapi.testclient import TestClient


class FakeConnection:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, query):
        return 1


class FakeEngine:
    def __init__(self):
        self.dispose_calls = 0

    def connect(self):
        return FakeConnection()

    async def dispose(self):
        self.dispose_calls += 1


class FakeChromaClient:
    def heartbeat(self):
        return 1


def test_app_lifespan_wires_resources_and_serves_health(monkeypatch):
    app_module = importlib.import_module("src.app")
    engine = FakeEngine()
    chroma_client = FakeChromaClient()
    session_factory = object()
    documents = object()
    memories = object()
    file_storage = object()
    embedder = object()

    monkeypatch.setattr(
        app_module,
        "create_database_engine",
        lambda database_url: engine,
    )
    monkeypatch.setattr(
        app_module,
        "create_session_factory",
        lambda database_engine: session_factory,
    )
    monkeypatch.setattr(
        app_module,
        "create_chroma_client",
        lambda persist_directory: chroma_client,
    )
    monkeypatch.setattr(
        app_module,
        "create_phase6_collections",
        lambda client: (documents, memories),
    )
    monkeypatch.setattr(
        app_module,
        "create_file_storage",
        lambda: file_storage,
    )
    monkeypatch.setattr(
        app_module,
        "_create_embedder",
        lambda: embedder,
    )

    application = app_module.create_app()
    with TestClient(application) as client:
        assert application.state.engine is engine
        assert application.state.session_factory is session_factory
        assert application.state.chroma_client is chroma_client
        assert application.state.chroma_documents is documents
        assert application.state.chroma_memories is memories
        assert application.state.file_storage is file_storage
        assert application.state.embedder is embedder

        live = client.get("/api/v1/health/live")
        assert live.status_code == 200
        assert live.json() == {"status": "ok"}
        assert live.headers.get("X-Request-ID")

        ready = client.get("/api/v1/health/ready")
        assert ready.status_code == 200
        assert ready.json() == {
            "status": "ok",
            "dependencies": {
                "postgres": "ok",
                "chroma": "ok",
            },
        }

        missing = client.get(
            "/api/v1/not-found",
            headers={"Origin": "http://localhost:3000"},
        )
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "NOT_FOUND"
        assert missing.headers["access-control-allow-origin"] == (
            "http://localhost:3000"
        )
        assert missing.headers.get("X-Request-ID")

        hostile_origin = client.get(
            "/api/v1/health/live",
            headers={"Origin": "https://attacker.invalid"},
        )
        assert "access-control-allow-origin" not in hostile_origin.headers

    assert engine.dispose_calls == 1
