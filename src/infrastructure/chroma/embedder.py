
"""
CoFoundr AI — Phase 6 Async Embedder.

Responsibilities:
- Embed document texts in configurable batches.
- Embed individual queries with retrieval-specific task types.
- Run synchronous Gemini calls in worker threads.
- Preserve input ordering.
- Reject empty text before making API calls.
- Enforce consistent vector dimensions.

Key rotation and retry behavior remain in GeminiTool.
"""

import asyncio
import logging

from typing import Any

from src.core.config import settings

RAG_EMBEDDING_BATCH_SIZE = settings.rag_embedding_batch_size

from src.tools.gemini_tool import gemini_tool


logger = logging.getLogger(__name__)

DOCUMENT_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "RETRIEVAL_QUERY"

DEVELOPMENT_BATCH_PAUSE_SECONDS = 0.1


class Embedder:
    """Provide asynchronous document and query embedding methods."""

    def __init__(
        self,
        tool: Any = None,
        batch_size: int = RAG_EMBEDDING_BATCH_SIZE,
    ) -> None:
        if isinstance(batch_size, bool) or not isinstance(batch_size, int):
            raise TypeError("batch_size must be an integer.")

        if batch_size < 1:
            raise ValueError("batch_size must be at least 1.")

        self._tool = tool if tool is not None else gemini_tool
        self._batch_size = batch_size
        self._embedding_dimension: int | None = None

    @staticmethod
    def _validate_text(text: str, index: int | None = None) -> None:
        """Reject empty or whitespace-only input."""
        location = f" at index {index}" if index is not None else ""

        if not isinstance(text, str):
            raise TypeError(f"Embedding text{location} must be a string.")

        if not text.strip():
            raise ValueError(
                f"Embedding text{location} must not be empty or whitespace-only."
            )

    def _validate_vectors(
        self,
        vectors: list[list[float]],
        expected_count: int,
    ) -> list[list[float]]:
        """Validate vector count and consistent dimensions."""
        if len(vectors) != expected_count:
            raise ValueError(
                f"Expected {expected_count} embedding vectors, "
                f"received {len(vectors)}."
            )

        for index, vector in enumerate(vectors):
            if not vector:
                raise ValueError(
                    f"Embedding vector at index {index} is empty."
                )

            if not all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in vector
            ):
                raise TypeError(
                    f"Embedding vector at index {index} "
                    "contains a non-numeric value."
                )

            if self._embedding_dimension is None:
                self._embedding_dimension = len(vector)

            if len(vector) != self._embedding_dimension:
                raise ValueError(
                    "Embedding dimension mismatch: expected "
                    f"{self._embedding_dimension}, received {len(vector)}."
                )

        return vectors

    async def _embed_batch(
        self,
        texts: list[str],
        task_type: str,
    ) -> list[list[float]]:
        """Call the synchronous Gemini wrapper in a worker thread."""
        chunks = [{"text": text} for text in texts]

        vectors = await asyncio.to_thread(
            self._tool.generate_embedding,
            chunks,
            task_type=task_type,
        )

        return self._validate_vectors(
            vectors=vectors,
            expected_count=len(texts),
        )

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Embed document texts in batches, preserving input order.

        Empty input returns an empty list without calling Gemini.
        """
        if not isinstance(texts, list):
            raise TypeError("texts must be a list of strings.")

        for index, text in enumerate(texts):
            self._validate_text(text, index)

        if not texts:
            return []

        all_vectors: list[list[float]] = []

        is_development = settings.environment.lower() == "development"

        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]

            batch_vectors = await self._embed_batch(
                texts=batch,
                task_type=DOCUMENT_TASK_TYPE,
            )

            all_vectors.extend(batch_vectors)

            has_more_batches = start + self._batch_size < len(texts)

            if is_development and has_more_batches:
                await asyncio.sleep(DEVELOPMENT_BATCH_PAUSE_SECONDS)

        if len(all_vectors) != len(texts):
            raise RuntimeError(
                "Embedding output count does not match input count."
            )

        return all_vectors

    async def embed_query(self, text: str) -> list[float]:
        """Embed one query using the retrieval-query task type."""
        self._validate_text(text)

        vectors = await self._embed_batch(
            texts=[text],
            task_type=QUERY_TASK_TYPE,
        )

        return vectors[0]


# Shared instance for application use.
embedder = Embedder()


if __name__ == "__main__":
    async def _smoke_test() -> None:
        """Make a real API call and check basic vector properties."""
        document_text = "A startup helps students manage their projects."
        query_text = "A startup helps students manage their projects."

        document_vectors = await embedder.embed_documents([document_text])
        query_vector = await embedder.embed_query(query_text)

        document_vector = document_vectors[0]

        assert len(document_vector) == len(query_vector)

        print("Document vector dimensions:", len(document_vector))
        print("Query vector dimensions:", len(query_vector))
        print("Same text, document and query vectors generated.")
        print(
            "Vectors differ:",
            any(
                left != right
                for left, right in zip(document_vector, query_vector)
            ),
        )

    asyncio.run(_smoke_test())
