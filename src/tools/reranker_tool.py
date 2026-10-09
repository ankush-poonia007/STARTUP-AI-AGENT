
from __future__ import annotations

import json
import logging
import math
import os
import urllib.error
import urllib.request
from typing import Dict, List, Any

from src.config.settings import DEFAULT_RERANK_TOP_K,JINA_API_KEY,JINA_RERANKER_MODEL

logger = logging.getLogger(__name__)

# ============================================================
# JINA RERANKER CONFIGURATION
# ============================================================

JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"

JINA_API_TIMEOUT_SECONDS = 30
MAX_DOCUMENTS_PER_REQUEST = 100


# ============================================================
# JINA API CLIENT
# ============================================================

def _request_jina_rerank(
    query: str,
    documents: List[str],
    top_n: int,
) -> List[Dict[str, Any]]:
    """Call Jina's hosted reranking API."""

    api_key = JINA_API_KEY

    if not api_key:
        raise RuntimeError(
            "JINA_API_KEY is missing. Add it to your environment "
            "or load it through your existing .env configuration."
        )

    payload = {
        "model": JINA_RERANKER_MODEL,
        "query": query,
        "documents": documents,
        "top_n": top_n,
        "return_documents": False,
    }

    request = urllib.request.Request(
        JINA_RERANK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=JINA_API_TIMEOUT_SECONDS,
        ) as response:
            response_body = response.read().decode("utf-8")

    except urllib.error.HTTPError as error:
        # Do not log request headers or API credentials.
        status_code = error.code

        if status_code == 401:
            message = "Jina authentication failed. Check JINA_API_KEY."
        elif status_code == 403:
            message = "Jina rejected the request. Check model access and account limits."
        elif status_code == 429:
            message = "Jina rate limit or quota reached."
        elif status_code >= 500:
            message = "Jina service returned a server error."
        else:
            message = f"Jina request failed with HTTP {status_code}."

        logger.error("%s", message)
        raise RuntimeError(message) from None

    except (TimeoutError, urllib.error.URLError) as error:
        logger.error(
            "Jina request failed due to a network or timeout error."
        )
        raise RuntimeError(
            "Unable to reach Jina reranking API."
        ) from error

    try:
        response_data = json.loads(response_body)
        results = response_data["results"]

    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError(
            "Jina returned an invalid or unexpected response."
        ) from error

    if not isinstance(results, list):
        raise RuntimeError("Jina response results must be a list.")

    validated_results = []
    seen_indices = set()

    for result in results:
        if not isinstance(result, dict):
            raise RuntimeError("Jina returned a malformed result.")

        index = result.get("index")
        score = result.get("relevance_score")

        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or index >= len(documents)
        ):
            raise RuntimeError("Jina returned an invalid document index.")

        if index in seen_indices:
            raise RuntimeError("Jina returned a duplicate document index.")

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
        ):
            raise RuntimeError("Jina returned an invalid relevance score.")

        seen_indices.add(index)

        validated_results.append(
            {
                "index": index,
                "relevance_score": float(score),
            }
        )

    return validated_results


# ============================================================
# RERANK FUNCTION — PUBLIC INTERFACE PRESERVED
# ============================================================

def rerank(
    query: str,
    retrieved_chunks: List[Dict],
    top_k: int = DEFAULT_RERANK_TOP_K,
) -> List[Dict]:
    """
    Re-rank retrieved chunks using Jina's hosted reranking API.

    Expected chunk structure:
        {
            "text": "...",
            "metadata": {...},
            "rrf_score": float
        }

    Returns the original chunk structure with an additional
    "rerank_score" field, sorted by descending relevance.
    """

    if not retrieved_chunks:
        return []

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    if len(retrieved_chunks) > MAX_DOCUMENTS_PER_REQUEST:
        raise ValueError(
            f"Received {len(retrieved_chunks)} chunks; maximum supported "
            f"per request is {MAX_DOCUMENTS_PER_REQUEST}."
        )

    for index, chunk in enumerate(retrieved_chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f"Chunk at index {index} must be a dictionary.")

        if not isinstance(chunk.get("text"), str) or not chunk["text"].strip():
            raise ValueError(
                f"Chunk at index {index} must contain non-empty text."
            )

    top_k = min(top_k, len(retrieved_chunks))

    documents = [chunk["text"] for chunk in retrieved_chunks]

    logger.info(
        "Reranking %d chunks using Jina model %s.",
        len(documents),
        JINA_RERANKER_MODEL,
    )

    results = _request_jina_rerank(
        query=query,
        documents=documents,
        top_n=top_k,
    )

    reranked_chunks = []

    for result in results:
        original_chunk = retrieved_chunks[result["index"]]

        # Preserve original metadata and fields.
        updated_chunk = original_chunk.copy()
        updated_chunk["rerank_score"] = result["relevance_score"]

        reranked_chunks.append(updated_chunk)

    reranked_chunks.sort(
        key=lambda chunk: chunk["rerank_score"],
        reverse=True,
    )

    logger.info(
        "Jina reranking completed. Returning %d chunks.",
        len(reranked_chunks),
    )

    return reranked_chunks[:top_k]


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    sample_query = "Who introduced the Transformer architecture?"

    sample_chunks = [
        {
            "text": (
                "Attention Is All You Need introduced the "
                "Transformer architecture in 2017."
            ),
            "metadata": {"page": 2},
            "rrf_score": 0.0323,
        },
        {
            "text": (
                "Artificial General Intelligence aims to "
                "achieve human-level reasoning."
            ),
            "metadata": {"page": 1},
            "rrf_score": 0.0161,
        },
        {
            "text": (
                "Scaling laws explain how model performance "
                "improves with compute and data."
            ),
            "metadata": {"page": 5},
            "rrf_score": 0.0158,
        },
    ]

    results = rerank(
        query=sample_query,
        retrieved_chunks=sample_chunks,
    )

    print("\n" + "=" * 80)
    print("JINA RERANK RESULTS")
    print("=" * 80)

    for rank, chunk in enumerate(results, start=1):
        print(f"\nRank         : {rank}")
        print(f"Rerank Score : {chunk['rerank_score']:.4f}")
        print(f"RRF Score    : {chunk['rrf_score']:.4f}")
        print(f"Metadata     : {chunk['metadata']}")
        print(f"Preview      : {chunk['text'][:120]}")

    print("\n" + "=" * 80)
