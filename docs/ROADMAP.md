<div align="center">

# 🧭 BizRadar AI — Roadmap

<sub>A phase-by-phase build path. Every phase ends with a concrete capability — something you can demonstrate, not just describe.</sub>

[![Phase](https://img.shields.io/badge/Current_Phase-4_Next-blue?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Phase_3-Complete-brightgreen?style=for-the-badge)]()
[![Version](https://img.shields.io/badge/Version-v3.6.0-orange?style=for-the-badge)]()
</div>

---

## 📊 Overall Progress

| Phase | Title | Status | Completion |
|---|---|---|---|
| Phase 1 | Foundation Agent | ✅ Complete | 100% |
| Phase 2 | Real Tool Integrations | ✅ Complete | 100% |
| Phase 3 | RAG & Document Intelligence | ✅ Complete | 100% |
| Phase 4 | Multi-PDF & Advanced RAG | 🔜 Next | 0% |
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

## 🔜 Phase 4 — Multi-PDF & Advanced RAG

<div align="center">
<sub><b>Outcome:</b> BizRadar ingests multiple PDFs in one session, compares them, and retrieves accurately across all documents using metadata filtering.</sub>
</div>

<br>

<details>
<summary><b>📚 Concepts To Learn</b></summary>
<br>

- [ ] Multi-document architecture — how ChromaDB handles multiple PDFs with metadata filtering
- [ ] `where` clause filtering in ChromaDB — query only a specific document by filename
- [ ] Chunking improvements — fixed token chunking vs semantic chunking vs paragraph chunking
- [ ] When simple chunking fails — tables, headers, bullet points in PDFs
- [ ] Context window management for RAG — when top-k chunks overflow LLM context
- [ ] RAG evaluation — measuring retrieval quality, precision vs recall
- [ ] Hybrid search — combining keyword search (BM25) with vector search
- [ ] Reranking — why top-k is not always the best k, cross-encoder rerankers

</details>

<details>
<summary><b>🔨 What To Build</b></summary>
<br>

| File | Purpose |
|---|---|
| `app.py` (updated) | Accept multiple PDF paths at startup |
| `rag.py` (updated) | Metadata filtering in `query_rag()` for targeted document search |
| `tools_description.py` (updated) | `search_documents` schema with optional `filename` filter |
| `evaluator.py` (new) | Basic RAG evaluation — query → chunks → relevance check |

</details>

<br>

**Architecture Target:**

```
User uploads 3 PDFs at startup
        ↓
Each ingested and stored with filename metadata
        ↓
User: "Compare revenue projections in deck_a.pdf and deck_b.pdf"
        ↓
Agent calls search_documents twice — once per file using metadata filter
        ↓
Results compared and synthesized in final response
```

> **Milestone:** User uploads three pitch decks. BizRadar retrieves from specific documents on demand and produces a structured comparison — no cross-document contamination.

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
| Multi-Document RAG | Phase 4 | 🔜 Next |
| RAG Evaluation | Phase 4 | 🔜 Next |
| Multi-Agent Orchestration | Phase 5 | 📋 Planned |
| Agent Communication | Phase 5 | 📋 Planned |
| Long-Term Memory | Phase 6 | 📋 Planned |
| Autonomous Planning | Phase 6 | 📋 Planned |
| Production API Design | Phase 6 | 📋 Planned |

---

## 📚 Study Before Phase 4

- [ ] ChromaDB `where` clause documentation — metadata filtering syntax
- [ ] Read: "Lost in the Middle" paper — why middle chunks get ignored by LLMs
- [ ] Build: ingest 2 PDFs manually, query with a filename filter, verify isolation
- [ ] Answer before starting: right now `query_rag()` searches all documents. What is the minimum change needed to make it search only one specific file?

---

<div align="center">

<sub>BizRadar AI v3.6.0 — Phase 3 Closed | Phase 4 Next</sub>
</div>
