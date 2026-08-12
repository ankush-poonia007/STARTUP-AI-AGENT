import os
import hashlib

import chromadb

from src.config.settings import (
    DEFAULT_VECTOR_TOP_K,
    CHROMA_DB_PATH,
)


def add_documents(chunks: list, embeddings: list):    # called ONCE at ingestion time
    client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH
    )

    collection = client.get_or_create_collection(
        name="data_storage"
    )

    ids_list = []
    embeddings_list = []
    documents_list = []
    metadatas_list = []

    for chunk, embedding in zip(chunks, embeddings):

        # MD5 of chunk text — deterministic unique ID, prevents duplicate storage
        ids_list.append(
            hashlib.md5(
                chunk["text"].encode()
            ).hexdigest()
        )

        # embedding.values is the raw float list — ChromaDB stores this as the vector
        embeddings_list.append(embedding)

        documents_list.append(chunk["text"])

        # Metadata stored per chunk — enables page-level citations and
        # Phase 4's where={"file_name": ...} multi-document filtering
        metadatas_list.append({
            "page_number": chunk["page_number"],
            "file_name": chunk["file_name"]
        })

    collection.add(
        ids=ids_list,
        embeddings=embeddings_list,
        documents=documents_list,
        metadatas=metadatas_list
    )

    return "Data ingestion complete. Document saved successfully."


def query_collection(
    user_input: list,
    where: dict | None = None,
    top_k=DEFAULT_VECTOR_TOP_K
):    # called at search time

    client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH
    )

    collection = client.get_or_create_collection(
        name="data_storage"
    )

    query_arguments = {
        "query_embeddings": user_input,
        "n_results": top_k,
        "include": [
            "documents",
            "metadatas",
            "distances"
        ],
    }

    if where is not None:
        query_arguments["where"] = where

    results = collection.query(
        **query_arguments
    )

    if results["documents"][0]:
        return results
    else:
        return {}


def normalize_chroma_results(results: dict) -> list:
    """
    Convert raw ChromaDB results into the standard
    {"text", "metadata"} chunk format.
    """

    if not results:
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    normalized_results = []

    for text, metadata in zip(documents, metadatas):
        normalized_results.append({
            "text": text,
            "metadata": metadata
        })

    return normalized_results


def reciprocal_rank_fusion(
    chroma_results: list,
    bm25_results: list
) -> list:

    fused_results = {}
    
    k = 60 
    
    # Process ChromaDB results
    for rank, chunk in enumerate(chroma_results, start=1):
        text = chunk["text"]
        score = 1 / (k + rank)

        if text not in fused_results:
            fused_results[text] = {
                "text": text,
                "metadata": chunk["metadata"],
                "rrf_score": score
            }
        else:
            fused_results[text]["rrf_score"] += score

    # Process BM25 results
    for rank, chunk in enumerate(bm25_results, start=1):
        text = chunk["text"]
        score = 1 / (k + rank)

        if text not in fused_results:
            fused_results[text] = {
                "text": text,
                "metadata": chunk["metadata"],
                "rrf_score": score
            }
        else:
            fused_results[text]["rrf_score"] += score

    # Sort by RRF score in descending order
    new_ranks = sorted(
        fused_results.values(),
        key=lambda chunk: chunk["rrf_score"],
        reverse=True
    )

    return new_ranks


if __name__ == "__main__":

    # 1. Mock Chunks (Input Data)
    mock_chunks = [
        {
            "text": "The Quick Start guide covers basic authentication steps using API keys.",
            "page_number": 1,
            "file_name": "api_documentation.pdf"
        },
        {
            "text": "Rate limits are enforced at 60 requests per minute per IP address.",
            "page_number": 4,
            "file_name": "api_documentation.pdf"
        },
        {
            "text": "Vector databases index high-dimensional embeddings for fast similarity search.",
            "page_number": 12,
            "file_name": "architecture_overview.pdf"
        }
    ]

    # 2. Mock Embeddings (Matching vectors)
    mock_embeddings = [
        [0.12, -0.43, 0.89, 0.05],      # Vector for Chunk 1
        [-0.71, 0.22, 0.15, -0.38],     # Vector for Chunk 2
        [0.55, 0.61, -0.02, 0.74]       # Vector for Chunk 3
    ]

    # Add all mock documents once
    print(
        add_documents(
            chunks=mock_chunks,
            embeddings=mock_embeddings
        )
    )

    # Query using one embedding
    query_embedding = [mock_embeddings[0]]

    raw_results = query_collection(
        user_input=query_embedding
    )

    # Normalize ChromaDB results before RRF
    chroma_results = normalize_chroma_results(
        raw_results
    )

    print("\nChromaDB Results:")
    print(chroma_results)

    # Mock BM25 results using the same standardized format
    bm25_results = [
        {
            "text": mock_chunks[1]["text"],
            "metadata": {
                "page_number": mock_chunks[1]["page_number"],
                "file_name": mock_chunks[1]["file_name"]
            }
        },
        {
            "text": mock_chunks[0]["text"],
            "metadata": {
                "page_number": mock_chunks[0]["page_number"],
                "file_name": mock_chunks[0]["file_name"]
            }
        }
    ]

    # Apply RRF
    fused_results = reciprocal_rank_fusion(
        chroma_results=chroma_results,
        bm25_results=bm25_results
    )

    print("\nRRF Results:")

    for rank, chunk in enumerate(
        fused_results,
        start=1
    ):
        print(
            f"\nRank {rank}"
        )
        print(
            f"Text: {chunk['text']}"
        )
        print(
            f"Metadata: {chunk['metadata']}"
        )
        print(
            f"RRF Score: {chunk['rrf_score']}"
        )