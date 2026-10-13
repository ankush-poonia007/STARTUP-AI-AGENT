
"""
CoFoundr AI — Phase 6 Startup-Scoped Chroma Access.

Responsibilities:
- Enforce startup isolation on every write and query.
- Build Chroma-compatible tenant filters using $and.
- Generate collision-safe document chunk IDs.
- Deactivate document chunks without deleting them.
- Delete all Chroma records belonging to a startup.
- Convert cosine distance to similarity.

Step 5d implementation.
"""

from typing import Any
from uuid import UUID

from chromadb.api.models.Collection import Collection


def validate_startup_id(startup_id: str | UUID) -> str:
    """Validate and normalize a startup identifier."""
    if isinstance(startup_id, UUID):
        return str(startup_id)

    if not isinstance(startup_id, str) or not startup_id.strip():
        raise ValueError("startup_id must be a non-empty string or UUID.")

    normalized = startup_id.strip()

    # Preserve support for non-UUID application identifiers.
    # Reject malformed values that look like UUIDs.
    try:
        UUID(normalized)
    except ValueError:
        if len(normalized) == 36 and normalized.count("-") == 4:
            raise ValueError("startup_id has an invalid UUID format.")

    return normalized


def _validate_record_id(value: str | UUID, field_name: str) -> str:
    """Validate and normalize a document or memory identifier."""
    if isinstance(value, UUID):
        return str(value)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string or UUID.")

    return value.strip()


def make_document_chunk_id(
    document_id: str | UUID,
    chunk_index: int,
) -> str:
    """Create a stable ID independent of chunk text."""
    normalized_document_id = _validate_record_id(
        document_id,
        "document_id",
    )

    if isinstance(chunk_index, bool) or not isinstance(chunk_index, int):
        raise TypeError("chunk_index must be an integer.")

    if chunk_index < 0:
        raise ValueError("chunk_index must not be negative.")

    return f"{normalized_document_id}_{chunk_index}"


def make_memory_id(memory_id: str | UUID) -> str:
    """Normalize a memory ID without deriving it from memory text."""
    return _validate_record_id(memory_id, "memory_id")


def enforce_startup_metadata(
    metadata: dict[str, Any],
    startup_id: str | UUID,
) -> dict[str, Any]:
    """Stamp startup_id into metadata and reject cross-startup writes."""
    if not isinstance(metadata, dict):
        raise TypeError("Each metadata entry must be a dictionary.")

    expected_id = validate_startup_id(startup_id)
    normalized_metadata = dict(metadata)

    existing_id = normalized_metadata.get("startup_id")

    if existing_id is not None:
        existing_id = validate_startup_id(existing_id)

        if existing_id != expected_id:
            raise ValueError(
                "Metadata startup_id conflicts with the requested startup."
            )

    normalized_metadata["startup_id"] = expected_id
    return normalized_metadata


def build_startup_where(
    startup_id: str | UUID,
    extra_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a startup filter with optional conditions joined using $and."""
    normalized_id = validate_startup_id(startup_id)

    if extra_filters is None or extra_filters == {}:
        return {"startup_id": normalized_id}

    if not isinstance(extra_filters, dict):
        raise TypeError("extra_filters must be a dictionary or None.")

    conditions: list[dict[str, Any]] = [
        {"startup_id": normalized_id}
    ]

    for key, value in extra_filters.items():
        if not isinstance(key, str) or not key:
            raise ValueError("Filter keys must be non-empty strings.")

        if key.startswith("$"):
            raise ValueError(
                "Pass simple metadata filters, not top-level operators."
            )

        if key == "startup_id":
            extra_id = validate_startup_id(value)
            if extra_id != normalized_id:
                raise ValueError(
                    "Extra filters cannot target a different startup."
                )
            continue

        conditions.append({key: value})

    return {"$and": conditions}


def write_records(
    collection: Collection,
    startup_id: str | UUID,
    ids: list[str],
    vectors: list[list[float]],
    texts: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    """
    Store records after enforcing startup isolation.

    Every record receives the requested startup_id.
    Conflicting startup IDs are rejected before the write begins.
    """
    normalized_startup_id = validate_startup_id(startup_id)

    if not (len(ids) == len(vectors) == len(texts) == len(metadatas)):
        raise ValueError(
            "ids, vectors, texts, and metadatas must have equal lengths."
        )

    if len(ids) != len(set(ids)):
        raise ValueError("Record IDs must be unique within a write.")

    if not ids:
        return

    if any(not isinstance(record_id, str) or not record_id.strip()
           for record_id in ids):
        raise ValueError("Every record ID must be a non-empty string.")

    if any(not isinstance(text, str) for text in texts):
        raise TypeError("Every document text must be a string.")

    stamped_metadatas = [
        enforce_startup_metadata(metadata, normalized_startup_id)
        for metadata in metadatas
    ]

    # All metadata is validated before the database operation.
    collection.upsert(
        ids=ids,
        embeddings=vectors,
        documents=texts,
        metadatas=stamped_metadatas,
    )


def query_records(
    collection: Collection,
    startup_id: str | UUID,
    query_vector: list[float],
    result_count: int,
    extra_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Query records belonging only to the requested startup.

    Chroma returns nested result lists. For one query vector, access
    the matching records through result["ids"][0], etc.

    Cosine distances are preserved and similarities are also returned.
    """
    validate_startup_id(startup_id)

    if isinstance(result_count, bool) or not isinstance(result_count, int):
        raise TypeError("result_count must be an integer.")

    if result_count < 1:
        raise ValueError("result_count must be at least 1.")

    if not query_vector:
        raise ValueError("query_vector must not be empty.")

    where = build_startup_where(startup_id, extra_filters)

    # Avoid querying an empty collection or requesting more records
    # than the collection contains.
    available_count = collection.count()

    if available_count == 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "similarities": [[]],
        }

    effective_count = min(result_count, available_count)

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=effective_count,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    distances = result.get("distances") or [[]]

    # Chroma's cosine distance is not cosine similarity.
    # Similarity = 1 - distance.
    result["similarities"] = [
        [1.0 - distance for distance in query_distances]
        for query_distances in distances
    ]

    return result


def deactivate_document(
    collection: Collection,
    startup_id: str | UUID,
    document_id: str | UUID,
) -> int:
    """
    Mark all chunks of one startup's document inactive.

    Records remain in Chroma for auditing and analysis.
    Returns the number of records updated.
    """
    normalized_startup_id = validate_startup_id(startup_id)
    normalized_document_id = _validate_record_id(
        document_id,
        "document_id",
    )

    where = build_startup_where(
        normalized_startup_id,
        {"document_id": normalized_document_id},
    )

    existing = collection.get(
        where=where,
        include=["metadatas"],
    )

    record_ids = existing["ids"]
    existing_metadatas = existing.get("metadatas") or []

    if not record_ids:
        return 0

    updated_metadatas: list[dict[str, Any]] = []

    for metadata in existing_metadatas:
        if metadata is None:
            raise ValueError(
                "Cannot deactivate a record without metadata."
            )

        # Defensive check: never update a record outside this startup.
        stamped = enforce_startup_metadata(
            metadata,
            normalized_startup_id,
        )
        stamped["is_active"] = False
        updated_metadatas.append(stamped)

    collection.update(
        ids=record_ids,
        metadatas=updated_metadatas,
    )

    return len(record_ids)



def delete_by_startup(
    collection: Collection,
    startup_id: str | UUID,
) -> int:
    """
    Delete every Chroma record belonging to one startup in bounded batches.

    This does not delete PostgreSQL rows or files on disk.
    Returns the number of records selected for deletion.
    """
    normalized_startup_id = validate_startup_id(startup_id)
    where = {"startup_id": normalized_startup_id}
    batch_size = 500
    deleted_count = 0

    while True:
        existing = collection.get(
            where=where,
            limit=batch_size,
            include=[],
        )

        record_ids = existing["ids"]

        if not record_ids:
            break

        collection.delete(ids=record_ids)
        deleted_count += len(record_ids)

    return deleted_count



if __name__ == "__main__":
    import tempfile

    from src.infrastructure.chroma.client import create_chroma_client
    from src.infrastructure.chroma.collection import (
        create_phase6_collections,
    )

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        client = create_chroma_client(temp_dir)
        documents, _ = create_phase6_collections(client)

        # Write two records for startup A.
        write_records(
            collection=documents,
            startup_id="startup-a",
            ids=[
                make_document_chunk_id("document-1", 0),
                make_document_chunk_id("document-1", 1),
            ],
            vectors=[
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
            ],
            texts=["First chunk", "Second chunk"],
            metadatas=[
                {
                    "document_id": "document-1",
                    "filename": "test.txt",
                    "page_number": 1,
                    "chunk_index": 0,
                    "is_active": True,
                    "record_type": "document_chunk",
                },
                {
                    "document_id": "document-1",
                    "filename": "test.txt",
                    "page_number": 1,
                    "chunk_index": 1,
                    "is_active": True,
                    "record_type": "document_chunk",
                },
            ],
        )

        # A startup-scoped query returns only startup A's records.
        result = query_records(
            collection=documents,
            startup_id="startup-a",
            query_vector=[1.0, 0.0, 0.0],
            result_count=10,
            extra_filters={
                "is_active": True,
                "record_type": "document_chunk",
            },
        )
        assert len(result["ids"][0]) == 2
        assert len(result["similarities"][0]) == 2
        print("PASS: Startup-scoped query and $and filters work.")

        # Conflicting startup metadata must never be written.
        try:
            write_records(
                collection=documents,
                startup_id="startup-a",
                ids=["cross-tenant-record"],
                vectors=[[0.0, 0.0, 1.0]],
                texts=["Must not be written"],
                metadatas=[{"startup_id": "startup-b"}],
            )
        except ValueError:
            print("PASS: Cross-startup write rejected.")
        else:
            raise AssertionError("Cross-startup write was accepted.")

        # Deactivation preserves records but marks them inactive.
        changed = deactivate_document(
            documents,
            "startup-a",
            "document-1",
        )
        assert changed == 2

        inactive = documents.get(
            where=build_startup_where(
                "startup-a",
                {"is_active": False},
            ),
            include=["metadatas"],
        )
        assert len(inactive["ids"]) == 2
        print("PASS: Document deactivation preserves records.")

        # Startup B cannot see startup A's records.
        other_startup = query_records(
            documents,
            "startup-b",
            [1.0, 0.0, 0.0],
            5,
        )
        assert other_startup["ids"] == [[]]
        print("PASS: Startup isolation and empty matches work.")

        deleted = delete_by_startup(documents, "startup-a")
        assert deleted == 2
        assert documents.count() == 0
        print("PASS: Delete-by-startup removes scoped records.")
