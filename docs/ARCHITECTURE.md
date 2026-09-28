<div align="center">

# 🏗️ CoFoundr AI — Architecture Deep Dive

### From manual agent loops to a validated multi-agent startup intelligence platform

[![Version](https://img.shields.io/badge/Version-v5.9.0-orange?style=for-the-badge)]()
[![Phase 1](https://img.shields.io/badge/Phase_1-Complete-brightgreen?style=for-the-badge)]()
[![Phase 2](https://img.shields.io/badge/Phase_2-Complete-brightgreen?style=for-the-badge)]()
[![Phase 3](https://img.shields.io/badge/Phase_3-Complete-brightgreen?style=for-the-badge)]()
[![Phase 4](https://img.shields.io/badge/Phase_4-Complete-brightgreen?style=for-the-badge)]()
[![Phase 5](https://img.shields.io/badge/Phase_5-Complete-brightgreen?style=for-the-badge)]()
[![Phase 6](https://img.shields.io/badge/Phase_6-Started-blue?style=for-the-badge)]()

<br>

**Framework-independent • Multi-agent • Hybrid RAG • Structured validation • Provider resilient**

</div>

---

## 🧭 Architecture at a Glance

CoFoundr AI analyzes startup ideas through specialized agents, shared workflow state, grounded retrieval, live research, and validation.

```mermaid
flowchart TD
    U["👤 User"] --> R["🎯 Intent Router"]
    R --> O["🧠 Orchestrator"]
    O --> P["📋 Execution Plan"]

    P --> W["🌐 Web Search"]
    P --> M["📊 Market Research"]
    P --> V["🧪 MVP Advisor"]
    P --> T["⚙️ Tech Advisor"]
    P --> K["⚠️ Risk Analyst"]
    P --> S["📈 Startup Scorer"]
    P --> RC["💡 Recommendation"]
    P --> G["💬 General / Idea / Nurturing / Advancement"]

    W --> ST["🗂️ Shared Workflow State"]
    M --> ST
    V --> ST
    T --> ST
    K --> ST
    S --> ST
    RC --> ST
    G --> ST

    ST --> J["🔍 LLM Judge"]
    J --> RW["📝 Report Writer"]
    RW --> FJ["⚖️ Final Judge"]
    FJ --> PDF["📄 PDF Generator"]
    PDF --> OUT["🚀 Final Output"]
```

> **Core principle:** agents reason independently; workflow state connects them; validators protect the final output.

---

## 📚 Table of Contents

- [Design Philosophy](#-design-philosophy)
- [Architecture Evolution](#-architecture-evolution)
- [Current Component Map](#-current-component-map)
- [Orchestration Architecture](#-orchestration-architecture)
- [Intent Routing](#-intent-routing)
- [Specialist Agents](#-specialist-agent-layer)
- [Shared Workflow State](#-shared-workflow-state)
- [Provider Architecture](#-provider-architecture)
- [Reliability and Key Rotation](#-reliability-and-key-rotation)
- [Validation and Structured Outputs](#-validation-and-structured-outputs)
- [RAG Architecture](#-rag-architecture)
- [Evaluation](#-evaluation)
- [Phase 5 Verification](#-phase-5-verification)
- [Design Tradeoffs](#-design-tradeoffs)
- [Known Limitations](#-known-limitations)
- [Phase 6 Direction](#-phase-6-direction)

---

## 🎯 Design Philosophy

<div align="center">

> **Architecture First. Frameworks Later.**

</div>

CoFoundr AI deliberately implements important agentic primitives directly instead of hiding them behind an orchestration framework.

The project uses this approach to understand:

- Agent orchestration internals.
- Tool execution boundaries.
- Context and state management.
- Retrieval pipelines.
- Provider abstraction.
- Failure propagation.
- Structured output contracts.
- Evaluation and verification.

### Architectural boundaries

| Layer | Owns | Does not own |
|---|---|---|
| **Agents** | Reasoning and domain decisions | Provider SDK details |
| **Tools** | External integrations | Workflow planning |
| **Core** | Orchestration, state, errors | Domain reasoning |
| **RAG** | Retrieval and reranking | Final report generation |
| **Evaluation** | Ground truth and verification | Production orchestration |
| **Prompts** | Behavioral instructions | Runtime state |

---

# 🧬 Architecture Evolution

CoFoundr AI evolved incrementally rather than jumping directly into the current architecture.

```mermaid
timeline
    title CoFoundr AI Architecture Evolution
    Phase 1 : Foundation
            : CLI application
            : Basic agent loop
    Phase 2 : Agentic Execution
            : Tool calling
            : ReAct execution
            : Stage gating
    Phase 3 : RAG
            : PDF ingestion
            : ChromaDB
            : Semantic retrieval
    Phase 4 : RAG Hardening
            : BM25 hybrid retrieval
            : Score fusion
            : CrossEncoder reranking
            : Document relevance gating
    Phase 5 : Multi-Agent System
            : Intent routing
            : Specialized agents
            : Shared workflow state
            : Provider abstraction
            : Structured validation
            : Verification
    Phase 6 : Autonomous Platform
            : Persistent memory
            : Planning
            : API layer
            : Async execution
            : Observability
```

### Current milestone

| Phase | Status | Architectural role |
|---|---|---|
| Phase 1 | ✅ Complete | Foundation |
| Phase 2 | ✅ Complete | Agentic execution |
| Phase 3 | ✅ Complete | Document intelligence |
| Phase 4 | ✅ Complete | Retrieval hardening |
| Phase 5 | ✅ Complete | Multi-agent orchestration |
| Phase 6 | 🚀 Started | Autonomous platform evolution |

---

# 📁 Current Component Map

```text
CoFoundr AI
│
├── app.py
│   └── CLI interface + pipeline execution + testing
│
├── src/
│   │
│   ├── agents/
│   │   ├── intent_router_agent.py
│   │   ├── orchestrator_agent.py
│   │   ├── web_search_agent.py
│   │   ├── market_research_agent.py
│   │   ├── rag_agent.py
│   │   ├── mvp_advisor_agent.py
│   │   ├── tech_advisor_agent.py
│   │   ├── risk_analyst_agent.py
│   │   ├── startup_scorer_agent.py
│   │   ├── recommendation_agent.py
│   │   ├── llm_judge_agent.py
│   │   ├── report_writer_agent.py
│   │   ├── pdf_generator_agent.py
│   │   ├── general_chat_agent.py
│   │   ├── idea_generation_agent.py
│   │   ├── nurturing_agent.py
│   │   ├── advancement_agent.py
│   │   └── workflow_state.py
│   │
│   ├── core/
│   │   ├── orchestrator.py
│   │   ├── context_manager.py
│   │   ├── decorators.py
│   │   ├── exceptions.py
│   │   └── key_rotator.py
│   │
│   ├── tools/
│   │   ├── openrouter/provider integrations
│   │   ├── gemini_tool.py
│   │   ├── groq_tool.py
│   │   ├── tavily_tool.py
│   │   ├── chroma_tool.py
│   │   ├── bm25_tool.py
│   │   ├── reranker_tool.py
│   │   └── pdf_tool.py
│   │
│   ├── rag/
│   │   ├── rag.py
│   │   └── reranker.py
│   │
│   ├── evaluation/
│   │   ├── evaluator.py
│   │   ├── ground_truth.py
│   │   ├── classifier_evaluator.py
│   │   ├── classifier_ground_truth.py
│   │   └── datasets/
│   │
│   ├── prompts/
│   ├── config/
│   ├── memory/        ← Phase 6 expansion
│   └── planning/      ← Phase 6 expansion
│
├── data/
│   ├── uploads/
│   ├── chroma_db/
│   ├── BM25/
│   └── outputs/
│
└── docs/
    ├── ARCHITECTURE.md
    ├── CHANGELOG.md
    ├── LEARNING_LOG.md
    └── ROADMAP.md
```

---

# 🧠 Orchestration Architecture

The current system no longer depends on one monolithic agent performing every startup-analysis task.

```mermaid
flowchart LR
    Q["User Query"] --> IR["Intent Router"]
    IR --> EP["Execution Plan"]
    EP --> OA["Orchestrator"]

    OA --> A1["Research Agents"]
    OA --> A2["Analysis Agents"]
    OA --> A3["Document Agents"]
    OA --> A4["Decision Agents"]

    A1 --> WS["Workflow State"]
    A2 --> WS
    A3 --> WS
    A4 --> WS

    WS --> QA["Quality / Judge Layer"]
    QA --> REPORT["Report Pipeline"]
```

### Orchestrator responsibilities

The orchestrator coordinates execution rather than owning every domain decision.

It handles:

- Execution-plan coordination.
- Agent invocation.
- Workflow-state propagation.
- Failure visibility.
- Retry boundaries.
- Downstream dependency handling.
- Final pipeline coordination.

### Why specialization?

A single agent performing market research, RAG, scoring, recommendations, and report writing creates:

- Large prompts.
- Mixed responsibilities.
- Poor failure isolation.
- Harder testing.
- Weak observability.
- Difficult provider optimization.

Specialized agents make each responsibility independently testable.

---

# 🎯 Intent Routing

```mermaid
flowchart TD
    Q["Raw User Query"] --> C["Intent Classification"]
    C --> I1["full_analysis"]
    C --> I2["partial_idea"]
    C --> I3["idea_exploration"]
    C --> I4["general_chat"]
    C --> I5["nurturing"]
    C --> I6["advancement"]
    C --> I7["pdf_request"]

    I1 --> PLAN["Execution Plan"]
    I2 --> PLAN
    I3 --> PLAN
    I4 --> PLAN
    I5 --> PLAN
    I6 --> PLAN
    I7 --> PLAN

    PLAN --> ORCH["Orchestrator"]
```

The router separates **what the user wants** from **how that request is executed**.

This prevents every request from triggering the full startup-analysis pipeline.

---

# 🤖 Specialist Agent Layer

| Agent | Primary responsibility |
|---|---|
| `WebSearchAgent` | Live external research |
| `MarketResearchAgent` | Market-focused analysis |
| `RAGAgent` | Uploaded-document retrieval |
| `MVPAdvisorAgent` | MVP definition and prioritization |
| `TechAdvisorAgent` | Technology-stack analysis |
| `RiskAnalystAgent` | Risk identification and analysis |
| `StartupScorerAgent` | Startup scoring |
| `RecommendationAgent` | Evidence-linked recommendations |
| `LLMJudgeAgent` | Intermediate quality validation |
| `ReportWriterAgent` | Final report composition |
| `PDFGeneratorAgent` | Report artifact generation |
| `GeneralChatAgent` | General conversational requests |
| `IdeaGenerationAgent` | Startup idea exploration |
| `NurturingAgent` | Follow-up and development flow |
| `AdvancementAgent` | Advancement-oriented workflows |

### Specialist-agent contract

```text
Input
  ↓
Agent-specific reasoning
  ↓
Structured / normalized output
  ↓
Workflow State
  ↓
Downstream consumer
```

The contract keeps agent implementations replaceable.

---

# 🗂️ Shared Workflow State

The workflow state is the main communication boundary between agents.

```mermaid
flowchart TD
    A["Intent"] --> S["Workflow State"]
    B["Execution Plan"] --> S
    C["Research"] --> S
    D["RAG Results"] --> S
    E["Specialist Analysis"] --> S
    S --> F["Judgment"]
    S --> G["Report"]
    S --> H["Errors"]
    S --> I["Pipeline Status"]
```

Conceptually, the state contains:

```text
workflow_state
├── user_query
├── intent
├── execution_plan
├── stage / agent outputs
├── validation results
├── errors
├── pipeline_status
└── final report data
```

### Why shared state?

It avoids direct coupling such as:

```text
Agent A → imports Agent B → calls Agent B
```

Instead:

```text
Agent A
   ↓
Workflow State
   ↓
Agent B
```

This makes dependencies explicit and easier to inspect.

---

# 🌐 Provider Architecture

Provider access is isolated behind tool-level integrations.

```mermaid
flowchart TD
    AG["Agents"] --> PT["Provider Tool Layer"]

    PT --> OR["OpenRouter"]
    PT --> GE["Gemini"]
    PT --> GR["Groq"]
    PT --> TV["Tavily"]

    OR --> LLM["Large-context / reasoning workloads"]
    GE --> EMB["Embeddings / Gemini workloads"]
    GR --> RET["Retained Groq workloads"]
    TV --> WEB["Live web research"]
```

## Why OpenRouter?

The migration from Groq was driven by **input-context limitations**.

Phase 5 increased the amount of workflow information passed into later agent calls.

```text
Before
User input
  ↓
Small agent context
  ↓
Groq

After
User input
  ↓
Multi-agent outputs
  ↓
Shared workflow state
  ↓
Larger downstream context
  ↓
OpenRouter
```

The important architectural change was therefore not simply changing an API endpoint.

It was separating **agent logic from model-provider constraints**.

### Provider abstraction principle

```text
Agent
  │
  └──> Provider Tool
          │
          ├──> Provider A
          ├──> Provider B
          └──> Provider C
```

Agents should not need to know provider-specific SDK details.

---

# 🔄 Reliability and Key Rotation

Phase 5 introduced reusable provider key-rotation infrastructure.

```mermaid
flowchart LR
    CALL["Provider Request"] --> RETRY["Retry Boundary"]
    RETRY --> ROT["Key Rotator"]
    ROT --> K1["Key 1"]
    ROT --> K2["Key 2"]
    ROT --> K3["Key N"]

    K1 --> OK{"Success?"}
    K2 --> OK
    K3 --> OK

    OK -->|Yes| OUT["Return"]
    OK -->|No| ERR["Record Failure"]
```

`src/core/key_rotator.py` centralizes rotation behavior.

This avoids duplicating key-selection logic across provider tools.

### Failure visibility

```mermaid
flowchart TD
    X["Agent Exception"] --> D["handle_errors"]
    D --> E["workflow_state.errors"]
    D --> P["pipeline_status[agent] = failed"]
    E --> DOWN["Downstream visibility"]
    P --> DOWN
```

A failed agent should remain visible as failed.

It should not silently look like an agent that produced no output.

---

# 🧾 Validation and Structured Outputs

Phase 5 introduced stronger output contracts.

```mermaid
flowchart TD
    A["Agent Output"] --> S["Schema Validation"]
    S -->|Valid| J["Judge"]
    S -->|Invalid| E["Error / Retry"]
    J --> R["Report Writer"]
    R --> F["Final Judge"]
```

Structured response formats are used for important contracts, including:

- Recommendations.
- Intermediate judgments.
- Final judgments.
- Startup scoring.

### Example scoring contract

```text
reasoning
breakdown
├── market
├── mvp
├── tech
└── risk
highest_risk_flag
```

Scores are constrained to the expected numeric range.

Judgment outputs use:

```text
PASS
WARNING
FAIL
```

This makes downstream processing deterministic.

---

# 🔎 RAG Architecture

RAG remains one of CoFoundr AI's core architectural subsystems.

```mermaid
flowchart TD
    PDF["📄 PDF"] --> EX["PDF Extraction"]
    EX --> CH["Paragraph-aware Chunking"]
    CH --> EMB["Gemini Embeddings"]
    EMB --> VDB["ChromaDB"]

    CH --> BM["BM25 Index"]

    Q["User Query"] --> VR["Vector Retrieval"]
    Q --> BR["BM25 Retrieval"]

    VDB --> VR
    BM --> BR

    VR --> FU["Score Fusion"]
    BR --> FU
    FU --> CE["CrossEncoder"]
    CE --> TOP["Top-K Context"]
    TOP --> AG["RAG Agent"]
```

## Retrieval stages

### 1. Ingestion

```text
PDF
 ↓
pdfplumber
 ↓
paragraph-aware chunks
 ↓
Gemini embeddings
 ↓
ChromaDB
```

Current chunking uses:

```text
CHUNK_SIZE = 250
OVERLAP    = 50
STEP       = 200
```

Large paragraphs use sliding windows.

Smaller paragraphs remain intact.

---

### 2. Hybrid retrieval

```text
User Query
├── Vector Search → ChromaDB
└── Lexical Search → BM25
          ↓
       Fusion
```

Current retrieval uses a balanced fusion concept:

```text
fusion_score =
    0.5 × vector_similarity
  + 0.5 × normalized_BM25
```

The approach combines:

- Semantic similarity.
- Exact lexical matching.

---

### 3. CrossEncoder reranking

```text
Fused top-10
    ↓
BAAI/bge-reranker-v2-m3
    ↓
Top-3
```

The CrossEncoder improves ranking precision without running over the entire document collection.

---

## 📄 Document relevance gating

Uploaded documents are not automatically searched for every request.

```mermaid
flowchart TD
    Q["User Query"] --> C["Document Relevance Classifier"]
    C -->|Relevant| F["Available Files"]
    C -->|Not Relevant| SKIP["Skip Document Retrieval"]
    F --> R["RAG Retrieval"]
```

This prevents irrelevant document retrieval and unnecessary model calls.

---

# 🧪 Evaluation

The project separates system evaluation from production execution.

```text
Evaluation
├── Classifier evaluation
├── Ground-truth datasets
├── RAG evaluation
├── Document QA
├── Document search
├── Startup analysis
├── MVP
├── Tech stack
├── Ambiguous queries
├── Adversarial inputs
└── General knowledge
```

The evaluation layer provides repeatable datasets rather than relying only on manual testing.

---

# ✅ Phase 5 Verification

Phase 5 ended with focused workflow verification.

The final full-analysis test reached:

```text
Expected : full_analysis
Actual   : full_analysis
Result   : ✅ PASS
Errors   : 0
```

The seven primary intent workflows were verified as part of the Phase 5 testing process.

```text
Intent classification
        ↓
Expected intent
        ↓
Actual intent
        ↓
Error count
```

### Important performance observation

The full-analysis workflow was observed taking approximately **15 minutes** during testing.

This is classified as a **performance optimization target**, not a functional correctness failure.

Likely contributors include:

- Multiple provider calls.
- External web-search latency.
- Retry boundaries.
- Specialist-agent execution.
- Validation calls.
- Large downstream contexts.

Phase 6 should therefore focus on execution efficiency.

---

# ⚖️ Design Tradeoffs

| Decision | Benefit | Tradeoff |
|---|---|---|
| Framework-independent architecture | Deep control and learning | More implementation work |
| Specialized agents | Better separation of concerns | More orchestration complexity |
| Shared workflow state | Explicit handoffs | State schema becomes important |
| OpenRouter | Larger-context provider access | Additional provider dependency |
| Gemini | Embeddings and selected model workloads | API/quota dependency |
| Groq | Fast retained workloads | Context limitations |
| Provider abstraction | Easier provider replacement | Extra integration layer |
| Key rotation | Reduces single-key bottlenecks | Pool-management complexity |
| ThreadPoolExecutor | Parallel sync workloads | Not fully asynchronous |
| In-memory context | Simple and fast | Lost after process exit |
| Hybrid RAG | Semantic + lexical recall | Additional indexing complexity |
| CrossEncoder | Better ranking precision | Adds inference latency |
| Top-10 → Top-3 | Balances recall and context size | Some answers may need more chunks |
| Document classifier | Avoids unnecessary retrieval | Classifier can misclassify ambiguous requests |

---

# ⚠️ Known Limitations

### Phase 5 limitations (addressed in Phase 6)

- ~~CLI-first interface~~ → FastAPI REST API in Phase 6
- ~~Session memory non-persistent~~ → PostgreSQL + ChromaDB persistent memory in Phase 6
- ~~Single-user, no isolation~~ → startup_id isolation in Phase 6

### Phase 6 remaining limitations (documented honestly)

- Local ChromaDB and BM25 storage — not production-grade managed storage
- Thread-based Phase 5 agent execution — wrapped in `asyncio.to_thread()`, not natively async
- No real-time streaming — workflow results available via polling only
- Scanned PDFs not supported — text extraction requires selectable text
- Documents stuck in PROCESSING status if server restarts mid-processing — no task queue recovery
- Full analysis latency can be high — multiple provider calls, no caching layer
- RAG fusion weight fixed at 0.5 — not query-adaptive

---

# 🚀 Phase 6 Direction

Phase 6 has **started**.

The goal is **portfolio signal** — not SaaS completeness. Phase 6 adds the minimal backend infrastructure that gives the AI system persistent context, structured I/O, and a professional service boundary. Every non-AI component exists only to serve AI execution.

```mermaid
flowchart TD
    P5["✅ Phase 5 Complete\nv5.9.0"] --> P6["🚀 Phase 6 In Progress"]

    P6 --> DB["PostgreSQL\nSP-01: 5 tables + migrations"]
    P6 --> INFRA["Infrastructure\nSP-02: Config + ChromaDB isolation"]
    P6 --> AUTH["FastAPI + Auth\nSP-03: JWT + refresh tokens"]
    P6 --> API["Resource APIs\nSP-04: CRUD + PDF upload"]
    P6 --> MEM["Memory + RAG\nSP-05: Persistent memory + polished RAG"]
    P6 --> ORCH["Orchestration\nSP-06: TaskContext + AgentResult + workflow API"]

    DB --> DONE["v6.0.0\nPortfolio-ready"]
    INFRA --> DONE
    AUTH --> DONE
    API --> DONE
    MEM --> DONE
    ORCH --> DONE
```

## Phase 6 Sub-Phase Architecture

| Sub-Phase | Focus | Key Deliverable |
|---|---|---|
| SP-01 | Database Foundation | 5 tables, Alembic migrations, repository pattern |
| SP-02 | Infrastructure | Centralised config, ChromaDB startup_id isolation, file storage |
| SP-03 | Auth + FastAPI | JWT + refresh tokens, error envelope, health endpoints |
| SP-04 | Core Resource APIs | Startup/conversation/message/memory/document CRUD |
| SP-05 | Memory + RAG | LLM memory extraction, persistent ChromaDB, hybrid retrieval polished |
| SP-06 | Orchestration | TaskContext/AgentResult contracts, workflow API, memory+RAG injection |

## Phase 6 Architecture Layer

```mermaid
flowchart TD
    FE["Frontend"] --> API["FastAPI REST API"]
    API --> AUTH["JWT Auth Middleware"]
    AUTH --> SVC["Service Layer"]
    SVC --> REPO["Repository Layer"]
    REPO --> PG["PostgreSQL"]
    SVC --> ORCH["OrchestratorAgent"]
    ORCH --> TC["TaskContext\n(memory + RAG injected)"]
    TC --> AGENTS["17 Phase 5 Agents\n(unchanged internally)"]
    AGENTS --> WS["workflow_state"]
    WS --> JUDGE["LLM Judge"]
    JUDGE --> WRITER["ReportWriter"]
    WRITER --> RESULT["Workflow Result\nstored to PostgreSQL"]
    SVC --> MEM["Memory Pipeline\nExtraction + ChromaDB"]
    SVC --> RAG["RAG Pipeline\nBM25 + Vector + CrossEncoder"]
    MEM --> CHROMA["ChromaDB\nstartup_id isolated"]
    RAG --> CHROMA
```

## What Phase 6 Adds vs Phase 5

| Capability | Phase 5 | Phase 6 |
|---|---|---|
| Interface | CLI only | FastAPI REST API |
| Auth | None | JWT + refresh tokens |
| Memory | Lost on exit | PostgreSQL + ChromaDB persistent |
| Context | Single user | Multi-user, startup_id isolated |
| RAG | Working but flat | startup_id isolated, code polished |
| Agent contracts | Loose dicts | Typed TaskContext + AgentResult |
| Workflow | Synchronous CLI | API submission + status polling |
| Documents | CLI upload | REST upload + MIME validation + processing pipeline |

## What Phase 6 Explicitly Does NOT Build

| Feature | Reason |
|---|---|
| Autonomous planning / DAG | SaaS-level, not the story |
| Redis | Backend plumbing, low AI signal |
| Streaming (WebSocket) | Not needed for portfolio demo |
| Circuit breakers | Production concern |
| OpenTelemetry / Prometheus | Deployment concern |
| 9-dimension scoring engine | Current Phase 5 scoring sufficient |
| Crash recovery | Task queue required — out of scope |

---

# 🧩 Core Architectural Principles

```text
1. Agents own reasoning.
2. Tools own integrations.
3. Workflow state owns handoffs.
4. Validators own quality.
5. Providers remain replaceable.
6. Retrieval remains independently testable.
7. Failures remain observable.
8. Phase history remains traceable.
```

The architecture is intentionally modular so individual components can evolve without rewriting the entire system.

---

<div align="center">

### 🏁 v5.9.0 — Phase 5 Complete

**Multi-agent orchestration • OpenRouter migration • Gemini integration • Hybrid RAG • Structured validation • Provider resilience**

<br>

### 🚀 Phase 6 In Progress

**PostgreSQL persistence • JWT auth • FastAPI REST API • Persistent memory • startup_id RAG isolation • TaskContext/AgentResult contracts • Workflow API**

<br>

<sub>CoFoundr AI — Architecture Deep Dive | Phase 6 In Progress</sub>

</div>
