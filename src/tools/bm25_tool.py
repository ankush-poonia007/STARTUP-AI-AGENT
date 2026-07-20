import os
import bm25s
import json

from src.config.settings import(
    BM25_CORPUS_FILE,
    BM25_INDEX_DIR,
    DEFAULT_VECTOR_TOP_K,
    
)

def add_documents(chunks: list):
    
    os.makedirs(BM25_INDEX_DIR, exist_ok=True)
    bm25_corpus = {}
    
    if os.path.isfile(BM25_CORPUS_FILE):
        
        with open(BM25_CORPUS_FILE,"r",encoding="utf-8") as file :
            bm25_corpus = json.load(file)
        
    if not chunks:
        return
    
    
    # Merge new chunks into existing corpus
    for chunk in chunks:
        bm25_corpus[chunk["text"]] = chunk

    # Build text corpus
    full_corpus = list(bm25_corpus.keys())

    # Tokenize
    corpus_tokens = bm25s.tokenize(
        full_corpus,
        stopwords="english"
    )

    # Rebuild BM25
    bm25_index = bm25s.BM25(corpus=full_corpus)
    bm25_index.index(corpus_tokens)

    # Save BM25 index
    bm25_index.save(
        BM25_INDEX_DIR,
        corpus=full_corpus
    )

    # Save corpus dictionary
    with open(BM25_CORPUS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            bm25_corpus,
            file,
            ensure_ascii=False,
            indent=4
        )

    print(f"✅ BM25 index updated with {len(full_corpus)} chunks.")
    
    return 

def bm25_retrieve(user_query, top_k = DEFAULT_VECTOR_TOP_K  ):
    
    if not os.path.exists(BM25_INDEX_DIR):
        return []
    
    bm25_index = bm25s.BM25.load(BM25_INDEX_DIR,load_corpus=True)
    
    if os.path.isfile(BM25_CORPUS_FILE):
        with open(BM25_CORPUS_FILE,'r',encoding='utf-8') as file:
            bm25_corpus = json.load(file)
    
    query_tokens = bm25s.tokenize(user_query)
    
    result, score = bm25_index.retrieve(query_tokens,k=top_k)
    
    res = []
    for k in range(top_k):
        chunk = bm25_corpus[result[0][k]]
        
        chunk['score'] = score[0][k]
        res.append(
            {
                'text':chunk['text'],
                'metadatas':chunk['metadata'],
                'score':chunk['score']
            }
        )
        
    return res


if __name__ == "__main__":
    # 1. Define sample chunks
    sample_chunks = [
        {
            "text": "The Python programming language was created by Guido van Rossum and released in 1991.",
            "metadata": {"source": "python_history.txt", "chunk_id": 1}
        },
        {
            "text": "BM25 is a ranking function used by search engines to estimate the relevance of documents.",
            "metadata": {"source": "search_theory.txt", "chunk_id": 2}
        },
        {
            "text": "Retrieval-Augmented Generation optimizes language models using an external knowledge base.",
            "metadata": {"source": "rag_framework.txt", "chunk_id": 3}
        }
    ]

    print("--- Testing Document Indexing ---")
    # 2. Add documents to build the index and save corpus
    add_documents(sample_chunks)

    print("\n--- Testing Retrieval ---")
    # 3. Query the index
    query = "Who created the Python language?"
    top_results = bm25_retrieve(user_query=query, top_k=2)

    # 4. Print results
    for idx, doc in enumerate(top_results):
        print(f"\nResult {idx + 1}:")
        print(f"Score: {doc['score']:.4f}")
        print(f"Text:  {doc['text']}")
        print(f"Meta:  {doc['metadatas']}")
