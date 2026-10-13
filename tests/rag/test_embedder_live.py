
import math

import pytest

from src.infrastructure.chroma.embedder import Embedder
from src.tools.gemini_tool import gemini_tool


@pytest.mark.external
@pytest.mark.asyncio
async def test_real_gemini_document_and_query_embeddings():
    embedder = Embedder(tool=gemini_tool)

    text = (
        "PostgreSQL stores structured application data, "
        "while vector databases support semantic retrieval."
    )

    # Exactly one document embedding request.
    document_vectors = await embedder.embed_documents([text])
    document_vector = document_vectors[0]

    # Exactly one query embedding request.
    query_vector = await embedder.embed_query(text)

    # Both responses must be valid, non-empty numeric vectors.
    assert document_vector
    assert query_vector

    assert all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        for value in document_vector + query_vector
    )

    # Document and query embeddings must share one dimension.
    assert len(document_vector) == len(query_vector)

    # Verify the distinct Gemini task configurations produce
    # different vectors for this identical input.
    assert document_vector != query_vector

    print("Gemini live embedding test passed.")
    print(f"Embedding dimension: {len(document_vector)}")
    print("Document/query vectors differ: verified.")
