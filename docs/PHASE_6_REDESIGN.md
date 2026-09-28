# CoFoundr AI — Phase 6 Redesign Document
## From SaaS-Level Plan to Portfolio-Signal Execution

**Version:** 6.0.0-redesign  
**Date:** September 22, 2026  
**Author:** Ankush Poonia  
**Status:** FROZEN — Implementation Ready  

---

## 1. Context — What Was Planned Before

The original Phase 6 plan (SP-01 through SP-10) was designed as a full SaaS-level autonomous research platform. It included:

- 16 database tables with complex relationships
- Redis for caching, distributed locks, idempotency, rate limiting
- Full autonomous planning engine with DAG validation
- 9-dimension scoring engine with deterministic arithmetic
- NDJSON streaming delivery layer
- Circuit breakers, retry storms protection, crash recovery
- OpenTelemetry observability, Prometheus metrics
- Full production reliability layer
- 30 days × 3 hours = 90 hours total capacity

**Why it was changed:**

The original plan optimised for SaaS completeness. The actual goal is portfolio signal — demonstrating AI engineering depth, not production deployment readiness. Building a SaaS-level system in 75 hours while learning Alembic, async SQLAlchemy, JWT, and FastAPI simultaneously was not realistic or strategically correct.

---

## 2. Current Direction

**One sentence purpose:**  
CoFoundr AI helps someone with a startup idea move beyond just having the idea — it analyzes market scope, improvement areas, and what to build for maximum user traction.

**Primary audience:** Recruiters and technical evaluators reviewing an AI engineering portfolio.

**What this project must demonstrate:**
- Ability to build AI orchestration from first principles (no frameworks)
- Understanding of multi-agent systems, RAG pipelines, tool calling
- Backend engineering sufficient to support AI execution
- Critical thinking about how frameworks work under the hood

**What this project does NOT need to demonstrate:**
- SaaS-level production readiness
- Full autonomous planning
- Real-time streaming
- Distributed systems reliability

**The core differentiator:**  
Built without LangChain or LlamaIndex. Every component — agent loops, tool calling, context management, retrieval, reranking, state passing, provider abstraction, validation — implemented from first principles. This gives complete control and complete understanding.

---

## 3. What Is Removed

| Original Feature | Reason Removed |
|---|---|
| Redis (caching, locks, idempotency) | Backend plumbing, no AI portfolio signal |
| 16-table schema | Overkill for scope; SaaS-level complexity |
| Sessions table | No session-specific functionality planned |
| Document versions table | Overkill for portfolio |
| Autonomous planning engine | Not the story being told |
| DAG validation + cycle detection | Follows from removing planning engine |
| Change evaluator + replanning | Follows from removing planning engine |
| 9-dimension scoring engine | Current Phase 5 scoring is sufficient |
| NDJSON streaming (SP-07) | No frontend streaming required yet |
| Circuit breakers (SP-08) | Production concern, not portfolio signal |
| Retry storms protection (SP-08) | Same reason |
| Crash recovery (SP-08) | Same reason |
| OpenTelemetry + Prometheus (SP-09) | Deployment concern, not portfolio signal |
| Observability metrics (SP-09) | Same reason |
| 3 conditional agents (UserProfile, FinancialPlanning, GoToMarket) | Were already marked conditional in original plan |
| LangChain integration | Contradicts "built from first principles" story |

---

## 4. What Is Added / Changed

| Feature | Status | Reason Added |
|---|---|---|
| startup_id isolation in ChromaDB | New | Multi-user RAG correctness |
| Standardised error envelope | New | Professional API signal |
| Refresh tokens | New | Auth maturity signal |
| CORS configuration | New | Frontend preparation |
| Message sequence numbers | New | Engineering thinking signal |
| PDF upload with MIME validation | New | Proper file handling |
| Automatic LLM memory extraction | New | AI-relevant capability |
| TaskContext + AgentResult contracts | New (minimal) | Structured agent I/O |
| Pydantic validation on all I/O | New | Professional Python signal |
| RAG pipeline polished | Changed | Cleaner code, startup_id isolation |
| API key rotation rewired for FastAPI | Changed | Fits new service architecture |
| LLM Judge kept and wired | Kept | Already proven in Phase 5 |

---

## 5. Strict Rules (Carried From Phase 5 + New)

### Carried from Phase 5
- Client initialization always inside functions or class constructors — never at module level
- Constants come exclusively from settings.py
- No try/except blocks inside agent files — error handling via decorators only
- @handle_errors must be outermost in decorator chains
- No global mutable variables
- workflow_state is the sole communication channel between agents
- Zero prompt strings inside agent files — all prompts centralized in prompts.py
- Single Responsibility Principle: one agent, one responsibility

### New for Phase 6
- Flowchart-before-code is mandatory for every new component — no exceptions
- No Alembic migration mixed with business logic changes in the same commit
- Every migration must have a working downgrade() function
- AsyncSession must open and close per request — never per application
- startup_id must be included in every ChromaDB query — no exceptions
- All API errors must return the standard error envelope — no raw exceptions to client
- Pagination required on every list endpoint — no unbounded queries
- No Redis dependency anywhere in Phase 6 codebase

### Architecture rules
- FastAPI = thin service layer only. No business logic in routes.
- Repositories handle all DB queries. No raw SQL outside repository layer.
- Agents are never called directly from routes. Always through orchestrator.
- Memory extraction happens automatically after every user message.
- CASCADE DELETE lives at database level, not application level.

---

## 6. Approach

### Philosophy
Build the minimal backend infrastructure that gives the AI system persistent context, structured I/O, and a professional service boundary. Every non-AI component exists only to serve AI execution.

### Implementation order
Infrastructure first → Auth → APIs → Memory + RAG → Orchestration

This order is non-negotiable because:
- SP-01 database must exist before any other component
- SP-02 config must exist before any service initializes
- SP-03 auth must exist before any protected route
- SP-04 APIs depend on SP-01 + SP-03
- SP-05 memory depends on SP-02 ChromaDB + SP-04 APIs
- SP-06 orchestration depends on all previous sub-phases

### Development discipline
- One sub-phase at a time. No parallel implementation.
- Flowchart → Code → Test → Commit for every component.
- Each sub-phase has a validation gate. Gate must pass before moving forward.
- No feature additions mid-implementation without explicit redesign discussion.

---

## 7. Time Duration

**Total capacity:** 75 hours (5 hours/day × 15 days)

| Sub-Phase | Hours | Days |
|---|---|---|
| SP-01 Database Foundation | 12 | 1–2.5 |
| SP-02 Infrastructure | 6 | 2.5–3.5 |
| SP-03 Auth + FastAPI | 12 | 3.5–6 |
| SP-04 Core Resource APIs | 15 | 6–9 |
| SP-05 Memory + RAG | 15 | 9–12 |
| SP-06 Orchestration | 10 | 12–14 |
| Polish + Frontend + Docs | 5 | 15 |
| **Total** | **75** | **15 days** |

---

## 8. Sub-Phase Definitions

---

### SP-01 — Database Foundation
**Duration:** 12 hours  
**Days:** 1–2.5  
**Depends on:** Nothing  
**Enables:** Everything else  

**Scope:**
- 5 tables only: users, startups, conversations, messages, memories
- All relationships and foreign key constraints
- CASCADE DELETE: deleting a startup deletes its conversations, messages, and memories
- Message sequence numbers: atomic, no gaps under concurrent writes
- Alembic migrations with working upgrade() and downgrade() for every migration
- Async SQLAlchemy models with TimestampMixin
- Repository layer: one repository per table, no raw SQL outside repositories
- Async database session dependency for FastAPI

**Tables:**

| Table | Key Columns | Notes |
|---|---|---|
| users | user_id, email, password_hash, created_at | Soft delete not required |
| startups | startup_id, owner_id, name, description, stage, created_at | owner_id → users |
| conversations | conversation_id, startup_id, title, created_at | startup_id → startups CASCADE |
| messages | message_id, conversation_id, role, content, sequence_number, created_at | conversation_id → conversations CASCADE |
| memories | memory_id, startup_id, memory_type, content, importance, created_at | startup_id → startups CASCADE |

**Validation gate:**
- alembic upgrade head runs clean on fresh database
- alembic downgrade base runs clean from head
- CASCADE DELETE verified: delete startup → conversations + messages + memories deleted
- Message sequence number is unique under concurrent inserts
- All repository operations tested

---

### SP-02 — Infrastructure
**Duration:** 6 hours  
**Days:** 2.5–3.5  
**Depends on:** SP-01  
**Enables:** SP-03, SP-05  

**Scope:**
- Centralised settings/config file using pydantic-settings
- All environment variables in one place — no os.getenv() anywhere else
- Existing ChromaDB integration kept and wired under new config
- startup_id isolation added to ChromaDB: every write and every query must include startup_id in metadata/filter
- Local filesystem for PDF storage: server-controlled paths, never user-supplied filenames as paths
- Gemini embedding client wired under new config
- FastAPI dependency injection wrappers for DB session, ChromaDB, file storage, embedder

**What is NOT in SP-02:**
- Redis — skipped entirely
- Any business logic
- Any routes

**Validation gate:**
- All config loads from .env — missing required variable raises at startup not runtime
- ChromaDB write with startup_id=A, query with startup_id=B returns empty
- File store + retrieve round-trip produces identical bytes
- Path traversal attempt in filename is neutralised

---

### SP-03 — Auth + FastAPI Bootstrap
**Duration:** 12 hours  
**Days:** 3.5–6  
**Depends on:** SP-01, SP-02  
**Enables:** SP-04  

**Scope:**
- FastAPI application factory
- CORS middleware (basic, configurable origins)
- Request ID middleware: every request gets a unique ID, propagated through logs and response headers
- Standardised error envelope: every API error returns {error: {code, message, request_id}}
- Argon2id password hashing
- JWT access tokens (15 minute expiry)
- Refresh tokens (opaque, stored as SHA-256 hash in DB, 30 day expiry)
- get_current_user() dependency
- Health endpoints: /health/live and /health/ready
- Auth routes: register, login, refresh, logout

**Auth routes:**

| Route | Method | Response |
|---|---|---|
| /api/v1/auth/register | POST | 201 user created |
| /api/v1/auth/login | POST | 200 access + refresh tokens |
| /api/v1/auth/refresh | POST | 200 new access token |
| /api/v1/auth/logout | POST | 200 refresh token revoked |
| /api/v1/health/live | GET | 200 always |
| /api/v1/health/ready | GET | 200 or 503 |

**Validation gate:**
- Protected route with no token → 401
- Protected route with expired token → 401
- Protected route with valid token → correct user extracted
- Duplicate email → 409
- Wrong password → 401 (same message as wrong email — do not reveal which)
- Refresh token revoked after logout
- Error envelope correct for every error type

---

### SP-04 — Core Resource APIs
**Duration:** 15 hours  
**Days:** 6–9  
**Depends on:** SP-03  
**Enables:** SP-05, SP-06  

**Scope:**
- Full CRUD for: startups, conversations, messages, memories
- PDF upload endpoint with MIME type validation
- Pagination on all list endpoints: {items, page, page_size, total}
- Hard delete with CASCADE (DB-level, not application-level)
- API key rotation rewired to work under FastAPI service architecture
- Pydantic schemas: separate Create, Update, Response schemas per resource
- Authorization dependency: every startup route verifies ownership via DB lookup
- Server always assigns: user_id, sequence_number, message role — never from client

**Routes:**

| Resource | Operations |
|---|---|
| Startups | POST, GET list, GET by id, PATCH, DELETE |
| Conversations | POST, GET list, GET by id, PATCH, DELETE (hard, cascades) |
| Messages | POST (append only), GET list (paginated, ASC order) |
| Memories | GET list, DELETE |
| Documents | POST (upload), GET list, GET by id, DELETE (soft) |

**Rules:**
- No route accesses DB directly — always through repository
- No business logic in routes — always through service layer
- Cross-user access returns 404 not 403 (do not reveal existence)
- Messages are append-only: no PATCH, no DELETE on individual messages
- Pagination: max page_size = 100, default = 20

**Validation gate:**
- Authenticated user accessing another user's startup → 404
- Message sequence numbers unique under concurrent appends
- File upload: invalid MIME type → 422
- Pagination envelope correct on all list endpoints
- Cascade delete verified at API level

---

### SP-05 — Memory System + RAG Polish
**Duration:** 15 hours  
**Days:** 9–12  
**Depends on:** SP-02, SP-04  
**Enables:** SP-06  

**Scope:**

**Memory system:**
- Automatic LLM memory extraction after every user message
- Lightweight relevance check first (rule-based): skip short/greeting messages
- Deep extraction LLM call for substantive messages: extracts type, content, importance
- Memory types: startup_fact, preference, decision, goal, constraint
- Store extracted memories to PostgreSQL with startup_id scope
- Embed memory content via Gemini and store in ChromaDB with startup_id metadata
- Retrieve relevant memories using hybrid search (vector + BM25) + reranker
- Assemble retrieved memories into context string for LLM injection
- Redis cache: skipped — simple retrieval only
- No conflict detection or supersession

**RAG polish:**
- PDF text extraction: clean rewrite using pypdf
- Chunking: sentence-aware with overlap, clean implementation
- Embedding: Gemini embedding API, batched
- ChromaDB storage: startup_id isolation enforced on every chunk
- Hybrid retrieval: vector search + BM25 + CrossEncoder reranker (Phase 5 components cleaned)
- All RAG components rewritten for clarity — no logic changes, code quality improvement

**Document processing pipeline:**
- PDF uploaded via SP-04 endpoint
- Background processing: extract text → chunk → embed → store in ChromaDB
- Document status: UPLOADED → PROCESSING → READY / FAILED
- Retry: up to 3 attempts on embedding failure

**Validation gate:**
- Substantive message → at least one memory extracted and stored
- Memory retrieval: relevant query returns correct top results
- startup_id isolation: query from startup B never returns startup A memories or chunks
- Document processing: uploaded PDF reaches READY status with chunks in ChromaDB
- RAG query returns grounded results from correct startup's documents only

---

### SP-06 — Orchestration + Agent Wiring
**Duration:** 10 hours  
**Days:** 12–14  
**Depends on:** SP-01 through SP-05  
**Enables:** Polish phase  

**Scope:**
- TaskContext dataclass: structured input every agent receives from orchestrator
- AgentResult dataclass: structured output every agent returns to orchestrator
- Adapter wrappers on all 17 Phase 5 agents: accepts TaskContext, returns AgentResult
- Internal Phase 5 reasoning logic of each agent: untouched
- Orchestrator wired to FastAPI: workflow submission through API route
- Memory context injected into every agent execution via TaskContext
- RAG context injected into every agent execution via TaskContext
- LLM Judge kept and wired: validates workflow outputs before report assembly
- Pydantic validation on all workflow inputs and outputs
- Current Phase 5 scoring kept — no changes
- No autonomous planning, no DAG, no replanning

**Agent disposition:**

| Agent | Action |
|---|---|
| All 17 Phase 5 agents | Add TaskContext input + AgentResult output wrapper only |
| OrchestratorAgent | Wire to FastAPI, inject memory + RAG context |
| LLMJudgeAgent | Keep existing logic, wire to new contracts |
| ReportWriterAgent | Keep existing logic, wire to new contracts |

**Workflow API route:**

| Route | Method | Response |
|---|---|---|
| /api/v1/startups/{id}/workflows | POST | 202 workflow started |
| /api/v1/workflows/{id} | GET | workflow status + result |

**Validation gate:**
- All 17 agents accept TaskContext and return AgentResult without error
- Phase 5 7/7 intent suite still passes after wiring changes
- Memory context appears in agent execution
- LLM Judge validates output before report assembly
- Workflow submission through FastAPI route reaches correct agents

---

### Polish + Frontend + Documentation
**Duration:** 5 hours  
**Day:** 15  
**Depends on:** SP-01 through SP-06  

**Scope:**
- Basic frontend using AI-generated UI (Antigravity or similar)
- Connect frontend to FastAPI endpoints
- README update: Phase 6 capabilities, architecture diagram update
- CHANGELOG update
- LEARNING_LOG update
- Git tag: v6.0.0
- Final verification: all endpoints responding, workflow executing end to end

---

## 9. Concepts to Learn Before Each Sub-Phase

### Before SP-01
- Alembic: difference between `revision --autogenerate` and `upgrade head`
- AsyncSession lifecycle: why session opens and closes per request
- CASCADE DELETE: database-level vs application-level deletion

### Before SP-03
- JWT structure: header, payload, signature — what each contains
- Refresh token pattern: why store hash not raw token
- Argon2id: why it is preferred over bcrypt for password hashing

### Before SP-04
- Pagination: offset vs cursor-based — which is simpler to implement correctly
- MIME type validation: why file extension alone is not sufficient
- Message sequence numbers: why SELECT FOR UPDATE is needed under concurrency

### Before SP-05
- ChromaDB metadata filtering: how where clause works in query()
- BM25: what it measures and how it differs from vector similarity
- Memory extraction prompt engineering: how to get structured JSON from LLM reliably

### Before SP-06
- Dataclass vs Pydantic model: when to use each
- Dependency injection in FastAPI: how Depends() works in route functions

---

## 10. What Phase 6 Proves to a Recruiter

> "He knows how to build AI orchestration and AI systems, agentic AI, and multi-agent pipelines from first principles — without relying on any framework. He understands what happens inside frameworks like LangChain because he built those primitives himself. This gives him complete control over the system and the ability to debug it at any level."

This is the story. Every feature in this document serves this story. Nothing else does.

---

*Document frozen: September 22, 2026*  
*Next action: SP-01 implementation — begin with src/core/enums.py*
