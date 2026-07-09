"""
============================================================
BizRadar AI - Cross Encoder Reranker
============================================================

Purpose
-------
Improve retrieval precision by reranking semantic-search
results using a CrossEncoder.

Pipeline
--------

User Query
      │
      ▼
Embedding Search (Top-N)
      │
      ▼
Cross Encoder Reranker
      │
      ▼
Top-K Most Relevant Chunks
      │
      ▼
LLM

Why use a reranker?
-------------------

Embedding search maximizes Recall.

CrossEncoder maximizes Precision.

The embedding model retrieves semantically similar chunks.

The CrossEncoder jointly evaluates the user query and each
candidate chunk before assigning a relevance score.

This significantly improves ranking quality compared to
cosine similarity alone.

Expected Improvements
---------------------

Recall@3
    ≈ 100% (should remain unchanged)

Recall@1
    Significant improvement

MRR
    Significant improvement

Author
------
BizRadar AI
"""

from __future__ import annotations

import logging
from typing import Dict, List

from sentence_transformers import CrossEncoder

from src.config.settings import (
    RERANKER_MODEL,
    DEFAULT_RERANK_TOP_K,
)

logger = logging.getLogger(__name__)

# ============================================================
# MODEL INITIALIZATION
# ============================================================

try:

    logger.info("Loading CrossEncoder model: %s", RERANKER_MODEL)

    reranker = CrossEncoder(
        RERANKER_MODEL,
        max_length=512,
    )

    # Explicit inference mode
    reranker.model.eval()

    logger.info("CrossEncoder loaded successfully.")

except Exception as e:

    logger.exception("Failed to initialize CrossEncoder.")

    raise RuntimeError(
        f"Unable to initialize reranker '{RERANKER_MODEL}'. "
        "Check internet connectivity (first download), verify the "
        "model name, or clear the Hugging Face cache."
    ) from e


# ============================================================
# RERANK FUNCTION
# ============================================================

def rerank(
    query: str,
    retrieved_chunks: List[Dict],
    top_k: int = DEFAULT_RERANK_TOP_K,
) -> List[Dict]:
    """
    Re-rank retrieved document chunks using a CrossEncoder.

    Parameters
    ----------
    query : str
        User search query.

    retrieved_chunks : List[Dict]

        Expected format:

        [
            {
                "text": "...",
                "metadata": {...},
                "distance": float
            }
        ]

    top_k : int

        Number of highest-ranked chunks to return.

    Returns
    -------
    List[Dict]

        Same structure as input with an additional field:

        rerank_score

    Notes
    -----
    The CrossEncoder jointly evaluates the query and each
    candidate chunk, producing a relevance score.

    Higher score = More relevant.
    """

    if not retrieved_chunks:
        return []

    top_k = min(top_k, len(retrieved_chunks))

    logger.debug(
        "Reranking %d retrieved chunks.",
        len(retrieved_chunks),
    )

    # --------------------------------------------------------
    # Build query-document pairs
    # --------------------------------------------------------

    sentence_pairs = [
        (query, chunk["text"])
        for chunk in retrieved_chunks
    ]

    # --------------------------------------------------------
    # CrossEncoder inference
    # --------------------------------------------------------

    scores = reranker.predict(
        sentence_pairs,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    # --------------------------------------------------------
    # Attach scores
    # --------------------------------------------------------

    for chunk, score in zip(retrieved_chunks, scores):

        chunk["rerank_score"] = float(score)

    # --------------------------------------------------------
    # Sort by reranker score
    # --------------------------------------------------------

    retrieved_chunks.sort(
        key=lambda chunk: chunk["rerank_score"],
        reverse=True,
    )

    logger.debug(
        "Returning Top-%d reranked chunks.",
        top_k,
    )

    # --------------------------------------------------------
    # Return Top-K
    # --------------------------------------------------------

    return retrieved_chunks[:top_k]


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    sample_query = (
        "Who introduced the Transformer architecture?"
    )

    sample_chunks = [

        {
            "text":
                "Attention Is All You Need introduced the "
                "Transformer architecture in 2017.",
            "metadata": {
                "page": 2
            },
            "distance": 0.72,
        },

        {
            "text":
                "Artificial General Intelligence aims to "
                "achieve human-level reasoning.",
            "metadata": {
                "page": 1
            },
            "distance": 0.61,
        },

        {
            "text":
                "Scaling laws explain how model performance "
                "improves with compute and data.",
            "metadata": {
                "page": 5
            },
            "distance": 0.58,
        },

    ]

    reranked_chunks = rerank(
        query=sample_query,
        retrieved_chunks=sample_chunks,
    )

    print("\n" + "=" * 80)
    print("RERANK RESULTS")
    print("=" * 80)

    for rank, chunk in enumerate(reranked_chunks, start=1):

        print(f"\nRank          : {rank}")
        print(f"Score         : {chunk['rerank_score']:.4f}")
        print(f"Distance      : {chunk['distance']:.4f}")
        print(f"Metadata      : {chunk['metadata']}")
        print(f"Preview       : {chunk['text'][:120]}...")

    print("\n" + "=" * 80)