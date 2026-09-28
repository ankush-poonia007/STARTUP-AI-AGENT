"""
CoFoundr AI — Phase 6 Global Constants
Single source of truth for all numeric limits, budgets, and thresholds.

Rules:
- Tunable / environment-specific values → src/core/config.py (Settings)
- Fixed architectural constants → this file
- Never scatter these values across modules
- Import from here everywhere; never redefine inline
"""

# ── API Pagination ────────────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# ── Message Constraints ───────────────────────────────────────────────────────
MAX_MESSAGE_CONTENT_CHARS: int = 32768       # 32KB max message content
MAX_STARTUP_NAME_CHARS: int = 255
MAX_CONVERSATION_TITLE_CHARS: int = 255
MAX_EMAIL_CHARS: int = 255
MIN_PASSWORD_CHARS: int = 8
MAX_PASSWORD_CHARS: int = 128

# ── Concurrency ───────────────────────────────────────────────────────────────
MAX_CONCURRENT_TASKS: int = 5               # Orchestrator parallel agent limit

# ── Retry Budgets ─────────────────────────────────────────────────────────────
PROVIDER_MAX_ATTEMPTS: int = 3              # Provider LLM call retries
AGENT_MAX_ATTEMPTS: int = 3                 # Agent-level retries
DOCUMENT_PROCESSING_MAX_ATTEMPTS: int = 3   # PDF processing retries
MEMORY_EXTRACTION_MAX_ATTEMPTS: int = 2     # Memory LLM extraction retries
PLANNER_MAX_ATTEMPTS: int = 3               # Memory extraction prompt retries

# ── Backoff (seconds) ─────────────────────────────────────────────────────────
PROVIDER_BASE_DELAY: float = 1.0
AGENT_BASE_DELAY: float = 2.0
DOCUMENT_PROCESSING_BASE_DELAY: float = 2.0  # 2s → 4s on retry
MAX_BACKOFF_DELAY: float = 30.0
JITTER_RANGE: float = 0.5                    # ± 50% of calculated delay

# ── Timeouts (seconds) ────────────────────────────────────────────────────────
TIMEOUT_PROVIDER_REQUEST: float = 30.0      # Single LLM API call
TIMEOUT_AGENT_EXECUTION: float = 120.0      # Full agent run
TIMEOUT_WORKFLOW: float = 3600.0            # Entire workflow (1 hour)
TIMEOUT_EMBEDDING: float = 30.0             # Single Gemini embedding call
TIMEOUT_DATABASE: float = 10.0              # Single DB query

# ── Memory System ─────────────────────────────────────────────────────────────
MEMORY_MIN_CONTENT_LENGTH: int = 30         # Skip messages shorter than this
MEMORY_MAX_EXTRACTIONS_PER_MESSAGE: int = 3 # LLM returns max 3 memories
MEMORY_FINAL_CONTEXT_SIZE: int = 5          # Top-N memories injected into agents
MEMORY_CANDIDATE_POOL: int = 10             # Candidates before reranking

# ── RAG Pipeline ──────────────────────────────────────────────────────────────
RAG_VECTOR_TOP_K: int = 10                  # ChromaDB retrieval candidates
RAG_BM25_TOP_K: int = 10                    # BM25 retrieval candidates
RAG_FINAL_TOP_K: int = 3                    # After CrossEncoder reranking
RAG_EMBEDDING_BATCH_SIZE: int = 20          # Chunks per Gemini batch call

# ── Document Chunking ─────────────────────────────────────────────────────────
CHUNK_SIZE_CHARS: int = 2000               # ~512 token proxy
CHUNK_OVERLAP_CHARS: int = 200             # Overlap between adjacent chunks
MIN_CHUNK_CHARS: int = 100                 # Skip chunks shorter than this

# ── Phase 5 Chunking (preserved for backward compatibility) ───────────────────
CHUNK_SIZE: int = 250                      # Phase 5 word-based chunk size
OVERLAP: int = 50                          # Phase 5 overlap
STEP: int = CHUNK_SIZE - OVERLAP           # Phase 5 step
MIN_CHUNK_WORDS: int = 20                  # Phase 5 min chunk words

# ── Retrieval (Phase 5 preserved) ────────────────────────────────────────────
DEFAULT_VECTOR_TOP_K: int = 10
DEFAULT_RERANK_TOP_K: int = 3
TAVILY_MAX_RESULTS: int = 3

# ── Workflow Statuses ─────────────────────────────────────────────────────────
# Used as string values — must match database enum exactly
WORKFLOW_STATUS_QUEUED: str = "QUEUED"
WORKFLOW_STATUS_RUNNING: str = "RUNNING"
WORKFLOW_STATUS_COMPLETED: str = "COMPLETED"
WORKFLOW_STATUS_FAILED: str = "FAILED"

WORKFLOW_TERMINAL_STATUSES: frozenset = frozenset({
    WORKFLOW_STATUS_COMPLETED,
    WORKFLOW_STATUS_FAILED,
})

WORKFLOW_CANCELLABLE_STATUSES: frozenset = frozenset({
    WORKFLOW_STATUS_QUEUED,
    WORKFLOW_STATUS_RUNNING,
})

# ── Document Statuses ─────────────────────────────────────────────────────────
DOCUMENT_STATUS_UPLOADED: str = "UPLOADED"
DOCUMENT_STATUS_PROCESSING: str = "PROCESSING"
DOCUMENT_STATUS_READY: str = "READY"
DOCUMENT_STATUS_FAILED: str = "FAILED"
DOCUMENT_STATUS_DELETED: str = "DELETED"

# ── MIME Type Allowlist ───────────────────────────────────────────────────────
ALLOWED_MIME_TYPES: frozenset = frozenset({
    "application/pdf",
    "text/plain",
    "text/markdown",
})

ALLOWED_FILE_EXTENSIONS: frozenset = frozenset({
    ".pdf",
    ".txt",
    ".md",
})

# ── Startup Stages ────────────────────────────────────────────────────────────
STARTUP_STAGE_IDEA: str = "IDEA"
STARTUP_STAGE_MVP: str = "MVP"
STARTUP_STAGE_TRACTION: str = "TRACTION"
STARTUP_STAGE_GROWTH: str = "GROWTH"

VALID_STARTUP_STAGES: frozenset = frozenset({
    STARTUP_STAGE_IDEA,
    STARTUP_STAGE_MVP,
    STARTUP_STAGE_TRACTION,
    STARTUP_STAGE_GROWTH,
})

# ── Memory Types ──────────────────────────────────────────────────────────────
MEMORY_TYPE_STARTUP_FACT: str = "startup_fact"
MEMORY_TYPE_PREFERENCE: str = "preference"
MEMORY_TYPE_DECISION: str = "decision"
MEMORY_TYPE_GOAL: str = "goal"
MEMORY_TYPE_CONSTRAINT: str = "constraint"

VALID_MEMORY_TYPES: frozenset = frozenset({
    MEMORY_TYPE_STARTUP_FACT,
    MEMORY_TYPE_PREFERENCE,
    MEMORY_TYPE_DECISION,
    MEMORY_TYPE_GOAL,
    MEMORY_TYPE_CONSTRAINT,
})

# ── Message Roles ─────────────────────────────────────────────────────────────
MESSAGE_ROLE_USER: str = "USER"
MESSAGE_ROLE_ASSISTANT: str = "ASSISTANT"
MESSAGE_ROLE_SYSTEM: str = "SYSTEM"

# ── ChromaDB Record Types ─────────────────────────────────────────────────────
CHROMA_RECORD_TYPE_CHUNK: str = "document_chunk"
CHROMA_RECORD_TYPE_MEMORY: str = "memory"

# ── Provider Key Pool Sizes ───────────────────────────────────────────────────
GEMINI_KEY_COUNT: int = 20
OPENROUTER_KEY_COUNT: int = 20
TAVILY_KEY_COUNT: int = 6

# ── Pipeline Config (Phase 5 preserved) ──────────────────────────────────────
MAX_RETRIES: int = 3
API_COOLDOWN_SECONDS: int = 60
MIN_COOLTIME_RETRY: int = 3
GEMINI_MAX_OUTPUT_TOKENS: int = 8192
