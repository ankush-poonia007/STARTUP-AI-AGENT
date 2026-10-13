
import pytest
import chromadb

from src.infrastructure.chroma.collection import create_phase6_collections
from src.infrastructure.chroma.scoped import delete_by_startup

from src.infrastructure.chroma.scoped import (
    build_startup_where,
    query_records,
    write_records,
)


@pytest.fixture
def documents(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    documents, _ = create_phase6_collections(client)
    yield documents
    client.clear_system_cache()

def test_delete_by_startup_preserves_other_startups_records(documents):
    write_one(documents, "startup-a", "record-a", "startup A data")
    write_one(documents, "startup-b", "record-b", "startup B data")

    deleted_count = delete_by_startup(documents, "startup-a")

    assert deleted_count == 1
    assert documents.get(ids=["record-a"])["ids"] == []
    assert documents.get(ids=["record-b"])["ids"] == ["record-b"]
    
    
def write_one(collection, startup_id, record_id, text, active=True):
    write_records(
        collection=collection,
        startup_id=startup_id,
        ids=[record_id],
        vectors=[[1.0, 0.0, 0.0]],
        texts=[text],
        metadatas=[
            {
                "document_id": record_id,
                "filename": "test.txt",
                "page_number": 1,
                "chunk_index": 0,
                "is_active": active,
                "record_type": "document_chunk",
            }
        ],
    )


def test_startup_cannot_retrieve_another_startups_records(documents):
    write_one(documents, "startup-a", "record-a", "shared text")
    write_one(documents, "startup-b", "record-b", "private text")

    result = query_records(
        documents, "startup-a", [1.0, 0.0, 0.0], 10
    )

    assert result["ids"][0] == ["record-a"]


def test_identical_text_is_stored_independently_per_startup(documents):
    write_one(documents, "startup-a", "record-a", "identical text")
    write_one(documents, "startup-b", "record-b", "identical text")

    result_a = query_records(
        documents, "startup-a", [1.0, 0.0, 0.0], 10
    )
    result_b = query_records(
        documents, "startup-b", [1.0, 0.0, 0.0], 10
    )

    assert result_a["ids"][0] == ["record-a"]
    assert result_b["ids"][0] == ["record-b"]


def test_combined_filters_use_and(documents):
    result = build_startup_where(
        "startup-a",
        {"is_active": True, "record_type": "document_chunk"},
    )

    assert result == {
        "$and": [
            {"startup_id": "startup-a"},
            {"is_active": True},
            {"record_type": "document_chunk"},
        ]
    }


def test_query_can_exclude_inactive_records(documents):
    write_one(documents, "startup-a", "active", "active text", True)
    write_one(documents, "startup-a", "inactive", "inactive text", False)

    result = query_records(
        documents,
        "startup-a",
        [1.0, 0.0, 0.0],
        10,
        extra_filters={"is_active": True},
    )

    assert result["ids"][0] == ["active"]


def test_records_survive_chroma_client_restart(tmp_path):
    from src.infrastructure.chroma.scoped import write_records, query_records

    persist_path = str(tmp_path / "persistent_chroma")
    startup_id = "startup-persistence"

    client_a = chromadb.PersistentClient(path=persist_path)
    documents_a, _ = create_phase6_collections(client_a)

    write_one(
        documents_a,
        startup_id,
        "persistent-record",
        "survive client restart",
    )

    # Release the first client and reopen the same persisted directory.
    del documents_a
    del client_a

    client_b = chromadb.PersistentClient(path=persist_path)
    documents_b, _ = create_phase6_collections(client_b)

    result = query_records(
        documents_b,
        startup_id,
        [1.0, 0.0, 0.0],
        10,
    )

    assert result["ids"][0] == ["persistent-record"]
