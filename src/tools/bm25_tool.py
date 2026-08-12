import os
import bm25s
import json

from src.config.settings import (
    BM25_CORPUS_FILE,
    BM25_INDEX_DIR,
    DEFAULT_VECTOR_TOP_K,
)


def add_documents(chunks: list):
    """
    Add document chunks to the BM25 corpus and rebuild the BM25 index.

    Parameters
    ----------
    chunks : list
        List of document chunk dictionaries containing the chunk text
        and associated metadata.

    Returns
    -------
    None
        Updates the persistent BM25 corpus and index.
    """

    # ----------------------------------------------------
    # 1. Prepare BM25 index directory
    # ----------------------------------------------------

    os.makedirs(
        BM25_INDEX_DIR,
        exist_ok=True
    )

    bm25_corpus = {}

    # ----------------------------------------------------
    # 2. Load existing BM25 corpus
    # ----------------------------------------------------

    if os.path.isfile(BM25_CORPUS_FILE):

        with open(
            BM25_CORPUS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            bm25_corpus = json.load(file)

    # ----------------------------------------------------
    # 3. Validate incoming chunks
    # ----------------------------------------------------

    if not chunks:
        return

    # ----------------------------------------------------
    # 4. Merge new chunks into existing corpus
    # ----------------------------------------------------

    for chunk in chunks:
        bm25_corpus[chunk["text"]] = chunk

    # ----------------------------------------------------
    # 5. Build text corpus
    # ----------------------------------------------------

    full_corpus = list(
        bm25_corpus.keys()
    )

    # ----------------------------------------------------
    # 6. Tokenize corpus
    # ----------------------------------------------------

    corpus_tokens = bm25s.tokenize(
        full_corpus,
        stopwords="english"
    )

    # ----------------------------------------------------
    # 7. Build BM25 index
    # ----------------------------------------------------

    bm25_index = bm25s.BM25(
        corpus=full_corpus
    )

    bm25_index.index(
        corpus_tokens
    )

    # ----------------------------------------------------
    # 8. Save BM25 index
    # ----------------------------------------------------

    bm25_index.save(
        BM25_INDEX_DIR,
        corpus=full_corpus
    )

    # ----------------------------------------------------
    # 9. Save BM25 corpus
    # ----------------------------------------------------

    with open(
        BM25_CORPUS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            bm25_corpus,
            file,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"✅ BM25 index updated with "
        f"{len(full_corpus)} chunks."
    )

    return


def bm25_retrieve(
    user_query,
    top_k=DEFAULT_VECTOR_TOP_K
):
    """
    Retrieve the most relevant document chunks using BM25.

    Parameters
    ----------
    user_query : str
        User's search query.

    top_k : int
        Maximum number of chunks to retrieve.

    Returns
    -------
    list
        Ranked list of standardized document chunks containing
        text, metadata, and BM25 score.
    """

    # ----------------------------------------------------
    # 1. Check whether BM25 index exists
    # ----------------------------------------------------

    if not os.path.exists(BM25_INDEX_DIR):
        return []

    # ----------------------------------------------------
    # 2. Load BM25 index
    # ----------------------------------------------------

    bm25_index = bm25s.BM25.load(
        BM25_INDEX_DIR,
        load_corpus=True
    )

    # ----------------------------------------------------
    # 3. Load BM25 corpus
    # ----------------------------------------------------

    if os.path.isfile(BM25_CORPUS_FILE):

        with open(
            BM25_CORPUS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            bm25_corpus = json.load(file)

    # ----------------------------------------------------
    # 4. Tokenize user query
    # ----------------------------------------------------

    query_tokens = bm25s.tokenize(
        user_query
    )

    # ----------------------------------------------------
    # 5. Retrieve top-K BM25 results
    # ----------------------------------------------------

    result, score = bm25_index.retrieve(
        query_tokens,
        k=top_k
    )

    # ----------------------------------------------------
    # 6. Convert BM25 results to standardized chunks
    # ----------------------------------------------------

    retrieved_results = []

    for index in range(top_k):

        chunk = result[0][index]

        chunk["score"] = score[0][index]

        retrieved_results.append(
            {
                "text": chunk["text"],
                "metadata": {
                    "page_number": chunk["page_number"],
                    "file_name": chunk["file_name"]
                },
                "score": chunk["score"]
            }
        )

    # ----------------------------------------------------
    # 7. Return ranked results
    # ----------------------------------------------------

    return retrieved_results


# ----------------------------------------------------
# LOCAL TEST
# ----------------------------------------------------

if __name__ == "__main__":

    # ----------------------------------------------------
    # 1. Define sample chunks
    # ----------------------------------------------------

    sample_chunks = [
        {
            "text": (
                "The Python programming language was created by "
                "Guido van Rossum and released in 1991."
            ),
            "page_number": 1,
            "file_name": "python_history.txt"
        },
        {
            "text": (
                "BM25 is a ranking function used by search engines "
                "to estimate the relevance of documents."
            ),
            "page_number": 2,
            "file_name": "search_theory.txt"
        },
        {
            "text": (
                "Retrieval-Augmented Generation optimizes language "
                "models using an external knowledge base."
            ),
            "page_number": 3,
            "file_name": "rag_framework.txt"
        }
    ]

    # ----------------------------------------------------
    # 2. Test document indexing
    # ----------------------------------------------------

    print(
        "--- Testing Document Indexing ---"
    )

    add_documents(
        sample_chunks
    )

    # ----------------------------------------------------
    # 3. Test BM25 retrieval
    # ----------------------------------------------------

    print(
        "\n--- Testing Retrieval ---"
    )

    query = (
        "Who created the Python language?"
    )

    top_results = bm25_retrieve(
        user_query=query,
        top_k=2
    )

    # ----------------------------------------------------
    # 4. Print retrieval results
    # ----------------------------------------------------

    for index, document in enumerate(
        top_results
    ):

        print(
            f"\nResult {index + 1}:"
        )

        print(
            f"Score: {document['score']:.4f}"
        )

        print(
            f"Text:  {document['text']}"
        )

        print(
            f"Meta:  {document['metadata']}"
        )