# Changelog

All notable changes to BizRadar AI are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).
---
## [v4.0.0] — 2026-06-19 — Phase 4: Multi-PDF, Stage Gating & RAG Hardening

### Added
- `validate_stage_tools(stage, tool_call_list)` in `agent.py` — real gatekeeping logic replacing the old print-only stage counter. Per-`tool_call` check against `STAGE_MAP`, reverse-lookup `TOOL_TO_STAGE` for naming the correct stage in rejection messages, whole-batch rejection, missing-tool detection injected as `role: "user"`
- `where={"file_name": ...}` filtering added to `query_rag()`'s `collection.query()` call — enables document-scoped retrieval across multiple uploaded PDFs in a single shared ChromaDB collection
- `get_available_files(user_input)` upgraded with a relevance classifier — separate Gemini call returns real filenames only when the query is document-relevant, `""` otherwise
- `classify_document_relevance()` — standalone Gemini classifier function backing the upgraded `get_available_files()`
- Non-mutating file-list injection pattern in `run()` — `temp_list = self.messages.copy()`, conditional replace of `temp_list[0]` only if files exist, ReAct loop runs on `temp_list`, `self.messages.extend(temp_list[length:])` on exit
- `evaluator.py` — offline RAG evaluation tool. Hardcoded ground-truth query/page/filename pairs, calls `query_rag()` directly, calculates recall@3
- Paragraph-aware fixed-token chunker in `rag.py` — `CHUNK_SIZE=250`, `OVERLAP=50`, `STEP=200`; small paragraphs kept whole, large paragraphs split via sliding window
- Shared `stage_print_flag` in `agent.py` — distinguishes fresh stage prints from gating-retry prints, replacing the earlier broken Stage-4-only fix
- `SYSTEM_PROMPT` now passed as a proper `role: "system"` message in the final-answer generation call, alongside `final_prompt` as `role: "user"`

### Changed
- `function_args` for `market_context` / `mvp_context` / `startup_idea` now forcibly overwritten in code immediately before tool execution — bypasses LLM argument construction entirely, eliminating hallucinated context
- Earlier system-message-injection approach for context passing removed as dead weight once forced-argument-overwrite was confirmed working — reduces token overhead

### Fixed
- Bug A — hallucinated `market_context`/`mvp_context` — fixed via forced argument overwrite (see Changed above)
- Bug B (Part 1) — missing system prompt in final-answer generation call caused ungrounded output; real Tavily URL now correctly appears in Market Potential
- Stage-gating gap — `stage` was previously a print-label counter with no enforcement power; real LLM tendency to bundle `risk_analysis` + `search_documents` at Stage 3 now correctly caught and rejected, LLM retries correctly
- Chunking granularity — a 2-page PDF previously produced only 2 chunks under pure `\n\n` splitting; now produces properly granular chunks under the new chunker, with recall@3 unchanged at 100%

### Verified
- Cross-document RAG isolation — 100% of retrieved chunks matched the requested file across multi-PDF tests, zero contamination
- `evaluator.py` — 100% recall@3 across 5 documents, 25 questions, full corpus evaluation
- `temp_list`/`self.messages` isolation — `self.messages[0]` confirmed static across multiple turns; file list correctly reaches the LLM each call
- Document-relevance classifier — 3 of 4 known test cases pass

### Reclassified
- Rate-limit/token-budget concern — moved out of open-code-bugs tracking. Only concrete evidence collected is a Groq TPD quota error, which is a billing/quota constraint, not a `temp_list` architecture defect

### Known Issues (Open)
- Citation bug — "From Your Pitch Deck" output has no page/filename citations despite explicit `SYSTEM_PROMPT` rule
- Bug B (Part 2) — Competitor Insights still leaks document citations instead of its own `search_knowledge_base()` URL; unverified against current forced-overwrite architecture, needs fresh re-diagnosis
- Retrieval relevance/chunking drift — correct theme retrieved, but specific details paraphrase loosely rather than tightly grounding in retrieved chunks
- Classifier edge case — ambiguous "analyze this idea..." phrasing intermittently misclassifies as relevant; deferred pending a structural safety net

### Deliberate Scope Decisions (Accepted Risk)
- Stage 2/3 context truncated to 1000 chars at injection, on top of existing 2000-char storage truncation — deferred to post-persistence work
- `search_documents`'s `file_name` argument left LLM-trusted, not validated against the actual file list — deferred until `get_available_files()` supports multi-document summary-based selection

### Phase 4 Remaining
- Hybrid search (BM25 + vector search) — cleared to start, chunking dependency resolved
- Reranking (cross-encoder on top-k results) — depends on hybrid search

---

## [v3.6.0] — 2026-06-14 — Phase 3 Closure, RAG Integration & CLI Rewrite

### Added
- Rule 11 in `prompts.py` — explicit prohibition: search_documents() never called during Stages 1, 2, or 3
- Rule 13 in `prompts.py` — Stage 2/3 failure handling distinct from Rule 12 footer
- Stage 4 explicitly defined in `TOOL CALL ORDER` — "ONLY after Stage 3, never during Stages 1, 2, or 3"
- Chain of thought block in `SYSTEM_PROMPT` — LLM reasons about required stages before acting
- Per-section fallback notes in output format for Rule 13 failures
- Inner `try/except` per URL in `summarize_text()` Fan-In — failed URLs skipped, not propagated to caller
- All-failed guard in `summarize_text()` — `if not response` returns distinct fallback string
- Context guard in `analyze_market()` and `search_knowledge_base()` — error strings flagged before reaching LLM as market data
- 503 retry backoff in `_call_gemini_with_retry()` alongside existing 429 retry
- `time.sleep(25)` between Fan-Out URL submissions in `summarize_text()` — partial Gemini RPM mitigation
- `client.heartbeat()` in `rag.py` `embed_and_store()` — verifies ChromaDB connection before write
- `EMBEDDING_MODEL` constant in `rag.py` — single source of truth for both ingestion and retrieval phases
- Cross-stage prohibitions added to all tool descriptions in `tools_description.py`
- ASCII art banner, animated spinner, styled input prompts, turn counter in `app.py`
- Full keyboard interrupt handling in `app.py` — Ctrl+C, Ctrl+D, EOF all handled cleanly
- `handle_exit()` shared exit function — consistent shutdown from all exit paths

### Changed
- All Stage 2/3 error returns normalized to `"<X> unavailable — service error, no data retrieved."` — matches Rule 13 pattern
- `search_documents()` return format changed from stringified dict to plain text `[Page N, filename]: text` — enables direct LLM citation
- `text-embedding-004` → `gemini-embedding-001` in `rag.py` — 404 NOT_FOUND on free tier API key
- `n_results` reduced from 5 to 3 in `query_rag()` — prevents Stage 4 RAG results bloating self.messages context
- `completed_future.result(timeout=60)` → `timeout=120` in `agent.py` — accounts for sleep(25) per URL in summarize_text()
- Stage 4 print label fixed in `agent.py` — now prints "🔍 Stage 4 — Querying your document..." correctly
- `time.sleep(25)` removed from `agent.py` Fan-Out loop — redundant, throttling belongs in `tools.py`
- `import datetime` removed from `rag.py` — unused import
- `handle_document_upload()` moved outside `while True` loop in `app.py` — was prompting for upload on every conversation turn

### Fixed
- Bug 16 — Formatting: missing newline between Rule 9 and Rule 10 concatenated them as one rule
- Bug 17 — Per-URL failure in `summarize_text()` discarded all successful results — inner try/except fixes partial failure
- Bug 18 — `search_documents` batched in Stage 1 Fan-Out — explicit Stage 4 with prohibition fixed ordering
- Bug 19 — `search_documents` stringified dict output unreadable for citation — plain text format fixes it
- Bug 20 — Rule 12 footer triggered on Stage 2/3 failures — Rule 13 added for correct scoping
- Bug 21 — Gemini RPM exhaustion during Stage 1 parallel calls — sleep(25) partial mitigation
- Bug 22 — `text-embedding-004` returned 404 NOT_FOUND — switched to `gemini-embedding-001`
- Bug 23 — `query_embeddings` received `ContentEmbedding` object — fixed to `[response.embeddings[0].values]`

### Verified
- 4-stage pipeline (3+1) confirmed working — correct order, RAG triggers on document reference
- PDF citations appear with page numbers and filename in final report
- Rule 12 and Rule 13 fire correctly for their respective failure cases
- Phase 3 closed ✅

---

## [v3.5.0] — 2026-06-13 — Pipeline Verified & RAG Citation Fix

### Changed
- `SYSTEM_PROMPT` Rule 10 corrected from "four stages" → "three stages" — fixes contradiction between Rule 10 and TOOL CALL ORDER that was causing LLM to narrate instructions as prose instead of executing them
- `summarize_text` removed from `agent.py` `available_functions` — dead entry after architectural refactor
- Pipeline confirmed as 3 stages from LLM perspective — Stage 1 (parallel search + self-summarize) → Stage 2 (parallel MVP + tech stack) → Stage 3 (risk analysis alone)

### Fixed
- Stage print label edge case in `agent.py` — harmless cosmetic mislabeling on edge cases
- Prompt contradiction — `prompts.py` Rule 10 and TOOL CALL ORDER were inconsistent after Stage 2 removal
- `query_rag()` — now returns `{"text": ..., "metadata": ...}` dicts via `zip(documents, metadatas)` — enables proper source citations with page numbers and filenames

### Verified
- 3-stage pipeline confirmed working across 2 different startup ideas — correct order, no stage skipping, no batching

### In Progress
- `query_rag()` citation fix — implemented, pending PDF upload + query end-to-end test

### Phase 4 Backlog
- `task_type` parameter for Gemini `embed_content()` calls — `RETRIEVAL_DOCUMENT` for ingestion, `RETRIEVAL_QUERY` for querying
- `embed_and_store()` batch `add()` fails entirely on any duplicate ID — needs per-chunk upsert logic
- `conversation_history` persistence to disk/DB

---

## [v3.4.0] — 2026-06-12 — summarize_text Architecture Refactor

### Changed
- `summarize_text()` removed as LLM-callable tool — now called internally by `analyze_market()` and `search_knowledge_base()` before returning results
- `market_context` single parameter replaced with two separate parameters — `market_analysis` and `market_search` — across `suggest_mvp()`, `recommend_tech_stack()`, and `risk_analysis()`
- Stage 2 removed from `TOOL CALL ORDER` in `prompts.py` — pipeline is now 3 stages from LLM perspective
- `tools_description.py` — `summarize_text` removed entirely as LLM-callable tool

### Fixed
- Bug 4 — LLM no longer constructs nested JSON from raw Tavily results — summarization happens internally before results reach the agent — special character schema validation failures eliminated

---

## [v3.3.0] — 2026-06-11 — Phase 3 Pipeline Debugging & Stage Enforcement

### Added
- Iteration markers in `agent.py` — prints `"Stage N Executing!!"` at start of each `while True` iteration for pipeline diagnosis
- Rules 10–13 in `SYSTEM_PROMPT` — enforce stage execution order and context passing
- `market_context` parameter to `suggest_mvp()`, `recommend_tech_stack()`
- `market_context` and `mvp_context` parameters to `risk_analysis()`
- Hallucinated tool name guard in `agent.py` — unknown tool names append clean error to history instead of crashing

### Changed
- Temperature `0.5` → `0.3` in `agent.py` — increases instruction-following for strict stage ordering
- `TOOL CALL ORDER` in `prompts.py` — replaced verbose repetitive draft with consolidated final version
- `risk_analysis()` parameter renamed `idea` → `startup_idea` — consistent with all other tools
- `analyze_market()` and `search_knowledge_base()` — `max_results=3`, content truncated to 300 chars

### Fixed
- Bug 1 — LLM skipping Stages 2–4 entirely after Stage 1, hallucinating full report
- Bug 2 — `risk_analysis()` batched with Stage 3 tools before `suggest_mvp()` returned, causing hallucinated `mvp_context`
- Bug 3 — Stage 4 printed as executing but `risk_analysis()` never called — diagnosed via content-based checking
- `rag.py` — `genai.Client()` had no API key, now explicitly passes `GEMINI_API_KEY`
- `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()` — wrong `requests.exceptions` handlers replaced with correct Gemini exception types

---

## [v3.2.0] — 2026-06-10 — Agent Scoping Fixes & Prompt Pipeline

### Added
- Four-stage tool call pipeline in `prompts.py` — explicit sequential ordering with Fan-Out at Stage 1 and Stage 3
- Hallucinated tool name guard in `agent.py` — unknown tool names now append a clean error message to history instead of crashing
- `self.context_loaded` boolean flag — prevents `get_context()` from reloading history on every conversation turn

### Fixed
- `self.future` was an instance variable — observed real bug where two rapid calls shared the same dict, corrupting results. Moved to local variable inside `run()`
- System prompt was appended inside `run()` — duplicated on every follow-up question. Moved to `__init__()`
- `future.clear()` removed — was dead code executing on a local variable already out of scope after the `with` block

---

## [v3.1.0] — 2026-06-09 — Tool Context & Exception Fixes

### Added
- `market_context` parameter to `suggest_mvp()` — injects live market research into MVP prompt for deeper, grounded output
- `market_context` parameter to `recommend_tech_stack()` — injects market conditions into stack recommendation prompt
- `market_context` and `mvp_context` parameters to `risk_analysis()` — risk assessment now aware of both market state and MVP scope
- Precondition instructions in `tools_description.py` for `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()` — LLM now knows these tools require upstream context before being called
- When-to-call instruction added to `summarize_text()` description

### Fixed
- `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()` were using `requests.exceptions` handlers — these tools use the Gemini client which raises `google.api_core.exceptions`, not `requests.exceptions`. Replaced with correct exception types.

---

## [v3.0.0] — 2026-06-08 — Phase 3 Complete

### Added
- `rag.py` — complete RAG pipeline built from scratch
  - `ingest_pdf()` — PDF to paragraph chunks via pdfplumber
  - `embed_and_store()` — chunks to vectors via Gemini embeddings, stored in ChromaDB
  - `query_rag()` — user question to top 5 relevant chunks via cosine similarity
- `search_documents` tool in `tools.py` — connects RAG pipeline to ReAct agent
- `search_documents` JSON schema in `tools_description.py`
- PDF ingestion trigger in `app.py` — runs before the conversation loop starts
- `database/chroma_db/` — persistent ChromaDB vector store directory
- All missing runtime dependencies in `requirements.txt`

### Changed
- Agent can now answer questions grounded in uploaded documents — no hallucination
- `app.py` now asks user for document upload before entering conversation loop
- `requirements.txt` updated with all actual runtime dependencies

### Fixed
- `requirements.txt` was missing `groq`, `google-genai`, `tavily-python`, `chromadb`, `pdfplumber`
---
## [v2.0.0] — 2026-06-07 — Phase 2 Complete

### Added
- ReAct agent loop in `agent.py` — `while True` with tool_calls detection
- Parallel tool execution via `ThreadPoolExecutor` and `as_completed`
- Groq LPU inference — Llama 3.3 70B replacing local Ollama
- Live Tavily web search — `analyze_market()` and `search_knowledge_base()`
- Gemini 2.5 Flash analysis tools — `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()`
- `tools_description.py` — separate JSON schema layer for all tools
- Provider-specific exception handling for Groq and Gemini

### Changed
- Replaced placeholder tools with real API integrations
- Replaced Ollama local inference with Groq LPU

---

## [v1.0.0] — 2026-06-01 — Phase 1 Complete

### Added
- `agent.py` — core agent class with manual tool execution
- `app.py` — CLI conversation loop
- `context_manager.py` — sliding window memory, last 6 turns
- `tools.py` — placeholder tools for market, MVP, tech stack, risk analysis
- `prompts.py` — system prompt with structured output format
- `.env` support via `python-dotenv`
- `.gitignore` — secrets and cache excluded from day one