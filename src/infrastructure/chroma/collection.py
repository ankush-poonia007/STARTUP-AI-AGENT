
"""
CoFoundr AI — Phase 6 ChromaDB Collections

Responsibilities:
- Create or retrieve document and memory collections.
- Configure cosine distance.
- Require application-supplied embeddings.
- Validate metadata contracts before records are stored.

Startup isolation is implemented separately in scoped.py (Step 5c/5d).
"""

from uuid import UUID
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from src.core.constants import (
    CHROMA_RECORD_TYPE_CHUNK,
    CHROMA_RECORD_TYPE_MEMORY,
)


DOCUMENTS_COLLECTION_NAME = "cofoundr_documents"
MEMORIES_COLLECTION_NAME = "cofoundr_memories"

DOCUMENT_REQUIRED_KEYS = {
    "startup_id",
    "document_id",
    "filename",
    "page_number",
    "chunk_index",
    "is_active",
    "record_type",
}

MEMORY_REQUIRED_KEYS = {
    "startup_id",
    "memory_id",
    "memory_type",
    "importance",
    "is_active",
    "record_type",
}

# Chroma supports these metadata value types.
ALLOWED_METADATA_TYPES = (str, int, float, bool)


def get_or_create_collection(
    client: chromadb.ClientAPI,
    collection_name: str,
) -> Collection:
    """Get or create a collection configured for cosine distance."""
    if not collection_name or not collection_name.strip():
        raise ValueError("collection_name must not be empty.")

    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def create_phase6_collections(
    client: chromadb.ClientAPI,
) -> tuple[Collection, Collection]:
    """Create or retrieve both Phase 6 collections."""
    documents = get_or_create_collection(
        client,
        DOCUMENTS_COLLECTION_NAME,
    )
    memories = get_or_create_collection(
        client,
        MEMORIES_COLLECTION_NAME,
    )

    return documents, memories


def _normalize_metadata(
    metadata: dict[str, Any],
    required_keys: set[str],
    expected_record_type: str,
) -> dict[str, str | int | float | bool]:
    """
    Normalize and validate metadata before sending it to Chroma.

    UUID values become strings. Optional None values are omitted.
    Missing required fields and invalid metadata types are rejected.
    """
    if not isinstance(metadata, dict):
        raise TypeError("Metadata must be a dictionary.")

    normalized: dict[str, str | int | float | bool] = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, UUID):
            value = str(value)

        # bool is a subclass of int, so both are explicitly accepted.
        if not isinstance(value, ALLOWED_METADATA_TYPES):
            raise TypeError(
                f"Invalid metadata value for '{key}': "
                f"{type(value).__name__}. "
                "Allowed types are str, int, float, and bool."
            )

        normalized[key] = value

    missing_keys = required_keys - normalized.keys()
    if missing_keys:
        raise ValueError(
            f"Missing required metadata fields: {sorted(missing_keys)}"
        )

    if normalized["record_type"] != expected_record_type:
        raise ValueError(
            f"record_type must be {expected_record_type!r}; "
            f"received {normalized['record_type']!r}."
        )

    return normalized


def validate_document_metadata(
    metadata: dict[str, Any],
) -> dict[str, str | int | float | bool]:
    """Validate metadata for a document chunk."""
    return _normalize_metadata(
        metadata=metadata,
        required_keys=DOCUMENT_REQUIRED_KEYS,
        expected_record_type=CHROMA_RECORD_TYPE_CHUNK,
    )


def validate_memory_metadata(
    metadata: dict[str, Any],
) -> dict[str, str | int | float | bool]:
    """Validate metadata for a memory record."""
    return _normalize_metadata(
        metadata=metadata,
        required_keys=MEMORY_REQUIRED_KEYS,
        expected_record_type=CHROMA_RECORD_TYPE_MEMORY,
    )


if __name__ == "__main__":
    import tempfile

    from src.infrastructure.chroma.client import create_chroma_client

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        client = create_chroma_client(temp_dir)
        documents, memories = create_phase6_collections(client)

        # Verify collection names and cosine configuration.
        assert documents.name == DOCUMENTS_COLLECTION_NAME
        assert memories.name == MEMORIES_COLLECTION_NAME
        assert documents.metadata["hnsw:space"] == "cosine"
        assert memories.metadata["hnsw:space"] == "cosine"

        # Validate document metadata.
        document_metadata = validate_document_metadata(
            {
                "startup_id": UUID(
                    "11111111-1111-1111-1111-111111111111"
                ),
                "document_id": "document-1",
                "filename": "test.txt",
                "page_number": 1,
                "chunk_index": 0,
                "is_active": True,
                "record_type": CHROMA_RECORD_TYPE_CHUNK,
                "optional_field": None,
            }
        )

        assert isinstance(document_metadata["startup_id"], str)
        assert "optional_field" not in document_metadata

        # Validate memory metadata.
        memory_metadata = validate_memory_metadata(
            {
                "startup_id": "startup-1",
                "memory_id": "memory-1",
                "memory_type": "preference",
                "importance": 0.8,
                "is_active": True,
                "record_type": CHROMA_RECORD_TYPE_MEMORY,
            }
        )

        assert memory_metadata["importance"] == 0.8

        # Reject missing required metadata.
        try:
            validate_document_metadata(
                {
                    "document_id": "document-2",
                    "filename": "missing_startup.txt",
                    "page_number": 1,
                    "chunk_index": 0,
                    "is_active": True,
                    "record_type": CHROMA_RECORD_TYPE_CHUNK,
                }
            )
        except ValueError:
            print("PASS: Missing required metadata is rejected.")
        else:
            raise AssertionError("Missing startup_id was not rejected.")

        # Verify validated metadata can be stored with supplied vectors.
        documents.upsert(
            ids=["document-1_0"],
            embeddings=[[1.0, 0.0, 0.0]],
            documents=["Test document chunk"],
            metadatas=[document_metadata],
        )

        result = documents.get(
            ids=["document-1_0"],
            include=["documents", "metadatas"],
        )

        assert result["ids"] == ["document-1_0"]
        assert result["metadatas"][0]["startup_id"] == str(
            UUID("11111111-1111-1111-1111-111111111111")
        )

        print("PASS: Both collections are configured correctly.")
        print("PASS: Document and memory metadata contracts validated.")
        print("PASS: UUID conversion and None omission work.")
        print("PASS: Validated metadata can be stored and retrieved.")
