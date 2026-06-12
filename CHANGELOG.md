# Changelog

All notable changes to BizRadar AI are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---
## [v3.3.0] — 2026-06-10 — Phase 3 Pipeline Debugging & Stage Enforcement

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

### In Progress
- Bug 4 — `summarize_text()` schema validation failing due to special characters (`\xa0`, escaped quotes) in Tavily search results
- Architecture proposal — move `summarize_text()` internal to `analyze_market()` and `search_knowledge_base()` under evaluation

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

## [v3.0.0] — 2026-06-08 — Phase 3

### Added
- `rag.py` — complete RAG pipeline built from scratch
  - `ingest_pdf()` — PDF to paragraph chunks via pdfplumber
  - `embed_and_store()` — chunks to vectors via Gemini text-embedding-004, stored in ChromaDB
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

## [v2.0.0] — Phase 2 Complete

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

## [v1.0.0] — Phase 1 Complete

### Added
- `agent.py` — core agent class with manual tool execution
- `app.py` — CLI conversation loop
- `context_manager.py` — sliding window memory, last 6 turns
- `tools.py` — placeholder tools for market, MVP, tech stack, risk analysis
- `prompts.py` — system prompt with structured output format
- `.env` support via `python-dotenv`
- `.gitignore` — secrets and cache excluded from day one