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
                "rrf_score": float
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

    # ============================================================
    # MODEL INITIALIZATION
    # ============================================================
    
    logger.info(
        "Loading CrossEncoder model: %s",
        RERANKER_MODEL
    )

    reranker = CrossEncoder(
        RERANKER_MODEL,
        max_length=512,
    )

    # Explicit inference mode
    reranker.model.eval()

    logger.info(
        "CrossEncoder loaded successfully."
    )

    top_k = min(
        top_k,
        len(retrieved_chunks)
    )

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

    reranked_chunks = []

    for chunk, score in zip(
        retrieved_chunks,
        scores
    ):

        updated_chunk = chunk.copy()

        updated_chunk["rerank_score"] = float(score)

        reranked_chunks.append(
            updated_chunk
        )

    # --------------------------------------------------------
    # Sort by reranker score
    # --------------------------------------------------------

    reranked_chunks.sort(
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

    return reranked_chunks[:top_k]


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

    # Simulates the output of RRF
    sample_chunks = [

        {
            "text":
                "Attention Is All You Need introduced the "
                "Transformer architecture in 2017.",
            "metadata": {
                "page": 2
            },
            "rrf_score": 0.0323,
        },

        {
            "text":
                "Artificial General Intelligence aims to "
                "achieve human-level reasoning.",
            "metadata": {
                "page": 1
            },
            "rrf_score": 0.0161,
        },

        {
            "text":
                "Scaling laws explain how model performance "
                "improves with compute and data.",
            "metadata": {
                "page": 5
            },
            "rrf_score": 0.0158,
        },

    ]

    reranked_chunks = rerank(
        query=sample_query,
        retrieved_chunks=sample_chunks,
    )

    print("\n" + "=" * 80)
    print("RERANK RESULTS")
    print("=" * 80)

    for rank, chunk in enumerate(
        reranked_chunks,
        start=1
    ):

        print(f"\nRank          : {rank}")
        print(
            f"Rerank Score  : "
            f"{chunk['rerank_score']:.4f}"
        )
        print(
            f"RRF Score     : "
            f"{chunk['rrf_score']:.4f}"
        )
        print(
            f"Metadata      : "
            f"{chunk['metadata']}"
        )
        print(
            f"Preview       : "
            f"{chunk['text'][:120]}..."
        )

    print("\n" + "=" * 80)