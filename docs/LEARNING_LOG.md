<div align="center">

# 📓 BizRadar AI — Learning Log

<sub>A personal record of concepts learned, decisions made, mistakes caught, and what comes next. Updated after every meaningful session or milestone.</sub>

[![Phase](https://img.shields.io/badge/Current_Phase-4_In_Progress-blue?style=for-the-badge)]()
[![Phase 3](https://img.shields.io/badge/Phase_3-Complete-brightgreen?style=for-the-badge)]()
[![Version](https://img.shields.io/badge/Version-v4.0.0-orange?style=for-the-badge)]()
</div>

---

## 👤 Engineer

**Ankush Poonia** — B.Tech AI/ML, 2nd Year, Arya College of Engineering, Jaipur

---

## 📊 Current Status

```
Phase 1 ✅ Complete
Phase 2 ✅ Complete
Phase 3 ✅ Complete — Closed
Phase 4 🔄 In Progress
Phase 5 📋 Planned
Phase 6 📋 Planned
```

---

## ✅ Phase 1 Log — Foundation Agent

**Completed:** BizRadar AI v1.0.0

### Concepts Learned

- [x] **AI Agent Architecture** — An agent has a brain (LLM), memory (context), and hands (tools). The agent loop connects all three.
- [x] **Prompt Engineering** — System prompts define behavior. Output format instructions produce structured responses. Rules constrain hallucination.
- [x] **Context Window Management** — Conversation history is passed manually on every API call. The sliding window (last 6 turns) balances memory vs token cost.
- [x] **OOP for AI Systems** — `StartupAgent` class encapsulates model name, base URL, and the `run()` method. Separation of concerns keeps files focused.
- [x] **Local LLM with Ollama** — Ollama runs models locally via a REST API on port 11434. No internet required for inference.
- [x] **Tool Architecture** — Tools are just Python functions. The agent calls them manually and injects results into the prompt.
- [x] **Environment Variables** — API keys live in `.env`, loaded via `python-dotenv`. Never hardcoded, never committed.

### Mistakes Made & Fixed

| Mistake | What Happened | Fix |
|---|---|---|
| `.env` file exposed | API keys nearly pushed to GitHub | Created `.gitignore` with `.env` listed |
| Vague tool outputs | Placeholder tools returned generic strings | Replaced with real Tavily + Gemini calls in Phase 2 |

### Key Insight From This Phase
> Tools called manually in a fixed sequence is not an agent — it is a pipeline. A real agent decides which tools to call and when. That realization led directly to Phase 2.

---

## ✅ Phase 2 Log — Real Tool Integrations

**Completed:** BizRadar AI v2.0.0

### Concepts Learned

- [x] **ReAct Pattern** — Reasoning + Acting. The LLM reasons about what it needs, calls a tool, observes the result, reasons again, and loops until the answer is complete.
- [x] **Groq LPU Inference** — Groq uses purpose-built Language Processing Units instead of GPUs. Dramatically faster token generation. Free tier available.
- [x] **Tool Calling / Function Calling** — The LLM does not run code. It returns a structured `tool_calls` object with the function name and arguments. The developer executes it.
- [x] **Tool Schema Design** — JSON schemas tell the LLM what tools exist, what they do, and what parameters they accept. Description quality directly affects tool selection accuracy.
- [x] **ThreadPoolExecutor** — Submits multiple tool calls simultaneously. Each call runs in its own thread. Results collected via `as_completed`.
- [x] **`as_completed` vs `executor.map`** — `as_completed` yields results as they finish. `map` waits for all and returns in order. `as_completed` is faster when tools have different response times.
- [x] **Fan-Out Fan-In Pattern** — Dispatch multiple tasks simultaneously (fan-out), collect all results before proceeding (fan-in).
- [x] **Multi-Provider Architecture** — Groq for fast reasoning, Gemini for analysis tools, Tavily for web search. Each provider used for what it does best.
- [x] **Tavily Search API** — `include_answer`, `search_depth`, `exclude_domains`, `country` parameters. Returns structured results with title, content, and URL.
- [x] **Provider-Specific Error Handling** — Each API has its own exception types. Groq: `AuthenticationError`, `RateLimitError`. Gemini: `ResourceExhausted`, `Unauthenticated`.
- [x] **Chain of Thoughts** — Prompting LLMs to break down complex problems into intermediate reasoning steps before answering.
- [x] **Preprocessing in Agentic Workflows** — Preparing dynamic, real-time inputs so an autonomous agent can reason, plan, and take the correct actions.

### Mistakes Made & Fixed

| Mistake | What Happened | Fix |
|---|---|---|
| `self.future` not cleared | Stale futures accumulated across ReAct loop iterations | Added `self.future.clear()` after each tool round |
| Generic tool descriptions | LLM picked wrong tools | Rewrote descriptions with specific, precise language |

### Key Insight From This Phase
> The LLM does not execute tools — it only requests them. The developer bridges the gap. Understanding this boundary is fundamental to building any agent system.

---

## ✅ Phase 3 Log — RAG & Document Intelligence
 
**Completed:** BizRadar AI v3.0.0
 
---
 
### 🏗️ Part 1 — Building Phase 3
 
#### Concepts Learned
 
- [x] **The Hallucination Problem** — BizRadar produced a McKinsey citation not present in Tavily results. It came from LLM training memory — unverified and potentially wrong. RAG solves this by constraining the LLM to answer only from retrieved document chunks.
- [x] **Why Keyword Search Fails** — Two failure modes: same meaning different words (misses relevant content), same words different meaning (returns irrelevant content). Vector similarity solves both.
- [x] **Vector Embeddings** — Text converted to lists of decimal numbers like `[0.23, 0.87, 0.45]` where each number captures a dimension of meaning. Similar meanings produce similar number lists. Reasoned from scratch starting from binary.
- [x] **Cosine Similarity** — Measuring the angle between two vectors to determine semantic similarity. Small angle = similar meaning. Derived from basic geometry independently.
- [x] **RAG Two-Phase Pipeline** — Phase 1 (ingestion, runs once): PDF → chunks → vectors → ChromaDB. Phase 2 (retrieval, every query): question → vector → cosine search → top chunks → LLM → answer.
- [x] **Vector Space Consistency** — Same embedding model must be used for both ingestion and querying. Different models produce different vector dimensions — similarity comparison becomes meaningless.
- [x] **Chunk Size Trade-offs** — Too large: irrelevant content dilutes the relevant answer. Too small: context gets fragmented, LLM cannot construct a meaningful answer.
- [x] **ChromaDB** — `PersistentClient`, `get_or_create_collection`, `collection.add()` (ids, embeddings, documents, metadatas), `collection.query()` returns nested list — use `[0]` for single query.
- [x] **Metadata in ChromaDB** — `filename` and `page_number` keys enable filtering across multiple PDFs. Page number stored as integer for numeric comparison.
- [x] **PDF Parsing with pdfplumber** — `enumerate(pdf.pages, start=1)` tracks page numbers. `\n\n` splitting creates paragraph chunks. List comprehension filters empty strings.
- [x] **Hash-Based Deduplication** — `hashlib.md5(chunk["text"].encode()).hexdigest()` as chunk ID prevents duplicate ingestion even when the same PDF is renamed.
- [x] **Graceful Error Handling** — `try/except chromadb.errors.DuplicateIDError` returns a clear user message instead of crashing.
#### Technical Decisions Made
 
| Decision | Reasoning |
|---|---|
| `PersistentClient` over `Client()` | Data must survive between sessions |
| `get_or_create_collection` | Safe for repeated initialization — no crash on restart |
| `gemini-embedding-001` | `text-embedding-004` returned 404 NOT_FOUND on free tier API key — switched to stable production alternative |
| Same model for Phase 1 and Phase 2 | Different models produce different vector spaces — similarity search breaks |
| MD5 hash of chunk text as ID | Prevents duplicates even when the same PDF is renamed |
| Flat list structure for chunks | Simplifies the embedding loop — no nested iteration |
| pdfplumber over PyPDF2 | Better handling of complex PDF layouts like pitch decks |
| `\n\n` paragraph chunking | Each paragraph contains one complete idea — meaningful retrieval unit |
| `try/except DuplicateIDError` | Graceful duplicate handling — user gets a clear message instead of a crash |
| `if not search_response` in tool | Handles empty collection edge case before returning to agent |
 
#### Mistakes Made & Fixed
 
| Mistake | What Happened | Fix |
|---|---|---|
| Jumped to code before reasoning 4 times | Habit of using code as an anchor under uncertainty | Write `# Input / Output / Steps` before every function — no exceptions |
| Lost mental model mid-session | Too many moving parts held simultaneously under cognitive overload | Say "let me start fresh" — retrace from first principles before continuing |
 
#### Key Insight From This Phase
> RAG does not make the LLM smarter — it constrains it. By telling the LLM "answer only from these retrieved chunks," you remove its ability to insert unverified information from training memory. The answer quality comes from retrieval quality, not model quality.
 
#### The Permanent Rule Set This Phase
 
Before writing any function — write this first. No exceptions:
 
```
# Input:
# Output:
# Steps:
#   1.
#   2.
#   3.
```
 
Fill it. Verify it. Then code.
 
---
 
### 🐛 Part 2 — Debugging Phase (v3.1.0–v3.5.0)
 
---
 
### Session Update v3.1.0 — tools.py & tools_description.py Refinements
 
#### Changes Made
 
**`tools.py`**
- `suggest_mvp()` — `market_context` parameter added, injected into prompt
- `recommend_tech_stack()` — `market_context` parameter added, injected into prompt
- `risk_analysis()` — `market_context` and `mvp_context` parameters added, both injected into prompt
- `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()` — wrong `requests.exceptions` handlers replaced with correct `google.api_core.exceptions` types
**`tools_description.py`**
- `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()` — precondition instructions added to descriptions
- `summarize_text()` — when-to-call instruction added
- `risk_analysis()` — `mvp_context` parameter added to schema
- All three analysis functions — `market_context` parameter added to schema
#### Why These Changes
 
| Change | Reasoning |
|---|---|
| `market_context` added | Analysis tools produced generic output without real market data — injecting Tavily results gives the model accurate market conditions, producing deeper grounded responses |
| `mvp_context` added to `risk_analysis()` | Risk analysis differs based on what is actually being built — generic risks without MVP awareness are not actionable |
| Fixed exception handlers | `requests.exceptions` are never raised by Gemini client calls — errors were falling silently to bare `except Exception`, losing precise diagnosis |
 
#### Key Insight
> Injecting upstream context into downstream tools produces significantly deeper output than isolated prompts. Each tool should know what the previous stage found.
 
---
 
### Session Update v3.2.0 — agent.py & prompts.py Refactor
 
#### Changes Made
 
**`agent.py`**
- `self.future` moved from `__init__()` to local variable in `run()` — prevents concurrent call corruption
- System prompt append moved from `run()` to `__init__()` — prevents duplicate system prompt on follow-up questions
- `self.context_loaded` boolean flag added — guards `get_context()` so history loads only once per session
- `future.clear()` removed — local variable already garbage collected after `with` block exits, dead code
- Hallucinated tool name guard added — unknown tool names append clean `role=tool` error message instead of crashing
- Temperature changed `0.5` → `0.3` — increases instruction-following for strict stage ordering
- Dev note comments replaced with real Fan-Out/Fan-In explanations
**`prompts.py`**
- Four-stage `TOOL CALL ORDER` added — sequential pipeline with explicit Fan-Out and Fan-In markers
- Rules 10–13 added — enforce stage execution order and context passing before final answer
#### Why These Changes
 
| Change | Reasoning |
|---|---|
| `self.future` made local | Observed real bug — two rapid calls shared the same instance-level dict, corrupting futures across calls |
| System prompt to `__init__()` | `run()` is called every turn — prompt was appending multiple times, inflating message history |
| `context_loaded` flag | `get_context()` should run once at session start — not reload history on every follow-up |
| `future.clear()` removed | Local variable is out of scope after `with` block — `.clear()` was executing on a dead reference |
| Hallucinated tool guard | Bare `except Exception` was silently swallowing `KeyError` — clean error message lets LLM reason about the failure |
| Four-stage pipeline | Without explicit ordering, tools were called out of sequence — downstream tools received empty context |
 
#### Key Insights
> Instance variables persist across calls — local variables reset every call. Wrong choice causes real concurrency bugs, not theoretical ones.
 
> Boolean flags are the simplest initialization guard. One flag, one line, prevents an entire class of repeated-work bugs.
 
---
 
### Session Update v3.3.0 — Pipeline Debugging
 
#### Bugs Found & Fixed
 
| Bug | File | Description | Root Cause | Fix |
|---|---|---|---|---|
| Bug 9 — Stage Skipping | `prompts.py` | LLM skipped Stages 2–4, hallucinated full report from Stage 1 alone | No enforcement mechanism requiring all stages to complete before answering | Added Rules 10–13 to `SYSTEM_PROMPT`, consolidated `TOOL CALL ORDER` into single non-repetitive rule |
| Bug 10 — Stage 4 Batching | `prompts.py` | `risk_analysis()` called in same batch as Stage 3 before `suggest_mvp()` returned — `mvp_context` hallucinated | No explicit instruction separating Stage 3 and Stage 4 | Added "Do not combine with Stage 3" instruction to Stage 4 |
| Bug 11 — Silent Stage 4 Skip | `agent.py`, `prompts.py` | Stage 4 marker printed but `risk_analysis()` never called — Risks section hallucinated | Tool call logs alone cannot show absence of a call | Added iteration markers — diagnosed via content-based checking |
 
#### Diagnostic Techniques Used
 
| Technique | What It Shows |
|---|---|
| Tool call logs | What tools were called |
| Iteration markers (`Stage N Executing!!`) | Absence of tool calls within a stage |
| Content-based diagnosis | Whether report sections reflect real tool output or LLM hallucination — generic output with no connection to actual tool results = hallucinated |
 
#### Other Changes
- Temperature `0.5` → `0.3` in `agent.py` — reduces randomness, increases instruction-following
- Consolidated `TOOL CALL ORDER` — replaced four separate "do not return before X" lines with one unified rule
#### Key Insights
> The LLM always finds the shortest path to a valid-looking answer. If that path skips tools, it will — unless the prompt makes skipping explicitly impossible. Enforcement beats instruction.
 
> All three diagnostic techniques were needed across different bugs — no single technique was sufficient alone.
 
---
 
### Session Update v3.4.0 — summarize_text Architecture Refactor
 
#### Changes Made
 
**`tools.py`**
- `summarize_text()` moved from LLM-callable tool to internal function
- Called inside `analyze_market()` and `search_knowledge_base()` before each returns
- Each function now returns a plain `str` summary directly
- `market_context` split into two separate parameters — `market_analysis` and `market_search`
**`tools_description.py`**
- `summarize_text` removed entirely as LLM-callable tool
**`prompts.py`**
- Stage 2 (`summarize_text`) removed from `TOOL CALL ORDER`
- Pipeline reduced from 4 stages to 3 stages from LLM perspective
- `market_context` references updated to `market_analysis` and `market_search`
**`agent.py`**
- `summarize_text` removed from `available_functions` dispatch map — dead entry after refactor
#### Why These Changes
 
| Change | Reasoning |
|---|---|
| `summarize_text()` made internal | LLM constructing nested JSON from raw Tavily results with special characters (`\xa0`, escaped quotes, em-dashes) is a design flaw — not fixable with character replacement |
| `market_context` split into `market_analysis` + `market_search` | Each search tool produces distinct insights — keeping them separate gives downstream tools richer, more targeted context |
| Stage 2 removed from prompt | `summarize_text()` no longer visible to LLM — no instruction needed for a tool the LLM cannot call |
| Nested `ThreadPoolExecutor` | Outer pool runs search tools in parallel, each internally spawns own pool for per-URL summarization — confirmed working |
 
#### Key Insights
> Architectural fixes remove problems entirely. Prompt fixes and character replacement reduce symptoms. They are not equivalent — always prefer the architectural fix when available.
 
> Nested `ThreadPoolExecutor` is safe — outer parallel execution and inner parallel execution operate independently.
 
---
 
### Session Update v3.5.0 — Pipeline Verified & RAG Citation Fix
 
#### Verification Status
 
| Item | Status |
|---|---|
| 3-stage pipeline — correct order, no skipping, no batching | ✅ Confirmed across 2 different startup ideas |
| `query_rag()` citation fix — end-to-end PDF upload + query test | ⏳ Pending — rate limit hit during testing |
 
#### Changes Made
 
**`rag.py`**
- `query_rag()` now returns `{"text": ..., "metadata": ...}` dicts via `zip(documents, metadatas)`
- Previously discarded `page_number` and `file_name` metadata already stored in ChromaDB
- Enables proper source citations in agent responses
**`prompts.py`**
- Rule 10 corrected from "four stages" → "three stages" — was contradicting `TOOL CALL ORDER` after Stage 2 removal
**`agent.py`**
- Stage print label edge case fixed ✅

---
### Session Update v3.6.0 — Phase 3 Closure & RAG Integration

#### Changes Made

**`prompts.py`**
- Rule 11 — added explicit prohibition: "Never call search_documents() during Stages 1, 2, or 3"
- Rule 12 — Stage 1 both-unavailable fallback with explicit stop condition
- Rule 13 — added: Stage 2/3 failure handling distinct from Rule 12 footer
- Stage 4 — added explicitly in TOOL CALL ORDER: "ONLY after Stage 3, never during Stages 1, 2, or 3"
- Chain of thought block added — LLM reasons about which stages are required before acting
- Output format — per-section fallback notes for Rule 13 added
- Formatting bug fixed — missing newline between Rule 9 and Rule 10

**`tools.py`**
- Inner `try/except` per URL in `summarize_text()` Fan-In — failed URLs skipped, not propagated
- All-failed guard added — `if not response: return "Summarization unavailable..."`
- Context guard added in `analyze_market()` and `search_knowledge_base()` — error strings flagged as `[MARKET DATA UNAVAILABLE]` before reaching LLM
- All Stage 2/3 error returns normalized to `"<X> unavailable — service error, no data retrieved."` matching Rule 13 pattern
- `search_documents()` return format changed to plain text `[Page N, filename]: text` — enables direct citation
- `time.sleep(25)` added between Fan-Out URL submissions in `summarize_text()` — RPM partial mitigation
- 503 retry added alongside 429 retry — `exceptions.ServiceUnavailable` handled

**`tools_description.py`**
- `search_documents` description rewritten — explicit Stage 4, "ONLY after Stages 1, 2, and 3", "Do not call during Stage 1, 2, or 3"
- All tool descriptions — cross-stage prohibitions added per tool

**`rag.py`**
- `text-embedding-004` → `gemini-embedding-001` — fixes 404 NOT_FOUND on free tier API key
- `EMBEDDING_MODEL` constant added — single source of truth for both phases
- `[response.embeddings[0].values]` — fixes ChromaDB query format error
- `n_results` reduced from 5 to 3 — prevents Stage 4 RAG bloating self.messages context
- `client.heartbeat()` added in `embed_and_store()` — verifies DB connection before write
- `import datetime` removed — was unused

**`agent.py`**
- `time.sleep(25)` removed from Fan-Out loop — redundant, throttling belongs in `summarize_text()`
- Stage 4 print label fixed — now prints "🔍 Stage 4 — Querying your document..." instead of "Stage 4 of 3"
- `completed_future.result(timeout=60)` → `timeout=120` — accounts for summarize_text() sleep(25) per URL
- Trailing comma removed from `run()` signature

#### Why These Changes

| Change | Reasoning |
|---|---|
| Rule 13 added | Rule 12 footer was triggering on Stage 2/3 failures — wrong scope. Stage 1 success must not be invalidated by downstream failures |
| Stage 4 explicit in TOOL CALL ORDER | "On-Demand" instruction caused LLM to batch search_documents in Stage 1 Fan-Out — explicit Stage 4 with prohibition fixed it |
| summarize_text inner try/except | Single URL failure was discarding all successful results — partial success should return partial data |
| sleep(25) in summarize_text | Stage 1 parallel calls were firing 6 simultaneous Gemini requests — exceeded 5 RPM free tier limit |
| gemini-embedding-001 | text-embedding-004 returned 404 on this API key version — not available on v1beta API |
| Plain text search_documents output | Stringified dict required LLM to parse structured data — same fragility class as Bug 12. Plain text with inline citations is directly readable |

#### Phase 3 Done Criteria — Verified ✅
1. Tool calls fire in correct stage order — no skips, no batching ✅
2. Report content reflects actual tool output, not hallucination ✅
3. RAG triggers when user references uploaded document ✅
4. PDF citations appear with page numbers and filename ✅
5. Rule 12 and Rule 13 fire correctly for the right failure cases ✅

#### Key Insights
> Rule scope matters — a rule that fires for the wrong case is as dangerous as no rule. Rule 12 footer was a false alarm when Stage 2/3 failed — it masked Stage 1's real success.

> Partial success is better than total failure. summarize_text() skipping failed URLs and returning what succeeded is more useful than returning one error string when any URL fails.

> The LLM will always find the most permissive interpretation of your instructions. "On-Demand" with no timing constraint was interpreted as "anytime I want." "ONLY after Stage 3, never during Stages 1, 2, or 3" is unambiguous.
---
## 🛠️ Complete Bug Registry table
| Bug No  | Type of Bug  | File Name | Issue | Solution | Status |
|---|---|---|---|---|---|
| Bug 1 | Missing API Key | `rag.py` | `genai.Client()` called with no `api_key` — crashed on startup | Added `load_dotenv()`, `os.getenv("GEMINI_API_KEY")`, passed explicitly | ✅ |
| Bug 2 | Wrong Exception Handlers | `tools.py` | `requests.exceptions` used in Gemini functions — never raised by Gemini client | Replaced with correct `google.api_core.exceptions` types | ✅ |
| Bug 3 | Inconsistent Parameter Name | `tools.py`, `tools_description.py` | `risk_analysis()` used `idea` — LLM passed `startup_idea`, got `KeyError` | Renamed `idea` → `startup_idea` in function and schema | ✅ |
| Bug 4 | Shared Future Dict | `agent.py` | `self.future` shared across concurrent calls — corrupted results | Moved to local variable inside `run()` | ✅ |
| Bug 5 | System Prompt Duplication | `agent.py` | System prompt appended in `run()` — duplicated on every follow-up | Moved to `__init__()` — appended once per session | ✅ |
| Bug 6 | Context Reloading Every Turn | `agent.py` | `get_context()` called on every `run()` — reloaded history repeatedly | Added `self.context_loaded` boolean flag | ✅ |
| Bug 7 | Dead Code future.clear() | `agent.py` | `future.clear()` on already out-of-scope local variable | Removed entirely | ✅ |
| Bug 8 | Hallucinated Tool Name Crash | `agent.py` | Unknown tool name caused `KeyError` swallowed by bare `except Exception` | Added guard — appends clean `role=tool` error message | ✅ |
| Bug 9 | Stage Skipping | `prompts.py` | LLM skipped Stages 2–4, hallucinated full report | Added Rules 10–13, consolidated `TOOL CALL ORDER` | ✅ |
| Bug 10 | Stage 4 Batching | `prompts.py` | `risk_analysis()` batched with Stage 3 — `mvp_context` hallucinated | Explicit Stage 4 separation instruction | ✅ |
| Bug 11 | Silent Stage 4 Skip | `agent.py`, `prompts.py` | Stage 4 marker printed but `risk_analysis()` never called | Iteration markers + content-based diagnosis + stronger enforcement | ✅ |
| Bug 12 | Schema Validation 400 — summarize_text JSON crash | `tools.py`, `tools_description.py`, `prompts.py` | LLM hand-constructing nested JSON from raw Tavily results — special characters broke Groq validation | Moved `summarize_text()` internal — removed as LLM-callable tool | ✅ |
| Bug 13 | Prompt Contradiction | `prompts.py` | Rule 10 said "four stages" after pipeline reduced to 3 | Updated Rule 10 to "three stages" | ✅ |
| Bug 14 | Stale available_functions Entry | `agent.py` | `summarize_text` left in dispatch map after removal | Removed from `available_functions` | ✅ |
| Bug 15 | query_rag() Metadata Discarded | `rag.py` | Metadata already stored in ChromaDB discarded on retrieval — no citations possible | Returns `{"text": ..., "metadata": ...}` dicts via `zip()` | ✅ |
| Bug 16 | Formatting Bug — Rules 9+10 Concatenated | `prompts.py` | Missing newline between Rule 9 and Rule 10 produced `"...assumption.10. Do not generate..."` — concatenated as one rule | Added newline between rules | ✅ |
| Bug 17 | Per-URL Failure Poisoning summarize_text | `tools.py` | Single URL Gemini failure propagated to outer except — discarded all successful URL results, returned one error string | Inner `try/except` per URL in Fan-In loop — skip failures, `if not response` returns distinct fallback | ✅ |
| Bug 18 | Stage 2/3 Skipped — search_documents Batched in Stage 1 | `prompts.py`, `tools_description.py` | LLM batched all 6 tools including search_documents into Stage 1 Fan-Out — Stage 2/3 tools received empty context | Explicit Stage 4 in TOOL CALL ORDER — "ONLY after Stage 3, never during Stages 1, 2, or 3" | ✅ |
| Bug 19 | search_documents Output Unreadable for Citation | `tools.py` | Returning stringified list of dicts — LLM couldn't reliably extract page_number/file_name for citations | Reformatted to plain text: `[Page N, filename]: text` per chunk | ✅ |
| Bug 20 | Rule 12 Footer Misapplied to Stage 2/3 Failures | `prompts.py`, `tools.py` | Rule 12 disclaimer triggered when Stage 2/3 tools failed even though Stage 1 succeeded with real data | Added Rule 13 — Stage 2/3 failures get per-section notes only, no footer. Normalized error strings to `"<X> unavailable — service error, no data retrieved."` | ✅ |
| Bug 21 | Gemini RPM Exhaustion During Stage 1 | `tools.py` | analyze_market() + search_knowledge_base() run in parallel, each firing up to 3 Gemini calls — up to 6 simultaneous calls exceeded 5 RPM free tier limit | `time.sleep(25)` between Fan-Out URL submissions inside summarize_text() — partial mitigation | ⚠️ Partial |
| Bug 22 | text-embedding-004 — 404 NOT_FOUND | `rag.py` | text-embedding-004 unavailable on free tier API key with google-genai SDK v1.75.0 | Switched to `gemini-embedding-001` — stable production alternative on free tier | ✅ |
| Bug 23 | query_embeddings Format Wrong | `rag.py` | ChromaDB received `ContentEmbedding` object instead of raw float list — TypeError on query | Fixed to `[response.embeddings[0].values]` — extracts float list, wraps in list for ChromaDB format | ✅ |
---
## 🎯 Phase 4 Entry Checklist

Before starting Phase 4 — complete these:

1. **Run clean end-to-end test** — LegalAid PDF + startup analysis prompt with fresh Groq quota. Confirm all 4 stages fire in order, RAG citations appear with page numbers and filename.
2. **Resolve Phase 4 backlog in priority order:**

| # | Item | File | Priority |
|---|---|---|---|
| 1 | Shared rate-limiter/semaphore for Gemini RPM across both Stage 1 callers | `tools.py` | High |
| 2 | `embed_and_store()` batch fails entirely on duplicate ID — needs per-chunk upsert | `rag.py` | High |
| 3 | RAG query rewriting — investigate `user_input` passed to `search_documents`, improve chunk relevance | `rag.py`, `tools.py` | High |
| 4 | `task_type` missing in `embed_content()` — `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY` | `rag.py` | Medium |
| 5 | Multi-PDF support — ChromaDB `where` clause filtering by filename | `rag.py`, `tools_description.py` | Medium |
| 6 | Document-only query flow — skip pipeline, `search_documents` only | `prompts.py` | Medium |
| 7 | `conversation_history` not persisted across process restarts | `context_manager.py` | Medium |
| 8 | Debug print hardcodes `"search_documents returned:"` — use `function_name` variable | `agent.py` | Low |
| 9 | Stage print labels — dynamic "Stage N of M" based on whether Stage 4 fires | `agent.py` | Low |

3. **Answer before starting Phase 4** — right now `query_rag()` searches all documents. What is the minimum change needed to make it search only one specific file using ChromaDB `where` clause? Do not code. Reason first. Flowchart second. Code third.
---

## 🔄 Phase 4 Log — Multi-PDF, Stage Gating & RAG Hardening

**Status:** In Progress — BizRadar AI v4.0.0

### 🎯 Milestone

Multi-PDF ingestion with document-scoped retrieval via metadata filtering, stage-order enforcement, and RAG evaluation tooling — building on the closed Phase 3 pipeline.

---

### ✅ Completed & Verified This Phase

#### 1. Cross-Document Isolation (`where` Filter)

`embed_and_store()` already tagged chunks with `file_name` + `page_number` metadata in a single shared collection. Rejected a per-file-collection design after cost/benefit reasoning — added `where={"file_name": ...}` to `query_rag()`'s `collection.query()` call instead.

**Verified live:** 100% of retrieved chunks matched the requested file, zero cross-document contamination.

#### 2. File-List Awareness For The LLM

Built `get_available_files()` using `.get(include=["metadatas"])` + `set()` dedup. Designed a non-mutating injection pattern in `run()`:

```python
length = len(self.messages)
temp_list = self.messages.copy()
temp_list[0] = {...}  # new dict, not mutated in place
# ReAct loop runs on temp_list
self.messages.extend(temp_list[length:])
```

**Verified live** across multiple turns — `self.messages[0]` stays permanently static; `temp_list[0]` carries the dynamic file list each call. Caught and fixed a real shallow-copy mutation bug along the way: `temp_list[0]["content"] = X` mutates the shared dict in place (bug); `temp_list[0] = {...}` (assigning a brand new dict) does not (fix).

#### 3. Stage-Order Enforcement (`validate_stage_tools`)

Diagnosed that `stage` was previously just a print-label counter with **zero gatekeeping power** — the actual root cause of an intermittent staging violation that had been silently present since Phase 3 (a "closed" bug that was never actually reliably re-verified).

Built `validate_stage_tools(stage, tool_call_list)`:
- Per-`tool_call` check against a `STAGE_MAP`
- Reverse-lookup (`TOOL_TO_STAGE`) to name the *correct* stage in rejection messages
- Whole-batch rejection, not per-tool
- Missing-tool detection injected as a `role: "user"` message — correctly reasoned out of `role: "system"` and `role: "assistant"` as the wrong fit

**Verified live:** caught a real, repeated LLM tendency to bundle `risk_analysis` + `search_documents` together at Stage 3, correctly rejected the batch, LLM retried correctly on the next iteration.

#### 4. Document-Relevance Classifier

Diagnosed that even with the file list visible, the LLM sometimes called `search_documents` on queries with no document reference at all — a prompt-rule non-compliance issue, not a missing-information issue.

Rejected two flawed fixes first:
- A `has_file_context` flag — solves the wrong problem; files persist across turns regardless of how the upload prompt was answered
- A per-turn manual user question — too much friction for the user

Landed on a separate Gemini classifier call inside an upgraded `get_available_files(user_input)`: returns real filenames when the query is document-relevant, `""` otherwise. Went through three prompt iterations.

**Status:** 3 of 4 known test cases pass. One known unreliable case remains — "analyze this idea with full tech stack and MVP suggestion" intermittently misclassifies as `true` even with explicit negative examples and `temperature=0.0`. **Conclusion:** not unsolvable, but evidence that prompt-only classification has a real, non-zero error rate. Needs a structural safety net eventually (e.g. a second-opinion check using actual retrieval similarity scores), not more prompt tuning. Logged as a known limitation — deferred, not blocking.

#### 5. Stage Print-Flag Fix

Replaced the earlier broken "Stage 4 only" fix with a single shared `stage_print_flag`: initializes `True` before the loop, flips `False` after the first print of any stage, resets `True` after `stage += 1` on the successful path. Retry messages now print distinctly from fresh stage messages — no more misleading repeated "Stage N — Executing tools..." lines during a gating rejection/retry cycle.

#### 6. `evaluator.py` — Built And Verified

Offline, standalone RAG evaluation tool. Takes hardcoded ground-truth query–answer pairs (question + correct page + correct filename), calls `query_rag()` directly, checks metadata match, calculates recall@3.

**Verified: 100% recall@3 across 5 documents, 25 questions**, full corpus evaluation, zero cross-document contamination.

#### 7. Chunking Improvement (`rag.py`)

Replaced pure `\n\n` paragraph splitting with a paragraph-aware fixed-token chunker — `CHUNK_SIZE=250`, `OVERLAP=50`, `STEP=200`. Small paragraphs kept whole; large paragraphs split via sliding window.

**Verified:** a 2-page PDF that previously produced only 2 chunks now produces properly granular chunks. Evaluator re-run confirmed 100% recall@3 post-migration — the chunking change did not regress retrieval quality.

#### 8. Bug A — Hallucinated Context (Fixed)

Fixed via forced argument overwrite: `function_args` is forcibly overwritten in code right before tool execution, bypassing LLM argument construction entirely for `market_context` / `mvp_context` / `startup_idea`. An earlier system-message-injection approach was correctly identified as dead weight once the forced-overwrite approach was confirmed working, and removed — eliminating wasted token overhead.

#### 9. Bug B (Part 1) — Missing System Prompt In Final Call (Fixed)

`SYSTEM_PROMPT` is now passed as a proper `"role": "system"` message alongside `final_prompt` as `"role": "user"` in the final-answer generation call. **Confirmed via test run:** a real Tavily URL correctly appeared in the Market Potential section.

---

### ⚠️ Reclassified — Not A Code Bug

**Rate-limit / token-budget concern.** The only concrete evidence collected is a Groq TPD quota error — this is a **billing/quota constraint, not a `temp_list` architecture defect**. Moved out of the open-code-bugs table to avoid implying it's still architectural. The deterministic stress test (forcing `MAX_STAGE_RETRIES` to confirm or rule out an actual unbounded-growth problem) was designed across multiple sessions but **never built or run** — three sessions running now without resolution. Needs an explicit decision next session: build it, or consciously drop it from the list rather than letting it silently roll over again.

---

### 🔴 Open Bugs

| # | Bug | File(s) | Priority | Status |
|---|---|---|---|---|
| 1 | Citation bug — "From Your Pitch Deck" output has no page/filename citations despite explicit `SYSTEM_PROMPT` rule requiring them | `prompts.py`, `agent.py` | High | Open |
| 2 | Bug B (Part 2) — Competitor Insights leaks document citations instead of its own `search_knowledge_base()` URL | `agent.py`, `prompts.py` | High | **Unverified against the current forced-overwrite architecture — must be re-diagnosed fresh, not assumed to be the same bug seen earlier** |
| 3 | Retrieval relevance / chunking drift — correct theme retrieved, but specific details paraphrase loosely rather than tightly grounding in actual retrieved chunks | `rag.py` | Medium | Open |
| 4 | Classifier edge case — ambiguous "analyze this idea..." phrasing intermittently misclassifies as `true` | `rag.py` | Medium | Deferred — needs a structural safety net, not more prompt tuning |

---

### 📝 Deliberate Scope Decisions (Accepted Risk, Not Oversight)

1. **Stage 2/3 context truncated to 1000 chars at injection**, on top of the existing 2000-char storage truncation — intentional, deferred to post-persistence work.
2. **`search_documents`'s `file_name` argument left LLM-trusted**, not validated against the actual file list — intentional, deferred until `get_available_files()` is upgraded to support multi-document summary-based selection rather than filename-only matching.

---

### 🔜 Remaining Phase 4 Implementation

| # | Item | Depends On |
|---|---|---|
| 1 | Hybrid search (BM25 + vector search) | Chunking improvement ✅ — cleared to start |
| 2 | Reranking (cross-encoder on top-k results) | Hybrid search |

---

### 📋 Standing Rules (Upgraded This Phase)

1. **Flowchart before code** — Input / Output / Steps written and verified before any function is coded. No exceptions.
2. **Session checklist first** — build an ordered checklist before diving into any new phase or session.
3. **Small, clear questions** — multiple related small questions allowed together; no dense paragraph-style bundles of unrelated things.
4. **Explicit answer feedback** — correct parts confirmed, wrong parts named precisely, no silent moving on.
5. **Low-pressure session opens** — new chat starts with one simple question confirming prior session completion, not forceful interrogation.

---

### 🔁 Recurring Pattern — Tracked Across Multiple Sessions This Phase

Proposing an architectural fix **before** diagnosing the actual root cause of a symptom. Confirmed instances this phase: per-file collections, the upload-flag, the `has_file_context` flag, "remove Stage 4 from validation," merging Stage 3+4, the stage-print-flag mechanism (twice), proposing hybrid chunking before confirming paragraph splitting was the real problem.

Every single time, self-correction happened once directly challenged with "what's the actual evidence this mechanism touches that function?" — that questioning reflex is real growth from earlier phases. The *first instinct* toward unjustified complexity is still present, though. Standing fix: before proposing any mechanism, explicitly answer "which function is producing this symptom, and what evidence do I have that this fix touches that function?" — out loud, before writing code.

### ✅ Before Next Phase 4 Session

1. Re-run the LegalAid/AGI test, check Competitor Insights specifically for its own `search_knowledge_base()` URL (Open Bug #2 above) — unverified against current architecture.
2. Decide explicitly on the deterministic retry-forcing test — build it or formally drop it. Don't let it roll over a fourth time.
3. Confirm the rate-limit issue is correctly filed as a quota issue, not sitting in any table implying architectural fault.

---

## 📋 Phase 5 Log — Multi-Agent Architecture

**Status:** Not Started

### Concepts To Learn
- [ ] Orchestrator pattern — coordinator agent that delegates to specialists
- [ ] Agent communication and handoffs
- [ ] Shared memory between agents
- [ ] Specialized agent design — narrow scope, deep focus
- [ ] Failure handling — what happens when a sub-agent times out

### Questions I Have Right Now
*(Fill in before starting Phase 5)*

---

## 📋 Phase 6 Log — Autonomous Platform

**Status:** Not Started

### Concepts To Learn
- [ ] Long-term memory with SQLite
- [ ] asyncio fundamentals — event loops, coroutines, `gather()`
- [ ] FastAPI REST layer
- [ ] Dynamic planning and goal decomposition
- [ ] Startup scoring rubric (0–100)

---

## 💡 Running Insights

| Phase | Insight |
|---|---|
| Phase 1 | A fixed tool pipeline is not an agent — an agent decides |
| Phase 2 | The LLM requests tools, the developer executes them — never forget this boundary |
| Phase 2 | `as_completed` is better than `map` when tools have unequal response times |
| Phase 2 | Tool description quality directly determines tool selection accuracy |
| Phase 3 | RAG constrains the LLM — retrieval quality determines answer quality, not model quality |
| Phase 3 | Same embedding model for ingestion and retrieval is non-negotiable — different models break vector space |
| Phase 3 | Flowchart before code is not a rule — it is a cognitive tool for managing complexity |
| Phase 3 | Exception handlers must match the library making the call — always check which client is used first |
| Phase 3 | Instance variables persist across calls — local variables reset. Wrong choice causes real concurrency bugs |
| Phase 3 | One-time initialization belongs in `__init__()` — repeated-call logic belongs in `run()` |
| Phase 3 | The LLM always finds the shortest path to a valid-looking answer — enforcement beats instruction |
| Phase 3 | Tool call logs show what was called. Iteration markers show absence of calls. Content analysis shows whether real data was used. All three needed |
| Phase 3 | Architectural fixes remove problems entirely — prompt fixes and character replacement reduce symptoms only |
| Phase 3 | Nested `ThreadPoolExecutor` is safe — outer and inner pools operate independently |
| Phase 3 | Prompt contradictions compound — stale references across files can independently cause failures after the main fix |
| Phase 3 | After any structural change — immediately audit all files for stale cross-file references |
| Phase 3 | Fixing symptoms and fixing root cause are not the same thing — always diagnose before patching |
| Phase 3 | Injecting upstream context into downstream tools produces significantly deeper output than isolated prompts |
| Phase 3 | Rule scope matters — a rule that fires for the wrong case is as dangerous as no rule |
| Phase 3 | Partial success is better than total failure — skip failed URLs, return what succeeded |
| Phase 3 | The LLM finds the most permissive interpretation — "On-Demand" means "anytime." Be explicit |
| Phase 4 | A counter that only labels stages but doesn't gate them is decoration, not enforcement — `validate_stage_tools` closed a real, previously-unverified gap |
| Phase 4 | Shallow-copy mutation through a dict reference is invisible until you trace it — reassigning a new dict at the index is the fix, not mutating the existing one in place |
| Phase 4 | Prompt-only classification has a non-zero, irreducible error rate — a fourth prompt rewrite is not guaranteed to close a case three rewrites already couldn't |
| Phase 4 | A "closed" bug from a previous phase is not guaranteed closed — re-verify under the current architecture before assuming continuity |
| Phase 4 | Reclassifying a bug correctly (quota vs. architecture) changes where it should live in your tracking, not just its priority |
| Phase 4 | Offline evaluation (recall@k against ground truth) is a different category of confidence than live spot-checking — build the evaluator early, not as an afterthought |
---

## 🐛 Mistakes & Lessons

| Phase | Mistake | Root Cause | Lesson |
|---|---|---|---|
| Phase 1 | Nearly pushed API keys to GitHub | Did not create `.gitignore` early enough | Always create `.gitignore` before first `git add` |
| Phase 2 | Stale futures across ReAct loop iterations | Did not clear `self.future` dict | Stateful objects in loops must be explicitly reset |
| Phase 2 | Wrong tool selected by LLM | Vague tool descriptions | Precision in tool schemas directly affects agent behavior |
| Phase 3 | Jumped to code before reasoning 4 times | Habit of using code as anchor under uncertainty | Write `# Input / Output / Steps` before every function — no exceptions |
| Phase 3 | Lost mental model mid-session | Too many moving parts held simultaneously | Say "let me start fresh" — retrace from first principles |
| Phase 3 | Wrong exception types in Gemini tools | Copy-pasted handlers from Tavily functions without checking client | Exception handlers must match the library making the call |
| Phase 3 | `self.future` as instance variable | Assumed instance variables were safe for loop state | Anything reset-per-iteration belongs as a local variable |
| Phase 3 | System prompt appended in `run()` | One-time setup placed in repeatedly-called method | One-time initialization belongs in `__init__()` |
| Phase 3 | Jumped to prompt drafts before completing diagnosis | Habit of reaching for solutions before understanding the problem | Complete diagnosis fully before proposing any fix |
| Phase 3 | Four separate "do not return" lines in prompt | Over-engineering enforcement | One consolidated rule beats four repetitive lines — LLMs respond to clarity, not volume |
| Phase 3 | Character replacement attempted before root cause diagnosis | Reached for symptom fix first | Always diagnose root cause before patching symptoms |
| Phase 3 | Rule 10 not updated after Stage 2 removal | Forgot to audit cross-file references after structural change | After any structural change audit all files immediately |
| Phase 3 | Rule 12 footer triggered on Stage 2/3 failures | Wrong rule scope — Stage 1 success does not invalidate Stage 2/3 failures | Each rule must have a precisely scoped trigger condition |
| Phase 3 | search_documents batched in Stage 1 | "On-Demand" with no timing constraint interpreted as "anytime" | Be explicit — "ONLY after Stage 3, never during Stages 1, 2, or 3" |
| Phase 3 | handle_document_upload() inside while True loop | One-time setup placed inside repeated loop | Startup operations belong before the loop — never inside it |
| Phase 4 | Proposed per-file ChromaDB collections before checking if `where` filtering on a shared collection would work | First instinct toward more architecture instead of checking if the simpler mechanism already solves it | Always check whether the existing single-collection design can be filtered before reaching for a structural split |
| Phase 4 | Proposed a `has_file_context` flag to fix relevance misclassification | Solved the wrong problem — files persist across turns regardless of upload-prompt history | Trace what the flag would actually condition on before building it |
| Phase 4 | Proposed merging Stage 3 and Stage 4 print logic without confirming root cause first | Assumed the symptom (double "Stage 3" print) meant the stages should be combined, before checking if it was the gating-retry pattern | Diagnose the actual cause of a printed symptom before proposing a structural merge |
| Phase 4 | Assumed Bug B (Part 2) was still the same bug after switching to forced-argument-overwrite | New architecture can change adjacent behavior — old diagnosis doesn't automatically transfer | Re-diagnose against the current file, don't assume bug continuity across an architecture change |
| Phase 4 | Deterministic retry-forcing test designed three sessions running, never built | Kept losing priority to more urgent diagnosis work without an explicit decision to deprioritize it | If something rolls over repeatedly, explicitly decide to build it or drop it — don't let it default-carry forward silently |

---

## 📈 Learning Patterns Tracked

| Pattern | Phase 1 | Phase 2 | Phase 3 | Trend |
|---|---|---|---|---|
| Jumping to code before reasoning | Frequent | Frequent | 4 times | Improving |
| Skipping harder questions | — | Noted | 2 times | Needs attention |
| Answering in fragments not prose | — | — | 3 times | Persistent |
| Skipping assigned reading | Frequent | Frequent | Improved | Getting better |
| Copying code without understanding | Frequent | Reduced | Rare | Strong improvement |
| Flowchart before coding | Not followed | Not followed | Followed | Real change |
| Jumping to fixes before diagnosis | — | — | Multiple | Needs attention |
| Cross-file consistency check after changes | — | — | Missed once | Now enforced |
| Content-based diagnosis skill | — | — | Demonstrated | New skill acquired |
---

## 📚 Resources Used

| Resource | Topic | Rating |
|---|---|---|
| Groq Documentation | LPU inference, API setup | ⭐⭐⭐⭐⭐ |
| Tavily Documentation | Search API parameters | ⭐⭐⭐⭐⭐ |
| Gemini API Docs | `google.genai` client, `embed_content()` | ⭐⭐⭐⭐ |
| Python `concurrent.futures` docs | ThreadPoolExecutor, as_completed | ⭐⭐⭐⭐⭐ |
| ChromaDB Documentation | Collections, `add()`, `query()`, metadata | ⭐⭐⭐⭐⭐ |
| pdfplumber Documentation | PDF text extraction, page enumeration | ⭐⭐⭐⭐ |

---

## 🎯 Next — Phase 4 Continues

Phase 4 is in progress. Multi-PDF, stage gating, evaluator, and chunking improvements are done and verified. Next session priorities: Bug B (Part 2) re-verification, the deterministic retry-forcing test decision, then hybrid search.
---

<div align="center">

<sub>Updated after every session. Honest entries only. — BizRadar AI v4.0.0 | Phase 3 Closed | Phase 4 In Progress</sub>

</div>