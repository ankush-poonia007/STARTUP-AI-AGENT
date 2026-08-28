<div align="center">

# 🧭 CoFoundr AI — Roadmap

<sub>A phase-by-phase build path. Every phase ends with a concrete capability — something you can demonstrate, not just describe.</sub>

[![Phase](https://img.shields.io/badge/Current_Phase-6_Started-blue?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Phase_5-Complete-brightgreen?style=for-the-badge)]()
[![Version](https://img.shields.io/badge/Version-v5.9.0-orange?style=for-the-badge)]()

</div>

---

## 📊 Overall Progress

| Phase | Title | Status | Completion |
|---|---|---|---|
| Phase 1 | Foundation Agent | ✅ Complete | 100% |
| Phase 2 | Real Tool Integrations | ✅ Complete | 100% |
| Phase 3 | RAG & Document Intelligence | ✅ Complete | 100% |
| Phase 4 | Multi-PDF, Hybrid Search & RAG Hardening | ✅ Complete | 100% |
| Phase 5 | Multi-Agent Architecture | ✅ Complete | 100% |
| Phase 6 | Autonomous Research Platform | 🚀 Started | 0% |

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

- [x] ReAct Pattern — Reasoning + Acting loop, `tool_calls` handling
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

## ✅ Phase 4 — Multi-PDF, Hybrid Search & RAG Hardening

<div align="center">
<sub><b>Outcome:</b> BizRadar ingests multiple PDFs in one session, isolates retrieval per document, gates document access to only the turns that need it, fuses lexical + semantic retrieval, reranks for precision, and survives process restarts and API rate limits — all verified against a real evaluation suite.</sub>
</div>

<br>

Phase 4 shipped across **six focused versions** rather than one large drop. Each version isolated a single capability so it could be tested and verified independently before the next was layered on. Full technical detail lives in [`CHANGELOG.md`](CHANGELOG.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md).

<details open>
<summary><b>🗂️ The Six Sub-Releases</b></summary>
<br>

| Version | Focus | Headline Capability |
|---|---|---|
| v4.0.0 | Multi-PDF Isolation | `where={"file_name": ...}` filtering + `temp_list` context isolation + forced argument overwrite |
| v4.1.0 | Stage Gating Enforcement | `validate_stage_tools()` — real, code-enforced tool-call gatekeeping |
| v4.2.0 | Document Relevance Classifier | Dedicated Gemini call decides per-turn whether Stage 4 is even reachable |
| v4.3.0 | Chunking Rework & Evaluation | Paragraph-aware sliding-window chunker + `evaluator.py` Recall@K suite |
| v4.4.0 | Hybrid Search, Reranking & API Pool | BM25 + vector fusion, CrossEncoder reranking, multi-key Gemini failover |
| v4.5.0 | Debugging & Hardening | Every open bug resolved, deferred with a reason, or reclassified — Phase 4 formally closed |

</details>

<details open>
<summary><b>✅ Done & Verified</b></summary>
<br>

| # | Item | Verification |
|---|---|---|
| 1 | Cross-document isolation via `query_rag(where={"file_name": ...})` | 100% isolation confirmed across multiple uploaded PDFs |
| 2 | Per-turn file-list injection (`temp_list`/`length`/`extend()` pattern) | `self.messages[0]` confirmed static across turns — no permanent pollution |
| 3 | `validate_stage_tools()` real stage gating | Replaced print-only counter; caught real LLM stage-bundling violations |
| 4 | Document-relevance classifier | 95–100% accuracy per category after DS-008 / DQA-015 / DQA-024 fixes |
| 5 | Paragraph-aware fixed-token chunking | `CHUNK_SIZE=250`, `OVERLAP=50`, `STEP=200` — fixed dense-PDF under-chunking |
| 6 | `evaluator.py` — Recall@K benchmark | 100% Recall@3 on vector pipeline, 5 documents, 25 questions |
| 7 | Hybrid search (BM25 + vector fusion) | 100% Recall@3 on hybrid pipeline, `HS_ALL_QUESTIONS`, 25 lexical queries |
| 8 | CrossEncoder reranking (`BAAI/bge-reranker-v2-m3`) | Integrated into `query_rag()`, top-10 → top-3 |
| 9 | BM25 persistence across restarts | Corpus JSON + index `.save()`/`.load()` verified — survives process restart |
| 10 | Dynamic Gemini API pool with exponential cooldown | Min-wait retry confirmed correct after `current_time` staleness fix |
| 11 | Forced `function_args` overwrite (`market_context`/`mvp_context`/`startup_idea`) | Hallucinated-context bug closed — LLM cannot fabricate these three keys |
| 12 | `__main__` guard on `rag.py`'s batch re-ingestion block | Prevents silent 12-file re-ingestion on every import |
| 13 | Classifier prompt centralized to `prompts.py` | `CLASSIFICATION_PROMPT` constant — matches convention used by all other prompts |

</details>

<details>
<summary><b>📈 Final Evaluation Results</b></summary>
<br>

| Dataset | Recall@1 | Recall@3 | MRR |
|---|---|---|---|
| `ALL_QUESTIONS` (vector-only, semantic) | 88% | 100% | 0.94 |
| `HS_ALL_QUESTIONS` (hybrid, lexical) | 72% | 100% | 0.86 |

Both pipelines reach 100% Recall@3. The Recall@1 gap is attributed to corpus size (~25 total chunks across 5 documents) rather than a defect — BM25 needs a larger candidate pool to show real discrimination advantage over vector search alone. Documented, not treated as a blocker.

</details>

<details>
<summary><b>🟢 All Previously Open Bugs — Resolved</b></summary>
<br>

| # | Bug | Resolution |
|---|---|---|
| 1 | "From Your Pitch Deck" missing page/filename citations | Re-verified live against current architecture — already fixed |
| 2 | Competitor Insights citation leak (Bug B Part 2) | Re-verified live against forced-overwrite architecture — already fixed |
| 3 | Retrieval relevance / chunking drift | Logged as a future multi-turn RAG design concern, not a current implementation bug |
| 4 | Classifier ambiguous-phrasing misclassification | Documented as an irreducible prompt-only classification limitation (DS-033) |
| 5 | Groq TPD rate-limit error | Reclassified — billing/quota constraint, not an architecture defect |

</details>

<details>
<summary><b>📝 Deliberate Scope Decisions (Accepted Tradeoffs, Not Bugs)</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| Stage 2/3 context truncated to 1000 chars at injection (on top of 2000-char storage truncation) | Deferred to post-persistence work — not a current defect |
| `search_documents()`'s `file_name` argument is LLM-trusted, not validated against the live file list | Deferred until `get_available_files()` supports multi-document summary-based selection |
| `alpha=0.5` fixed fusion weight (not query-adaptive) | Simple and sufficient for current corpus size; adaptive weighting is a Phase 5+ candidate |
| Deterministic `MAX_STAGE_RETRIES` stress test | Formally dropped — inspection confirmed `temp_list` cannot grow unboundedly, the test would have validated a non-issue |

</details>

<br>

> **Verified Capability:** Multiple PDFs can be uploaded in one session with retrieval correctly isolated per document. A relevance classifier gates whether document retrieval is even reachable on a given turn. Retrieval itself is hybrid — BM25 lexical search and vector semantic search are fused and then reranked by a CrossEncoder for precision. The system persists its lexical index across restarts, survives Gemini rate limits via a multi-key pool, and every claim in this section is backed by a re-run evaluation, not just a memory of having built it.

---

## ✅ Phase 5 — Multi-Agent Architecture

<div align="center">
<sub><b>Outcome:</b> A production-oriented multi-agent workflow where specialist agents are coordinated through a shared workflow state.</sub>
</div>

<br>

Phase 5 was completed through incremental provider, orchestration, reliability, and verification work. The final release was **v5.9.0**, with the existing implementation verified rather than new functionality introduced in the closing release.

<details open>
<summary><b>📚 Concepts Covered</b></summary>
<br>

- [x] Multi-agent architecture — specialist agents with focused responsibilities
- [x] Orchestrator pattern — centralized workflow coordination
- [x] Shared workflow state — passing structured context between agents
- [x] Agent handoffs — sequential specialist execution through shared state
- [x] Provider abstraction — reusable provider tools instead of provider logic inside agents
- [x] Dynamic API-key rotation — instance-level rotation with shared key-rotation utility
- [x] Provider migration strategy — routing large-context workloads through OpenRouter
- [x] Structured outputs — provider-compatible response schemas
- [x] Workflow error propagation — failed agents remain visible to downstream consumers
- [x] Focused integration testing — intent-level workflow verification

</details>

<details>
<summary><b>🔨 What Was Built</b></summary>
<br>

| Component | Purpose |
|---|---|
| `orchestrator_agent.py` | Coordinates specialist-agent execution and workflow state |
| Specialist agent modules | Market, MVP, technology, recommendation, scoring, and judging responsibilities |
| `workflow_state` | Shared state carrying inputs, outputs, errors, and pipeline status |
| `key_rotator.py` | Generic provider-independent API-key rotation logic |
| `gemini_tool.py` | Gemini provider integration with reusable tool-instance behavior |
| `groq_tool.py` | Groq provider integration retained for supported workloads |
| `tavily_tool.py` | Web-search integration used by research agents |
| `decorators.py` | Centralized workflow error capture and failure-state recording |
| Focused test runner | Validates expected intent, actual intent, and recorded workflow errors |

</details>

<details>
<summary><b>⚖️ Key Decisions</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| Specialist agents over one monolithic agent | Each workflow responsibility needs narrower context and clearer ownership |
| `orchestrator_agent.py` as the orchestration entry point | Keeps orchestration logic separate from legacy RAG/tool modules |
| Shared `workflow_state` | Provides a consistent contract for agent handoffs and downstream reporting |
| Generic `key_rotator.py` | Prevents duplicated credential-rotation logic across providers |
| OpenRouter for large-context reasoning | Groq context limits became restrictive for some agent inputs |
| Gemini retained for supported analysis workloads | Preserves an existing provider path where it remains appropriate |
| Error capture through shared workflow state | Prevents failed agents from appearing successful through default state values |
| Verification before Phase 5 closure | Release readiness requires complete intent coverage and zero recorded errors |

</details>

<details open>
<summary><b>🗂️ Phase 5 Release Progression</b></summary>
<br>

| Version | Focus | Status |
|---|---|---|
| v5.0.0–v5.6.0 | Specialist-agent and multi-agent workflow construction | ✅ Complete |
| v5.7.0 | LLM judging and structured workflow validation | ✅ Complete |
| v5.8.0 | Provider migration, Gemini integration, API-key rotation, reliability changes | ✅ Complete |
| v5.9.0 | Final verification, documentation consolidation, Phase 5 closure | ✅ Complete |

</details>

<details open>
<summary><b>✅ Final Verification</b></summary>
<br>

| Verification | Result |
|---|---|
| `general_chat` | ✅ PASS |
| `full_analysis` | ✅ PASS |
| `partial_idea` | ✅ PASS |
| `idea_exploration` | ✅ PASS |
| `nurturing` | ✅ PASS |
| `advancement` | ✅ PASS |
| `pdf_request` | ✅ PASS |
| Intent workflows | **7/7 PASS** |
| Final `full_analysis` | **PASS — 0 errors** |

</details>

<details>
<summary><b>🧠 Phase 5 Engineering Lessons</b></summary>
<br>

- Provider selection must follow workload requirements, especially context-window requirements.
- Provider-specific recovery logic should live below the agent layer.
- Error handling must preserve failures inside shared state.
- Expected intent alone cannot establish workflow success.
- Final verification should measure both routing correctness and workflow health.
- Slow successful execution is a performance concern, not automatically a release blocker.

</details>

<br>

> **Milestone:** CoFoundr AI coordinates specialist agents through a shared workflow, supports multiple model providers, preserves workflow failures, and passes all seven focused intent tests.

---

## 🚀 Phase 6 — Autonomous Research Platform

<div align="center">
<sub><b>Outcome:</b> Single input. Autonomous research. Scored, cited, structured report — with planning, memory, and service-ready execution.</sub>
</div>

<br>

Phase 6 has **started**. The focus now shifts from completing the multi-agent foundation to making the workflow increasingly autonomous, persistent, observable, and service-ready.

<details open>
<summary><b>📚 Concepts To Learn</b></summary>
<br>

- [ ] Long-term memory — persistent storage beyond the context window
- [ ] Dynamic planning — automatic decomposition of goals into subtasks
- [ ] Startup scoring — formal 0–100 evaluation rubric
- [ ] Async execution — `async/await` and event-loop based concurrency
- [ ] Streaming responses — incremental output for better UX
- [ ] REST API layer — FastAPI service around the agent
- [ ] Rate limiting and retry logic — exponential backoff and circuit-breaker patterns
- [ ] Observability — structured logs, execution traces, latency, and failure metrics

</details>

<details open>
<summary><b>🎯 Phase 6 Starting Priorities</b></summary>
<br>

| Priority | Objective | Initial Deliverable |
|---|---|---|
| 1 | Persistent memory | Define storage contract and SQLite-backed memory layer |
| 2 | Autonomous planning | Define goal → subtasks → execution workflow |
| 3 | Startup scoring | Formalize scoring dimensions and aggregation rules |
| 4 | Execution modernization | Evaluate async execution against current concurrency model |
| 5 | Streaming UX | Define event/output contract before implementation |
| 6 | Service layer | Design FastAPI boundary around the agent workflow |
| 7 | Reliability | Standardize retries, timeouts, and circuit-breaker behavior |
| 8 | Observability | Capture per-agent latency, errors, retries, and final status |

</details>

<details>
<summary><b>🔨 Planned Components</b></summary>
<br>

| Component | Purpose |
|---|---|
| `memory_store.py` | Persistent long-term memory with SQLite |
| `planner.py` | Goal decomposition into executable subtasks |
| `scorer.py` | Startup viability scoring with a defined rubric |
| `api.py` | FastAPI endpoints exposing the workflow as a service |
| Observability layer | Execution traces, latency, retries, and failures |

</details>

<details>
<summary><b>⚖️ Phase 6 Design Principles</b></summary>
<br>

| Principle | Reasoning |
|---|---|
| Build on Phase 5 orchestration | Avoid replacing a verified coordination layer unnecessarily |
| Plan before executing | Autonomous systems need explicit task decomposition |
| Persist only useful state | Long-term memory should improve future execution, not duplicate context |
| Measure before optimizing | Phase 5 established correctness; Phase 6 must quantify performance |
| Keep provider concerns isolated | New autonomy features should remain provider-independent |
| Make failures observable | Autonomous workflows require stronger operational visibility |

</details>

<br>

> **Milestone:** CoFoundr AI accepts one startup idea and autonomously plans, researches, scores, and assembles a cited report without requiring manual workflow decisions.

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
| Stage-Gated Tool Orchestration | Phase 4 | ✅ Unlocked — real enforcement, not label-only |
| LLM-Based Relevance Classification | Phase 4 | ✅ Unlocked — with a documented, known edge case |
| Hybrid Retrieval (BM25 + Vector Fusion) | Phase 4 | ✅ Unlocked — 100% Recall@3 verified |
| CrossEncoder Reranking | Phase 4 | ✅ Unlocked — precision layer on fused candidates |
| RAG Evaluation Methodology (Recall@K, MRR) | Phase 4 | ✅ Unlocked — dual benchmark suite (semantic + lexical) |
| Multi-Key API Failover & Rate-Limit Handling | Phase 4 | ✅ Unlocked — exponential cooldown, min-wait retry |
| Multi-Agent Orchestration | Phase 5 | ✅ Unlocked — verified in Phase 5 |
| Agent Communication & Handoffs | Phase 5 | ✅ Unlocked — shared workflow verified |
| Long-Term Memory | Phase 6 | 🚀 Started |
| Autonomous Planning | Phase 6 | 🚀 Started |
| Production API Design | Phase 6 | 🚀 Started |

---

## 📚 Phase 5 Closure Checklist — Final Status

- [x] Multi-agent orchestration — specialist-agent workflow implemented and verified
- [x] Shared workflow state — agent handoffs and downstream state propagation verified
- [x] Intent-based workflow routing — all seven focused workflows verified
- [x] Provider abstraction — provider-specific integrations separated from agent logic
- [x] OpenRouter migration — large-context workloads migrated from Groq due to input-context limitations
- [x] Gemini integration — Gemini provider tooling retained and stabilized for supported workloads
- [x] Dynamic API-key rotation — reusable instance-level key rotation implemented
- [x] Workflow error handling — failed agents recorded in `workflow_state.errors` and `pipeline_status`
- [x] Structured response formats — judge, recommendation, and startup-score contracts implemented
- [x] Intermediate LLM judging — PASS / WARNING / FAIL validation implemented
- [x] Final report judging — final report validation implemented
- [x] Provider integration verification — transient provider failures handled during final testing
- [x] Focused intent testing — `general_chat`, `full_analysis`, `partial_idea`, `idea_exploration`, `nurturing`, `advancement`, and `pdf_request` verified
- [x] Final `full_analysis` verification — expected intent matched actual intent with `Errors: 0`
- [x] Phase 5 documentation — changelog, learning log, roadmap, architecture, and engineering audit consolidated

**Phase 5 is closed. All seven focused intent workflows passed, including the final full-analysis verification with zero workflow errors.**

> **Release status:** v5.9.0 — Phase 5 Complete. No known functional blocker remains for Phase 6.

---

## 🔜 Starting Phase 6

- [x] Phase 5 closed at v5.9.0 with 7/7 focused intent workflows passing
- [x] Final `full_analysis` verified with 0 workflow errors
- [ ] Define the Phase 6 persistent-memory contract
- [ ] Design autonomous goal decomposition and planning state
- [ ] Define startup scoring dimensions and aggregation
- [ ] Establish Phase 6 observability and performance baseline
- [ ] Evaluate async execution against the current Phase 5 workflow
- [ ] Design the FastAPI service boundary


<div align="center">

<sub>CoFoundr AI v5.9.0 — Phase 5 Closed | Phase 6 Started</sub>

</div>