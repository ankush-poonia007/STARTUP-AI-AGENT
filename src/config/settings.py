import os 

EMBEDDING_MODEL = "gemini-embedding-001"

RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

DEFAULT_VECTOR_TOP_K = 10

DEFAULT_RERANK_TOP_K = 3

GENERATION_MODEL = "gemini-2.5-flash"

BM25_INDEX_DIR = "data/BM25"

BM25_CORPUS_FILE = os.path.join(BM25_INDEX_DIR, "existing_corpus.json")

MIN_COOLTIME_RETRY = 3 