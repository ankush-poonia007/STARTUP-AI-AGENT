"""
CoFoundr AI — Phase 5 Settings
Preserved exactly for Phase 5 agent compatibility.

DO NOT DELETE until SP-06 is complete and all agents
are confirmed importing from src/core/config.py instead.

Phase 6 centralised config lives in: src/core/config.py
"""
from dotenv import load_dotenv
import os

load_dotenv()

# ── LLM MODELS ───────────────────────────────────────────────────────────────
GROQ_MODEL          = "openai/gpt-oss-120b"
GEMINI_MODEL        = "gemini-3.6-flash"
GEMINI_LITE_MODEL   = "gemini-3.5-flash-lite"
EMBEDDING_MODEL     = "gemini-embedding-001"
RERANKER_MODEL      = "BAAI/bge-reranker-v2-m3"

# ── PIPELINE CONFIG ──────────────────────────────────────────────────────────
MAX_RETRIES             = 3
API_COOLDOWN_SECONDS    = 60
MIN_COOLTIME_RETRY      = 3
GEMINI_MAX_OUTPUT_TOKENS = 8192
GROQ_DEBUG_REQUESTS     = os.getenv("GROQ_DEBUG_REQUESTS", "") == "1"

# ── RETRIEVAL CONFIG ─────────────────────────────────────────────────────────
DEFAULT_VECTOR_TOP_K    = 10
DEFAULT_RERANK_TOP_K    = 3
TAVILY_MAX_RESULTS      = 3

# ── STORAGE PATHS ────────────────────────────────────────────────────────────
CHROMA_DB_PATH      = "data/chroma_db"
BM25_INDEX_DIR      = "data/BM25"
BM25_CORPUS_FILE    = os.path.join(BM25_INDEX_DIR, "existing_corpus.json")
PDF_OUTPUT_DIR      = "data/outputs"

# ── CHUNKING ─────────────────────────────────────────────────────────────────
CHUNK_SIZE      = 250
OVERLAP         = 50
STEP            = CHUNK_SIZE - OVERLAP
MIN_CHUNK_WORDS = 20

# ── GEMINI API KEYS ───────────────────────────────────────────────────────────
GEMINI_API_KEYS = [
    os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 21)
]
GEMINI_API_KEYS = [k for k in GEMINI_API_KEYS if k]

# ── OPENROUTER API KEYS ───────────────────────────────────────────────────────
OPEN_ROUTER_API_KEYS = [
    os.getenv(f"OPEN_ROUTER_API_KEY_{i}") for i in range(1, 21)
]
OPEN_ROUTER_API_KEYS = [k for k in OPEN_ROUTER_API_KEYS if k]

# ── TAVILY API KEYS ───────────────────────────────────────────────────────────
TAVILY_API_KEYS = [
    os.getenv(f"TAVILY_API_KEY_{i}") for i in range(1, 7)
]
TAVILY_API_KEYS = [k for k in TAVILY_API_KEYS if k]

# ── DATABASE API KEYS ───────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
ALEMBIC_DATABASE_URL = os.getenv("ALEMBIC_DATABASE_URL")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")

if __name__ == "__main__":
    print("Phase 5 settings loaded.")
    print(f"Gemini keys loaded: {len(GEMINI_API_KEYS)}")
    print(f"OpenRouter keys loaded: {len(OPEN_ROUTER_API_KEYS)}")
    print(f"Tavily keys loaded: {len(TAVILY_API_KEYS)}")
