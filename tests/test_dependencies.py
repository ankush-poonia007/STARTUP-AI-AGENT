
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.chroma.dependency import (
    get_chroma_documents,
    get_chroma_memories,
)
from src.infrastructure.embedding.dependency import get_embedder
from src.infrastructure.storage.dependency import get_file_storage


def test_dependency_instance_identity():
    app = FastAPI()

    documents = object()
    memories = object()
    storage = object()
    embedder = object()

    app.state.chroma_documents = documents
    app.state.chroma_memories = memories
    app.state.file_storage = storage
    app.state.embedder = embedder

    @app.get("/dependencies")
    def read_dependencies(
        docs=Depends(get_chroma_documents),
        mems=Depends(get_chroma_memories),
        files=Depends(get_file_storage),
        embeddings=Depends(get_embedder),
    ):
        return {
            "documents": docs is documents,
            "memories": mems is memories,
            "storage": files is storage,
            "embedder": embeddings is embedder,
        }

    with TestClient(app) as client:
        response = client.get("/dependencies")

    assert response.status_code == 200
    assert response.json() == {
        "documents": True,
        "memories": True,
        "storage": True,
        "embedder": True,
    }



def test_missing_state_names_key():
    app = FastAPI()

    @app.get("/embedder")
    def read_embedder(embedder=Depends(get_embedder)):
        return {"available": True}

    with TestClient(app) as client:
        try:
            client.get("/embedder")
            assert False, "Expected missing-state RuntimeError"
        except RuntimeError as exc:
            assert "embedder" in str(exc)
            assert "startup wiring did not run" in str(exc).lower()



def test_embedder_dependency_override():
    app = FastAPI()
    fake_embedder = object()

    app.state.embedder = object()
    app.dependency_overrides[get_embedder] = lambda: fake_embedder

    @app.get("/embedder")
    def read_embedder(embedder=Depends(get_embedder)):
        return {"is_fake": embedder is fake_embedder}

    with TestClient(app) as client:
        response = client.get("/embedder")

    assert response.status_code == 200
    assert response.json() == {"is_fake": True}

        