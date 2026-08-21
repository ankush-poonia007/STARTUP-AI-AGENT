"""
File        : agents/rag_agent.py
Triggered By:
    - full_analysis
    - partial_idea
    - nurturing
    - Any workflow containing pitch_deck_text

Tools:
    - gemini_tool.py
    - chroma_tool.py
    - bm25_tool.py
    - reranker_tool.py

Input:
    workflow_state["user_input"]
        Original user request.

    workflow_state["startup_idea"]
        Normalized startup concept.

    workflow_state["startup_type"]
        Startup industry/category.

    workflow_state["pitch_deck_text"]
        List of pitch-deck document chunks containing text and metadata.

Output:
    workflow_state["rag_context"]
        Final ranked and reranked pitch-deck chunks.

    workflow_state["pipeline_status"]["RAGAgent"]
        Updated to "success" after successful execution.

Responsibilities:
    - Build a contextual retrieval query.
    - Generate embeddings for pitch-deck chunks.
    - Ingest chunks into ChromaDB and BM25.
    - Retrieve candidates from both retrieval systems.
    - Normalize ChromaDB results.
    - Fuse ChromaDB and BM25 rankings using Reciprocal Rank Fusion.
    - Rerank the fused candidates using a CrossEncoder.
    - Store the final ranked context in workflow state.

Execution Flow:
    1. Read startup context.
    2. Build contextual retrieval query.
    3. Check whether pitch-deck chunks are available.
    4. Generate chunk embeddings with Gemini.
    5. Ingest chunks into ChromaDB.
    6. Ingest chunks into BM25.
    7. Generate query embedding with Gemini.
    8. Retrieve candidates from ChromaDB.
    9. Normalize ChromaDB results.
    10. Retrieve candidates from BM25.
    11. Fuse both rankings using RRF.
    12. Rerank fused candidates using CrossEncoder.
    13. Store final RAG context.
    14. Update pipeline status.
    15. Return updated workflow state.

Design Notes:
    - ChromaDB provides semantic/vector retrieval.
    - BM25 provides lexical retrieval.
    - RRF combines both retrieval rankings.
    - CrossEncoder performs final relevance reranking.
    - The contextual query is reused throughout retrieval and reranking.
    - If pitch_deck_text is empty, the agent returns an empty RAG context
      without executing the retrieval pipeline.

Failure Handling:
    Execution logging, timing, retry behavior, and exception handling
    are managed centrally by src/core/decorators.py.
"""

from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure,
)

from src.tools.gemini_tool import gemini_tool
from src.tools.reranker_tool import rerank

import src.tools.chroma_tool as chroma_tool
import src.tools.bm25_tool as bm25_tool


class RAGAgent:
    """
    Retrieve and rank the most relevant information from the startup's
    pitch-deck context.

    RAGAgent implements the project's hybrid retrieval pipeline by
    combining semantic retrieval, lexical retrieval, rank fusion,
    and CrossEncoder reranking.

    Retrieval Pipeline
    ------------------
        Pitch Deck Chunks
              ↓
        Gemini Embeddings
              ↓
        ┌───────────────┐
        │ ChromaDB      │
        │ BM25          │
        └───────┬───────┘
                ↓
        Reciprocal Rank Fusion
                ↓
        CrossEncoder Reranking
                ↓
        workflow_state["rag_context"]

    Input State
    -----------
    workflow_state["user_input"]:
        Original user request.

    workflow_state["startup_idea"]:
        Normalized startup concept.

    workflow_state["startup_type"]:
        Startup category used to provide retrieval context.

    workflow_state["pitch_deck_text"]:
        Pitch-deck chunks available for retrieval.

    Output State
    ------------
    workflow_state["rag_context"]:
        Final ranked retrieval results.

    workflow_state["pipeline_status"]["RAGAgent"]:
        Execution status of the RAG pipeline.

    Important:
        This agent performs retrieval and ranking only.

        It does not:
            - Generate a final startup analysis.
            - Generate recommendations.
            - Call an LLM for answer generation.
            - Modify the original pitch-deck content.

        Its responsibility ends after producing ranked retrieval
        context for downstream agents.
    """

    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state: dict) -> dict:
        """
        Execute the hybrid pitch-deck retrieval pipeline.

        Parameters
        ----------
        workflow_state : dict
            Shared workflow state containing the startup context and
            available pitch-deck chunks.

        Returns
        -------
        dict
            Updated workflow state containing:
                - workflow_state["rag_context"]
                - workflow_state["pipeline_status"]["RAGAgent"]

        Processing Stages
        -----------------
        1. Read startup context.
        2. Build the contextual retrieval query.
        3. Check for available pitch-deck chunks.
        4. Generate embeddings for all chunks.
        5. Store chunks in ChromaDB.
        6. Store chunks in BM25.
        7. Generate the contextual query embedding.
        8. Retrieve semantic candidates from ChromaDB.
        9. Normalize ChromaDB results.
        10. Retrieve lexical candidates from BM25.
        11. Fuse both retrieval rankings using RRF.
        12. Apply CrossEncoder reranking.
        13. Store the final ranked context.
        14. Update pipeline status.
        15. Return the updated workflow state.

        Notes
        -----
        The same contextual retrieval query is used for semantic retrieval,
        BM25 retrieval, and CrossEncoder reranking.

        If pitch_deck_text is empty, the method returns an empty
        rag_context and marks the agent as successful.
        """

        # ============================================================
        # 1. Read startup context
        # ============================================================

        user_input = workflow_state["user_input"]
        startup_idea = workflow_state["startup_idea"]
        startup_type = workflow_state["startup_type"]

        # ============================================================
        # 2. Build contextual retrieval query
        # ============================================================

        retrieval_query = (
            f"{startup_idea} "
            f"{startup_type} "
            f"{user_input}"
        )

        # ============================================================
        # 3. Check pitch_deck_text
        # ============================================================

        chunks = workflow_state["pitch_deck_text"]

        if not chunks:
            workflow_state["rag_context"] = []

            workflow_state["pipeline_status"]["RAGAgent"] = (
                "success"
            )

            return workflow_state

        # ============================================================
        # 4. Batch embed chunks → Gemini
        # ============================================================

        embedding_list = gemini_tool.generate_embedding(
            chunks=chunks
        )

        # ============================================================
        # 5. Ingest chunks → ChromaDB
        # ============================================================

        chroma_tool.add_documents(
            chunks=chunks,
            embeddings=embedding_list
        )

        # ============================================================
        # 6. Ingest chunks → BM25
        # ============================================================

        bm25_tool.add_documents(
            chunks=chunks
        )

        # ============================================================
        # 7. Embed contextual query → Gemini
        # ============================================================
        
        retrieval_query_embedding = gemini_tool.generate_embedding(
            [
                {
                    "text": retrieval_query
                }
            ]
        )

        # ============================================================
        # 8. Query ChromaDB
        # ============================================================

        chroma_retrieval = chroma_tool.query_collection(
            user_input=retrieval_query_embedding
        )

        # ============================================================
        # 9. Normalize ChromaDB results
        # ============================================================

        normalized_result = (
            chroma_tool.normalize_chroma_results(
                chroma_retrieval
            )
        )

        # ============================================================
        # 10. Query BM25
        # ============================================================

        bm25_retrieval = bm25_tool.bm25_retrieve(
            user_query=retrieval_query
        )

        # ============================================================
        # 11. Reciprocal Rank Fusion
        # ============================================================

        fused_list = chroma_tool.reciprocal_rank_fusion(
            chroma_results=normalized_result,
            bm25_results=bm25_retrieval
        )

        # ============================================================
        # 12. CrossEncoder reranking
        # ============================================================

        final_list = rerank(
            query=retrieval_query,
            retrieved_chunks=fused_list
        )

        # ============================================================
        # 13. Write final RAG context
        # ============================================================

        workflow_state["rag_context"] = final_list

        # ============================================================
        # 14. Update pipeline status
        # ============================================================

        workflow_state["pipeline_status"]["RAGAgent"] = (
            "success"
        )

        # ============================================================
        # 15. Return updated workflow state
        # ============================================================

        return workflow_state


# ================================================================
# STANDALONE TEST
# Allows RAGAgent to be tested independently using the shared
# mock workflow state and displays the final ranked context.
# ================================================================

if __name__ == "__main__":

    # ============================================================
    # 1. Load mock workflow state
    # ============================================================

    from tests.mock_workflow_state import MOCK_STATE_FULL

    # ============================================================
    # 2. Initialize RAGAgent
    # ============================================================

    agent = RAGAgent()

    # ============================================================
    # 3. Execute RAG retrieval pipeline
    # ============================================================

    result = agent.run(
        MOCK_STATE_FULL.copy()
    )

    # ============================================================
    # 4. Display final ranked RAG context
    # ============================================================

    print("\n" + "=" * 80)
    print("RAG CONTEXT")
    print("=" * 80)

    for rank, chunk in enumerate(
        result["rag_context"],
        start=1
    ):

        print(f"\nRank: {rank}")
        print(f"Text: {chunk['text']}")
        print(f"Metadata: {chunk['metadata']}")

        if "rrf_score" in chunk:
            print(
                f"RRF Score: "
                f"{chunk['rrf_score']:.4f}"
            )

        if "rerank_score" in chunk:
            print(
                f"Rerank Score: "
                f"{chunk['rerank_score']:.4f}"
            )

    # ============================================================
    # 5. Display execution errors
    # ============================================================

    print("\nERRORS:")
    print(result["errors"])