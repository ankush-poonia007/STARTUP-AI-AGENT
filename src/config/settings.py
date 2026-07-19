from dotenv import load_dotenv
import os 

load_dotenv()

# ── LLM MODELS ───────────────────────────────────────────────
GROQ_MODEL          = "llama-3.3-70b-versatile"
GEMINI_MODEL        = "gemini-2.5-flash"
EMBEDDING_MODEL     = "gemini-embedding-001"
RERANKER_MODEL      = "BAAI/bge-reranker-v2-m3"

# ── PIPELINE CONFIG ──────────────────────────────────────────
MAX_RETRIES         = 3
API_COOLDOWN_SECONDS = 60
MIN_COOLTIME_RETRY  = 3

# ── RETRIEVAL CONFIG ─────────────────────────────────────────
DEFAULT_VECTOR_TOP_K = 10
DEFAULT_RERANK_TOP_K = 3
TAVILY_MAX_RESULTS   = 3

# ── STORAGE PATHS ────────────────────────────────────────────
CHROMA_DB_PATH      = "data/chroma_db"
BM25_INDEX_DIR      = "data/BM25"
BM25_CORPUS_FILE    = os.path.join(BM25_INDEX_DIR, "existing_corpus.json")
PDF_OUTPUT_DIR      = "data/outputs"

# ── GEMINI API KEYS ──────────────────────────────────────────
# Loaded from .env — do not hardcode
GEMINI_API_KEYS     = [
    os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 21)
]
GEMINI_API_KEYS     = [k for k in GEMINI_API_KEYS if k]

# ── GROQ API KEYS ────────────────────────────────────────────
GROQ_API_KEYS       = [
    os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 6)
]
GROQ_API_KEYS       = [k for k in GROQ_API_KEYS if k]

# ── TAVILY ───────────────────────────────────────────────────
TAVILY_API_KEY      = os.getenv("TAVILY_API_KEY")



if __name__ == "__main__":
    print("Hello")