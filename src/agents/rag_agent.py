from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure,
)

from src.tools.gemini_tool import embedding_call
from src.tools.reranker_tool import rerank

import src.tools.chroma_tool as chroma_tool
import src.tools.bm25_tool as bm25_tool


class RAGAgent:
    """
    Retrieval-Augmented Generation (RAG) agent responsible for
    retrieving the most relevant context from the pitch deck.

    This agent operates as one stage in the multi-agent workflow.
    It receives the shared workflow state, processes the available
    pitch deck chunks, performs hybrid retrieval using ChromaDB
    and BM25, fuses both rankings using Reciprocal Rank Fusion
    (RRF), and applies CrossEncoder reranking.

    Workflow:
        1. Read user input and pitch deck chunks.
        2. Generate embeddings for document chunks.
        3. Store chunks in ChromaDB and BM25.
        4. Generate an embedding for the user query.
        5. Retrieve candidates from ChromaDB and BM25.
        6. Normalize ChromaDB results.
        7. Fuse retrieval results using RRF.
        8. Rerank fused results using a CrossEncoder.
        9. Store the final ranked context in the workflow state.

    Input State Requirements:
        workflow_state["user_input"]:
            User's search/query text.

        workflow_state["pitch_deck_text"]:
            List of document chunk dictionaries containing at least
            the chunk text and required metadata.

        workflow_state["pipeline_status"]:
            Dictionary used to track the execution status of agents.

    Output State:
        workflow_state["rag_context"]:
            Top-ranked and reranked document chunks containing their
            text, metadata, RRF score, and reranker score.

        workflow_state["pipeline_status"]["RAGAgent"]:
            Updated to "success" when the RAG pipeline completes
            successfully.

    Notes:
        This agent performs retrieval and ranking only. It does not
        generate the final answer to the user. Downstream agents can
        consume "rag_context" from the shared workflow state.
    """

    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state: dict) -> dict:
        """
        Execute the RAG retrieval pipeline for the current workflow state.

        The method reads the user query and pitch deck chunks from the
        shared multi-agent workflow state, performs hybrid retrieval
        through ChromaDB and BM25, combines the results using Reciprocal
        Rank Fusion, and reranks the fused candidates using a
        CrossEncoder.

        Parameters
        ----------
        workflow_state : dict
            Shared state passed between agents in the multi-agent
            workflow. It must contain "user_input", "pitch_deck_text",
            and "pipeline_status".

        Returns
        -------
        dict
            The updated workflow state containing the final ranked
            retrieval context under "rag_context" and the updated
            RAGAgent execution status under "pipeline_status".

        Notes
        -----
        If "pitch_deck_text" is empty, the method skips retrieval,
        sets "rag_context" to an empty list, marks the agent as
        successful, and returns the workflow state.
        """

        user_input = workflow_state["user_input"]

        # ----------------------------------------------------
        # 1. Check pitch_deck_text
        # ----------------------------------------------------

        chunks = workflow_state["pitch_deck_text"]

        if not chunks:
            workflow_state["rag_context"] = []

            workflow_state["pipeline_status"]["RAGAgent"] = (
                "success"
            )

            return workflow_state

        # ----------------------------------------------------
        # 2. pitch_deck_text is already a list of chunk dicts
        # ----------------------------------------------------

        # ----------------------------------------------------
        # 3. Batch embed chunks → Gemini
        # ----------------------------------------------------

        embedding_list = embedding_call(
            chunks=chunks
        )

        # ----------------------------------------------------
        # 4. Ingest chunks → ChromaDB
        # ----------------------------------------------------

        chroma_tool.add_documents(
            chunks=chunks,
            embeddings=embedding_list
        )

        # ----------------------------------------------------
        # 5. Ingest chunks → BM25
        # ----------------------------------------------------

        bm25_tool.add_documents(
            chunks=chunks
        )

        # ----------------------------------------------------
        # 6. Embed user input → Gemini
        # ----------------------------------------------------

        user_input_embedding = embedding_call(
            [
                {
                    "text": user_input
                }
            ]
        )

        # ----------------------------------------------------
        # 7. Query ChromaDB
        # ----------------------------------------------------

        chroma_retrieval = chroma_tool.query_collection(
            user_input=user_input_embedding
        )

        # ----------------------------------------------------
        # 8. Normalize ChromaDB results
        # ----------------------------------------------------

        normalized_result = (
            chroma_tool.normalize_chroma_results(
                chroma_retrieval
            )
        )

        # ----------------------------------------------------
        # 9. Query BM25
        # ----------------------------------------------------

        bm25_retrieval = bm25_tool.bm25_retrieve(
            user_query=user_input
        )

        # ----------------------------------------------------
        # 10. Reciprocal Rank Fusion
        # ----------------------------------------------------

        fused_list = chroma_tool.reciprocal_rank_fusion(
            chroma_results=normalized_result,
            bm25_results=bm25_retrieval
        )

        # ----------------------------------------------------
        # 11. CrossEncoder reranking
        # ----------------------------------------------------

        final_list = rerank(
            query=user_input,
            retrieved_chunks=fused_list
        )

        # ----------------------------------------------------
        # 12. Write final RAG context
        # ----------------------------------------------------

        workflow_state["rag_context"] = final_list

        # ----------------------------------------------------
        # 13. Update pipeline status
        # ----------------------------------------------------

        workflow_state["pipeline_status"]["RAGAgent"] = (
            "success"
        )

        return workflow_state


if __name__ == "__main__":
    
    from tests.mock_workflow_state import MOCK_STATE_FULL
    
    agent = RAGAgent()

    result = agent.run(
        MOCK_STATE_FULL.copy()
    )

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