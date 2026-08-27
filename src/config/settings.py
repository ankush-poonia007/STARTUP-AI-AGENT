from dotenv import load_dotenv
import os 

load_dotenv()

# ── LLM MODELS ───────────────────────────────────────────────
GROQ_MODEL          = "openai/gpt-oss-120b"
GEMINI_MODEL        = "gemini-3.6-flash"
GEMINI_LITE_MODEL   = "gemini-3.5-flash-lite"
EMBEDDING_MODEL     = "gemini-embedding-001"
RERANKER_MODEL      = "BAAI/bge-reranker-v2-m3"

# ── PIPELINE CONFIG ──────────────────────────────────────────
MAX_RETRIES         = 3
API_COOLDOWN_SECONDS = 60
MIN_COOLTIME_RETRY  = 3

# Claude: added. gemini_tool.generate_text sent no output-token budget, so
# structured responses could stop at the model default and return truncated
# JSON that failed to parse in the four structured consumers.
GEMINI_MAX_OUTPUT_TOKENS = 8192

# Claude: added. groq_tool printed request sizes and 500 characters of the
# user prompt on every call with no gate. Set GROQ_DEBUG_REQUESTS=1 in .env
# to re-enable that instrumentation when debugging.
GROQ_DEBUG_REQUESTS = os.getenv("GROQ_DEBUG_REQUESTS", "") == "1"

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
GEMINI_API_KEYS     = [
    k for k in GEMINI_API_KEYS if k
]

# ── GROQ API KEYS ────────────────────────────────────────────
OPEN_ROUTER_API_KEYS       = [
    os.getenv(f"OPEN_ROUTER_API_KEY_{i}") for i in range(1, 6)
]
OPEN_ROUTER_API_KEYS       = [
    k for k in OPEN_ROUTER_API_KEYS if k
]

# ── TAVILY ───────────────────────────────────────────────────
TAVILY_API_KEYS     = [
    os.getenv(f"TAVILY_API_KEY_{i}") for i in range(1, 7)
]
TAVILY_API_KEYS     = [
    k for k in TAVILY_API_KEYS if k
]

# ── STORAGE CONSTANTS ───────────────────────────────────────────────────
CHUNK_SIZE = 250

OVERLAP = 50

STEP = CHUNK_SIZE - OVERLAP

MIN_CHUNK_WORDS = 20



if __name__ == "__main__":
    print("Hello")