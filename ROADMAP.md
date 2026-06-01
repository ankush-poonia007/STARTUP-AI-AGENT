# 🧭 BizRadar AI — Detailed Roadmap

> A phase-by-phase learning and build path covering every concept, technology, and milestone required to evolve BizRadar from a CLI agent to an autonomous research platform.

---

## 📊 Overall Progress

| Phase | Title | Status | Completion |
|---|---|---|---|
| Phase 1 | Foundation Agent | ✅ Complete | 100% |
| Phase 2 | Real Tool Integrations | ✅ Complete | 100% |
| Phase 3 | RAG & Document Intelligence | 🔄 Next | 0% |
| Phase 4 | Multi-Agent Architecture | 📋 Planned | 0% |
| Phase 5 | Autonomous Research Platform | 📋 Planned | 0% |

---

## ✅ Phase 1 — Foundation Agent
> **Goal:** Build a working local AI agent from scratch without frameworks.

### Concepts Covered
- [ ] What is an AI Agent — definitions, components, responsibilities
- [ ] Prompt Engineering — system prompts, output formatting, constraints
- [ ] Context Window Management — what fits, what gets cut, sliding window
- [ ] Tool Architecture — what tools are, why agents need them
- [ ] OOP Design for AI — classes, separation of concerns, modularity
- [ ] Local LLM Deployment — Ollama, model pulling, inference parameters
- [ ] HTTP API Communication — requests library, POST payloads, error handling
- [ ] Environment Variables — `.env`, `python-dotenv`, secret management

### What Was Built
- `agent.py` — Core agent class with manual tool execution
- `app.py` — CLI loop
- `context_manager.py` — Sliding window memory (last 6 turns)
- `tools.py` — Placeholder tools (market, MVP, tech stack, risk)
- `prompts.py` — System prompt with structured output format

### Key Decisions Made
- No LangChain or LlamaIndex — architecture first
- Ollama for local inference — privacy + zero API cost
- Manual tool execution — understand the pattern before automating it

---

## ✅ Phase 2 — Real Tool Integrations
> **Goal:** Replace simulated tools with real APIs and implement the ReAct pattern with parallel execution.

### Concepts Covered
- [ ] ReAct Pattern — Reasoning + Acting loop, tool_calls handling
- [ ] Groq API — LPU inference, API authentication, model selection
- [ ] Tool Calling / Function Calling — tool schemas, JSON definitions, required fields
- [ ] Tool Schema Design — how descriptions affect LLM tool selection accuracy
- [ ] Parallel Execution — `ThreadPoolExecutor`, `as_completed`, `executor.submit`
- [ ] Fan-Out Fan-In Pattern — dispatching multiple tasks, collecting results
- [ ] `as_completed` vs `executor.map` — when to use each
- [ ] Tavily Search API — query parameters, `include_answer`, `exclude_domains`
- [ ] Gemini API — `google.genai`, prompt templates, `generate_content`
- [ ] Error Handling — provider-specific exceptions (Groq, Gemini, Tavily)
- [ ] Multi-Provider Architecture — mixing LLM providers in one system

### What Was Built
- `agent.py` — ReAct loop with `while True`, tool_calls detection, parallel execution
- `tools.py` — Live Tavily search + Gemini-powered analysis tools
- `tools_description.py` — JSON tool schemas for LLM tool-calling interface

### Key Decisions Made
- Groq over Ollama — LPU speed + free tier for development
- Gemini 2.5 Flash for analysis tools — cost-effective, fast, high quality
- Parallel tool execution — reduce latency from sequential to simultaneous
- Tool schemas in separate file — clean separation of concerns

---

## 🔄 Phase 3 — RAG & Document Intelligence
> **Goal:** Give BizRadar the ability to read, understand, and reason over documents.

### Concepts To Learn
- [ ] What is RAG — Retrieval Augmented Generation, why it reduces hallucination
- [ ] Vector Embeddings — what they are, how text becomes numbers
- [ ] Embedding Models — `text-embedding-004` (Gemini), `nomic-embed-text` (Ollama)
- [ ] Vector Databases — ChromaDB (local), Pinecone (cloud), pgvector (Postgres)
- [ ] Chunking Strategies — fixed size, recursive, semantic chunking
- [ ] Similarity Search — cosine similarity, dot product, approximate nearest neighbor
- [ ] Document Loaders — PDF parsing, web scraping, markdown reading
- [ ] Retrieval Pipeline — embed query → search index → retrieve top-k → inject into prompt
- [ ] Reranking — why top-k is not always the best k, cross-encoder rerankers
- [ ] Hybrid Search — combining keyword search (BM25) with vector search

### What To Build
- `document_loader.py` — PDF, markdown, web page ingestion
- `embedder.py` — Text → vector conversion
- `vector_store.py` — ChromaDB integration, upsert, query
- `retriever.py` — Query → relevant chunks pipeline
- Updated `tools.py` — `search_knowledge_base()` replaced with real RAG retrieval

### Milestone
> BizRadar can ingest a startup pitch deck PDF and answer questions from its content.

---

## 📋 Phase 4 — Multi-Agent Architecture
> **Goal:** Replace single agent with specialized agents coordinated by an orchestrator.

### Concepts To Learn
- [ ] Multi-Agent Systems — why one agent cannot do everything well
- [ ] Orchestrator Pattern — coordinator agent that delegates to specialists
- [ ] Agent Communication — how agents pass context and results between each other
- [ ] Specialized Agent Design — narrow scope, deep focus per agent
- [ ] Shared Memory — agents reading from and writing to a common state store
- [ ] Agent Handoffs — when and how an orchestrator decides to delegate
- [ ] Inter-Agent Prompt Design — prompting one agent to call another
- [ ] Failure Handling — what happens when a sub-agent fails or times out

### Agents To Build
- `orchestrator_agent.py` — Receives user input, delegates to specialists
- `market_research_agent.py` — Deep market and competitor analysis
- `competitor_analyst_agent.py` — Competitor discovery and differentiation
- `tech_advisor_agent.py` — Architecture and stack recommendations
- `report_writer_agent.py` — Compiles all agent outputs into final report

### Architecture Target
```
User
 ↓
Orchestrator Agent
 ├──→ Market Research Agent
 ├──→ Competitor Analyst Agent
 ├──→ Tech Advisor Agent
 └──→ Report Writer Agent
         ↓
   Final Structured Report
```

### Milestone
> BizRadar produces a 5-section report where each section is written by a specialized agent.

---

## 📋 Phase 5 — Autonomous Research Platform
> **Goal:** BizRadar can plan, research, and produce reports without step-by-step user guidance.

### Concepts To Learn
- [ ] Long-Term Memory — persistent storage beyond context window (SQLite, Redis)
- [ ] Memory Types — episodic (events), semantic (facts), procedural (how-to)
- [ ] Dynamic Planning — agent breaks down a goal into subtasks automatically
- [ ] Task Queues — Celery, RQ, or simple asyncio queues for async workflows
- [ ] Startup Scoring — building a scoring rubric and evaluation framework
- [ ] Autonomous Pipelines — trigger → plan → execute → store → report
- [ ] Asyncio — `async/await`, event loops, replacing ThreadPoolExecutor
- [ ] Streaming Responses — token-by-token output for better UX
- [ ] REST API Layer — FastAPI wrapper around the agent for web/mobile access
- [ ] Rate Limiting & Retry Logic — exponential backoff, circuit breaker pattern

### What To Build
- `memory_store.py` — Persistent long-term memory with SQLite
- `planner.py` — Goal decomposition into subtask list
- `scorer.py` — Startup viability scoring (0-100) with rubric
- `api.py` — FastAPI endpoints exposing agent as a service
- `pipeline.py` — Autonomous end-to-end research workflow

### Milestone
> User types a startup idea once. BizRadar autonomously researches, scores, and delivers a full report with no follow-up prompts.

---

## 📚 Recommended Study Order

### Before Phase 3
- [ ] Read: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al.)
- [ ] Build: A basic ChromaDB demo — embed 10 sentences, query top-3
- [ ] Watch: Any hands-on ChromaDB + LangChain tutorial (to understand RAG, not to use the framework)

### Before Phase 4
- [ ] Read: "A Survey on Large Language Model based Autonomous Agents" (Wang et al.)
- [ ] Study: AutoGPT and BabyAGI source code — understand orchestrator patterns
- [ ] Build: A 2-agent system — one agent calls another via a shared message queue

### Before Phase 5
- [ ] Learn: FastAPI fundamentals — routes, Pydantic models, async endpoints
- [ ] Learn: asyncio fundamentals — event loops, coroutines, `gather()`
- [ ] Study: Redis basics — key-value store, TTL, pub/sub for agent communication

---

## 🎯 Skills Unlocked Per Phase

| Skill | Phase Unlocked |
|----|----|
| Prompt Engineering | Phase 1 |
| Context Management | Phase 1 |
| Local LLM Deployment | Phase 1 |
| ReAct Agent Pattern | Phase 2 |
| Tool Calling / Function Calling | Phase 2 |
| Parallel Execution | Phase 2 |
| Multi-Provider LLM Integration | Phase 2 |
| RAG Pipelines | Phase 3 |
| Vector Search | Phase 3 |
| Document Intelligence | Phase 3 |
| Multi-Agent Orchestration | Phase 4 |
| Agent Communication | Phase 4 |
| Long-Term Memory | Phase 5 |
| Autonomous Planning | Phase 5 |
| Production API Design | Phase 5 |

---

*Last Updated: BizRadar AI v2.0 — Phase 2 Complete*