
import pytest

from src.infrastructure.chroma.embedder import (
    DOCUMENT_TASK_TYPE,
    QUERY_TASK_TYPE,
    Embedder,
)


class FakeEmbeddingTool:
    def __init__(self):
        self.calls = []

    def generate_embedding(self, chunks, task_type):
        self.calls.append(
            {
                "texts": [chunk["text"] for chunk in chunks],
                "task_type": task_type,
            }
        )

        if task_type == DOCUMENT_TASK_TYPE:
            vector = [1.0, 2.0]
        elif task_type == QUERY_TASK_TYPE:
            vector = [2.0, 1.0]
        else:
            raise ValueError(f"Unexpected task type: {task_type}")

        return [vector.copy() for _ in chunks]
    

@pytest.mark.asyncio
async def test_document_and_query_use_distinct_task_types():
    tool = FakeEmbeddingTool()
    embedder = Embedder(tool=tool, batch_size=15)

    await embedder.embed_documents(["same text"])
    await embedder.embed_query("same text")

    assert tool.calls[0]["task_type"] == DOCUMENT_TASK_TYPE
    assert tool.calls[1]["task_type"] == QUERY_TASK_TYPE


@pytest.mark.asyncio
async def test_empty_document_input_does_not_call_tool():
    tool = FakeEmbeddingTool()
    embedder = Embedder(tool=tool)

    assert await embedder.embed_documents([]) == []
    assert tool.calls == []


@pytest.mark.asyncio
async def test_45_texts_use_three_batches_in_input_order():
    tool = FakeEmbeddingTool()
    embedder = Embedder(tool=tool, batch_size=15)
    texts = [f"text-{index}" for index in range(45)]

    vectors = await embedder.embed_documents(texts)

    assert [len(call["texts"]) for call in tool.calls] == [15, 15, 15]
    assert [
        text for call in tool.calls for text in call["texts"]
    ] == texts
    assert len(vectors) == 45


@pytest.mark.asyncio
async def test_query_and_document_vectors_have_matching_dimensions():
    tool = FakeEmbeddingTool()
    embedder = Embedder(tool=tool)

    document_vector = (await embedder.embed_documents(["same text"]))[0]
    query_vector = await embedder.embed_query("same text")

    assert len(document_vector) == len(query_vector) == 2
    assert document_vector != query_vector


@pytest.mark.asyncio
async def test_inconsistent_vector_dimensions_are_rejected():
    class InconsistentTool:
        def __init__(self):
            self.calls = 0

        def generate_embedding(self, chunks, task_type):
            self.calls += 1
            if self.calls == 1:
                return [[1.0, 2.0]]
            return [[1.0, 2.0, 3.0]]

    embedder = Embedder(tool=InconsistentTool(), batch_size=1)

    await embedder.embed_documents(["first"])

    with pytest.raises(ValueError, match="dimension mismatch"):
        await embedder.embed_query("second")
