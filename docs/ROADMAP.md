<div align="center">

# 🧭 BizRadar AI — Roadmap

<sub>A phase-by-phase build path. Every phase ends with a concrete capability — something you can demonstrate, not just describe.</sub>

[![Phase](https://img.shields.io/badge/Current_Phase-4_In_Progress-blue?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Phase_3-Complete-brightgreen?style=for-the-badge)]()
[![Version](https://img.shields.io/badge/Version-v4.0.0-orange?style=for-the-badge)]()
</div>

---

## 📊 Overall Progress

| Phase | Title | Status | Completion |
|---|---|---|---|
| Phase 1 | Foundation Agent | ✅ Complete | 100% |
| Phase 2 | Real Tool Integrations | ✅ Complete | 100% |
| Phase 3 | RAG & Document Intelligence | ✅ Complete | 100% |
| Phase 4 | Multi-PDF & Advanced RAG | 🔄 In Progress | See breakdown below |
| Phase 5 | Multi-Agent Architecture | 📋 Planned | 0% |
| Phase 6 | Autonomous Research Platform | 📋 Planned | 0% |

---

## ✅ Phase 1 — Foundation Agent

<div align="center">
<sub><b>Outcome:</b> A working local AI agent that holds a conversation, remembers context, and calls tools manually.</sub>
</div>

<br>

<details>
<summary><b>📚 Concepts Covered</b></summary>
<br>

- [x] What is an AI Agent — definitions, components, responsibilities
- [x] Prompt Engineering — system prompts, output formatting, constraints
- [x] Context Window Management — what fits, what gets cut, sliding window
- [x] Tool Architecture — what tools are, why agents need them
- [x] OOP Design for AI — classes, separation of concerns, modularity
- [x] Local LLM Deployment — Ollama, model pulling, inference parameters
- [x] HTTP API Communication — requests library, POST payloads, error handling
- [x] Environment Variables — `.env`, `python-dotenv`, secret management

</details>

<details>
<summary><b>🔨 What Was Built</b></summary>
<br>

| File | Purpose |
|---|---|
| `agent.py` | Core agent class with manual tool execution |
| `app.py` | CLI conversation loop |
| `context_manager.py` | Sliding window memory — last 6 turns |
| `tools.py` | Placeholder tools — market, MVP, tech stack, risk |
| `prompts.py` | System prompt with structured output format |

</details>

<details>
<summary><b>⚖️ Key Decisions</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| No LangChain or LlamaIndex | Architecture first — understand internals before abstractions |
| Ollama for local inference | Privacy and zero API cost during learning |
| Manual tool execution | Understand the pattern before automating it |

</details>

<br>

> **Milestone:** BizRadar holds a multi-turn conversation, remembers the last 6 turns, and calls tools in a fixed sequence.

---

## ✅ Phase 2 — Real Tool Integrations

<div align="center">
<sub><b>Outcome:</b> A true ReAct agent that decides which tools to call, executes them in parallel, and produces cited startup analysis reports.</sub>
</div>

<br>

<details>
<summary><b>📚 Concepts Covered</b></summary>
<br>

- [x] ReAct Pattern — Reasoning + Acting loop, tool_calls handling
- [x] Groq API — LPU inference, authentication, model selection
- [x] Tool Calling / Function Calling — tool schemas, JSON definitions, required fields
- [x] Tool Schema Design — how descriptions affect LLM tool selection accuracy
- [x] Parallel Execution — `ThreadPoolExecutor`, `as_completed`, `executor.submit`
- [x] Fan-Out Fan-In Pattern — dispatching multiple tasks, collecting results
- [x] `as_completed` vs `executor.map` — when to use each
- [x] Tavily Search API — query parameters, `include_answer`, `exclude_domains`
- [x] Gemini API — `google.genai`, prompt templates, `generate_content`
- [x] Error Handling — provider-specific exceptions (Groq, Gemini, Tavily)
- [x] Multi-Provider Architecture — mixing LLM providers in one system

</details>

<details>
<summary><b>🔨 What Was Built</b></summary>
<br>

| File | Purpose |
|---|---|
| `agent.py` | ReAct loop — `while True`, tool_calls detection, parallel execution |
| `tools.py` | Live Tavily search + Gemini-powered analysis tools |
| `tools_description.py` | JSON tool schemas for LLM tool-calling interface |

</details>

<details>
<summary><b>⚖️ Key Decisions</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| Groq over Ollama | LPU speed + free tier for development |
| Gemini 2.5 Flash for analysis | Cost-effective, fast, high quality |
| Parallel tool execution | Reduce latency from sequential to simultaneous |
| Tool schemas in separate file | Clean separation of concerns |

</details>

<br>

> **Milestone:** BizRadar receives a startup idea, decides which tools to call, executes them in parallel, and returns a structured report with cited sources — no hardcoded tool execution order.

---

## ✅ Phase 3 — RAG & Document Intelligence

<div align="center">
<sub><b>Outcome:</b> BizRadar can ingest a PDF pitch deck and answer questions grounded entirely in the document — zero hallucination.</sub>
</div>

<br>

<details>
<summary><b>📚 Concepts Covered</b></summary>
<br>

- [x] The Hallucination Problem — why LLMs produce confident but unverified citations
- [x] Why Keyword Search Fails — same meaning different words, same words different meaning
- [x] Vector Embeddings — text as lists of decimal numbers capturing semantic meaning
- [x] Cosine Similarity — angle between vectors as a measure of semantic closeness
- [x] RAG Two-Phase Pipeline — ingestion once, retrieval every query
- [x] Vector Space Consistency — same embedding model for both phases
- [x] ChromaDB — `PersistentClient`, `get_or_create_collection`, `add()`, `query()`
- [x] Chunking Strategies — paragraph chunking via `\n\n`, chunk size trade-offs
- [x] PDF Parsing — pdfplumber over PyPDF2 for complex layout handling
- [x] Metadata Filtering — `filename` and `page_number` for multi-document support
- [x] Duplicate Handling — MD5 hash as chunk ID, `DuplicateIDError` graceful catch
- [x] Retrieval Pipeline — embed query → cosine search → top-k chunks → LLM

</details>

<details>
<summary><b>🔨 What Was Built</b></summary>
<br>

| File | Purpose |
|---|---|
| `rag.py` | Complete RAG pipeline — `ingest_pdf()`, `embed_and_store()`, `query_rag()` |
| `tools.py` | `search_documents` tool added — connects RAG to ReAct agent |
| `tools_description.py` | `search_documents` JSON schema added |
| `app.py` | PDF ingestion trigger before conversation loop |
| `database/chroma_db/` | Persistent vector store on disk |

</details>

<details>
<summary><b>⚖️ Key Decisions</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| `PersistentClient` | Data must survive between sessions |
| `gemini-embedding-001` | `text-embedding-004` returned 404 on free tier API key — switched to stable alternative |
| MD5 hash as chunk ID | Prevents duplicates even with renamed files |
| pdfplumber over PyPDF2 | Better complex PDF layout handling |
| `\n\n` paragraph chunking | One complete idea per chunk |
| `try/except DuplicateIDError` | Graceful duplicate handling |

</details>

<br>

> **Milestone:** User provides a pitch deck PDF. BizRadar ingests it, stores vectors in ChromaDB, and answers document-specific questions with grounded responses — no hallucination.

---

## 🔄 Phase 4 — Multi-PDF & Advanced RAG

<div align="center">
<sub><b>Outcome:</b> BizRadar ingests multiple PDFs in one session, isolates retrieval per document, and gates document access to only the turns that actually need it.</sub>
</div>

<br>

<details open>
<summary><b>✅ Done & Verified</b></summary>
<br>

| # | Item | Verification |
|---|---|---|
| 1 | Cross-document isolation via `query_rag(where={"file_name": ...})` | 100% isolation confirmed across multiple uploaded PDFs |
| 2 | Per-turn file-list injection (`temp_list`/`length`/`extend()` pattern in `orchestrator.py`) | `self.messages[0]` confirmed static across turns — no permanent pollution |
| 3 | `validate_stage_tools()` real stage gating in `orchestrator.py` | Replaced print-only counter; caught real LLM stage-bundling violations |
| 4 | Document-relevance classifier — `classify_document_relevance()` + `get_available_files(user_input)` in `rag.py` | 3 of 4 known test cases pass reliably (see Open Items) |
| 5 | Stage print-flag fix in `orchestrator.py` | `stage_print_flag` distinguishes fresh-stage prints from gating-retry prints |
| 6 | `evaluator.py` — Recall@3 benchmark | 100% recall@3 across 5 documents, 25 ground-truth questions, **at time of last run** |
| 7 | Paragraph-aware fixed-token chunking in `rag.py` | Fixes dense-PDF under-chunking (a 2-page report previously produced only 2 chunks via pure `\n\n` split). `CHUNK_SIZE=250`, `OVERLAP=50`, `STEP=200`. Verified via evaluator — no regression at time of test |
| 8 | Hallucinated-context bug — forced `function_args` overwrite for `market_context`/`mvp_context`/`startup_idea` | Fixed in `orchestrator.py` |
| 9 | Missing system prompt in final synthesis call | Fixed — real Tavily URLs now appear correctly in final report |
| 10 | `__main__` guard added to `rag.py`'s batch re-ingestion block | Without it, importing `rag.py` anywhere silently re-ingested 12 hardcoded files on every run — caught during Phase 4 decoration |

> ⚠️ **Recall@3 status — unverified on current code.** Item 6/7's 100% figure was confirmed against an earlier `rag.py` state. The version now committed (chunking + decoration changes, commit `03329d4`) has **not** been re-run through `evaluator.py` — blocked by Gemini rate limits at time of last attempt. Treat "100% recall@3" as a past result, not a current guarantee, until re-verified.

</details>

<details>
<summary><b>🔴 Open Bugs</b></summary>
<br>

| # | Bug | Priority | Notes |
|---|---|---|---|
| 1 | "From Your Pitch Deck" section missing page/filename citations in some runs | High | Open |
| 2 | Competitor Insights section leaks document citations instead of its own `search_knowledge_base()` URL (Bug B Part 2) | High | **Unverified against current forced-overwrite architecture** — flagged across multiple sessions, never re-tested live |
| 3 | Retrieval relevance drift — correct theme returned, details paraphrase loosely | Medium | Open |
| 4 | Classifier misclassifies one ambiguous phrasing ("analyze this idea with full tech stack and MVP suggestion") | Medium | Confirmed structural, not a prompt-wording issue — temperature=0.0 and explicit FALSE examples already in place. Needs a structural safety net (e.g. retrieval-similarity second opinion), not another prompt rewrite |
| 5 | `classify_document_relevance()`'s ~100-line prompt still hardcoded inline in `rag.py` instead of centralized in `prompts.py` as a `CLASSIFIER_PROMPT` constant | Low | Newly identified — `prompts.py` is the established source of truth for all other LLM-facing prompt strings; this one was missed |

</details>

<details>
<summary><b>📝 Deliberate Scope Decisions (accepted tradeoffs, not bugs)</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| Stage 2/3 context truncated to 1000 chars at injection time (on top of 2000-char storage truncation) | Deferred to post-persistence work — not a current defect |
| `search_documents()`'s `file_name` argument is LLM-trusted, not validated against the live file list | Deferred until `get_available_files()` supports multi-doc summary-based selection |

</details>

<details>
<summary><b>🔜 Remaining Phase 4 Work</b></summary>
<br>

| Item | Status |
|---|---|
| Hybrid search (BM25 + vector) | Cleared to start — chunking dependency resolved |
| Reranking (cross-encoder) | Depends on hybrid search landing first |

</details>

<br>

> **Verified Capability:** Multiple PDFs can be uploaded in one session. Retrieval is correctly isolated per document via ChromaDB's `where` filter — querying one file does not leak chunks from another. A relevance classifier gates whether Stage 4 (document retrieval) is even reachable on a given turn, rather than leaving that decision to prompt instructions alone.

---

## 📋 Phase 5 — Multi-Agent Architecture

<div align="center">
<sub><b>Outcome:</b> A 5-section startup report where each section is researched and written by a specialized agent coordinated by an orchestrator.</sub>
</div>

<br>

<details>
<summary><b>📚 Concepts To Learn</b></summary>
<br>

- [ ] Multi-agent systems — why one agent cannot do everything well
- [ ] Orchestrator pattern — coordinator agent that delegates to specialists
- [ ] Agent communication — how agents pass context and results between each other
- [ ] Specialized agent design — narrow scope, deep focus per agent
- [ ] Shared memory — agents reading from and writing to a common state store
- [ ] Agent handoffs — when and how an orchestrator decides to delegate
- [ ] Failure handling — what happens when a sub-agent fails or times out

</details>

<details>
<summary><b>🔨 Agents To Build</b></summary>
<br>

| Agent | Responsibility |
|---|---|
| `orchestrator_agent.py` | Receives user input, delegates to specialists |
| `market_research_agent.py` | Deep market and competitor analysis |
| `tech_advisor_agent.py` | Architecture and stack recommendations |
| `report_writer_agent.py` | Compiles all agent outputs into final report |

</details>

<br>

> **Milestone:** BizRadar produces a multi-section report where each section comes from a dedicated specialist agent.

---

## 📋 Phase 6 — Autonomous Research Platform

<div align="center">
<sub><b>Outcome:</b> Single input. Fully autonomous research. Scored, cited, structured report — no follow-up prompts required.</sub>
</div>

<br>

<details>
<summary><b>📚 Concepts To Learn</b></summary>
<br>

- [ ] Long-term memory — persistent storage beyond context window (SQLite)
- [ ] Dynamic planning — agent breaks down a goal into subtasks automatically
- [ ] Startup scoring — building a scoring rubric and evaluation framework (0–100)
- [ ] Asyncio — `async/await`, event loops, replacing ThreadPoolExecutor
- [ ] Streaming responses — token-by-token output for better UX
- [ ] REST API layer — FastAPI wrapper around the agent
- [ ] Rate limiting and retry logic — exponential backoff, circuit breaker pattern

</details>

<details>
<summary><b>🔨 What To Build</b></summary>
<br>

| File | Purpose |
|---|---|
| `memory_store.py` | Persistent long-term memory with SQLite |
| `planner.py` | Goal decomposition into subtask list |
| `scorer.py` | Startup viability scoring with rubric |
| `api.py` | FastAPI endpoints exposing agent as a service |

</details>

<br>

> **Milestone:** User types a startup idea once. BizRadar autonomously researches, scores, and delivers a full report with no follow-up prompts.

---

## 🎯 Skills Unlocked Per Phase

| Skill | Phase | Status |
|---|---|---|
| Prompt Engineering | Phase 1 | ✅ Unlocked |
| Context Window Management | Phase 1 | ✅ Unlocked |
| Local LLM Deployment | Phase 1 | ✅ Unlocked |
| OOP Architecture for AI | Phase 1 | ✅ Unlocked |
| ReAct Agent Pattern | Phase 2 | ✅ Unlocked |
| Tool Calling / Function Calling | Phase 2 | ✅ Unlocked |
| Parallel Execution | Phase 2 | ✅ Unlocked |
| Multi-Provider LLM Integration | Phase 2 | ✅ Unlocked |
| Vector Embeddings | Phase 3 | ✅ Unlocked |
| RAG Pipelines | Phase 3 | ✅ Unlocked |
| ChromaDB / Vector Search | Phase 3 | ✅ Unlocked |
| PDF Document Intelligence | Phase 3 | ✅ Unlocked |
| Multi-Document RAG | Phase 4 | ✅ Unlocked — cross-document isolation verified |
| RAG Evaluation | Phase 4 | ✅ Unlocked — `evaluator.py` built, recall@K methodology applied (pending re-verification on current code) |
| Document-Relevance Classification | Phase 4 | ✅ Unlocked — dedicated classifier gating pattern, with known edge-case limitation |
| Multi-Agent Orchestration | Phase 5 | 📋 Planned |
| Agent Communication | Phase 5 | 📋 Planned |
| Long-Term Memory | Phase 6 | 📋 Planned |
| Autonomous Planning | Phase 6 | 📋 Planned |
| Production API Design | Phase 6 | 📋 Planned |

---

## 📚 Phase 4 Entry Checklist — Status

- [x] ChromaDB `where` clause metadata filtering — implemented and verified in `rag.py`
- [x] Ingest 2+ PDFs, query with a filename filter, verify isolation — confirmed working
- [x] Answered: minimum change to make `query_rag()` search only one file → `where={"file_name": ...}` parameter, now in place

## 🔜 Before Closing Phase 4

- [ ] Re-run `evaluator.py` against current `rag.py` once Gemini quota allows — confirm 100% recall@3 still holds post-chunking-changes
- [ ] Re-test Bug B Part 2 (Competitor Insights citation leak) against current forced-overwrite architecture — most overdue open item
- [ ] Resolve citation bug in "From Your Pitch Deck" section
- [ ] Decide: build the deterministic retry-forcing test, or formally drop it from tracking
- [ ] Centralize `classify_document_relevance()`'s prompt into `prompts.py`
- [ ] Then: hybrid search → reranking, in that order

---

<div align="center">

<sub>BizRadar AI v4.0.0 — Phase 3 Closed | Phase 4 In Progress</sub>
</div>