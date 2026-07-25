# CoFoundr AI — Phase 5 Master Plan
> Version: v5.0 Planning Document | Status: Active | Phase 4 Closed: v4.1.0
> Sessions 0–9 Complete | Starting: Agent Implementation (Session 10+)

---

## Vision

Build a fully dynamic multi-agent AI startup mentor.

Every user input triggers a **different combination** of specialized agents.
No two requests run the same pipeline.
One orchestrator brain coordinates all 17 independent agents dynamically.

The system behaves like a team of specialized experts:
- One brain (Orchestrator) receives the problem
- One classifier (IntentRouter) decides which experts are needed
- Only the relevant experts activate — no wasted computation
- One judge (LLMJudge) validates quality at two checkpoints
- One assembler (ReportWriter) combines all expert outputs
- One formatter (PDFGenerator) delivers the final artifact

This is not a chatbot. This is a coordinated AI team.

---

## Sessions 0–9 Completion Status

| Session | What Was Built | Status |
|---|---|---|
| Session 0 | Orientation + session map | ✅ Complete |
| Session 1 | `config/settings.py` + `workflow_state.py` schema | ✅ Complete |
| Session 2 | `tavily_tool.py` | ✅ Complete |
| Session 3 | `chroma_tool.py` | ✅ Complete |
| Session 4 | `gemini_tool.py` | ✅ Complete |
| Session 5 | `groq_tool.py` | ✅ Complete |
| Session 6 | `bm25_tool.py` | ✅ Complete |
| Session 7 | `pdf_tool.py` | ⏳ Next |
| Session 8 | `core/exceptions.py` + `core/decorators.py` | ⏳ Pending |
| Session 9 | `prompts.py` + `mock_workflow_state.py` | ⏳ Pending |

**Next session starts: Agent implementation — OrchestratorAgent + IntentRouterAgent**

---

## Core Principles

| Principle | Rule | Why It Matters |
|---|---|---|
| Zero Frameworks | Pure Python only — no LangChain, no CrewAI, no AutoGen | Forces deep understanding of agent mechanics |
| Agent Independence | No agent imports from another agent — ever | Prevents cascading failures |
| Single Communication Channel | Agents communicate ONLY via `workflow_state` | One source of truth — no hidden state |
| Single Responsibility | One responsibility per file, per function | Every file replaceable without touching others |
| Testability | Every agent testable with mock `workflow_state` independently | No agent requires full pipeline to test |
| Tool Isolation | Every tool in `tools/` works standalone — zero agent dependency | Tools reusable across all agents |
| Prompt Centralization | All prompts in `prompts.py` — zero prompt strings inside agent files | One place to tune all AI behaviour |
| Schema Separation | `workflow_state.py` contains schema only — zero logic | Schema changes never break business logic |
| Cross-Cutting Concerns | Decorators handle logging, timing, retry, error handling | Agents stay clean — zero boilerplate |
| FastAPI Ready | Structure supports FastAPI migration without rewrite | Phase 6 migration costs zero rework |
| Deployment Ready | Every module designed as an independently deployable service | Each agent can become a microservice later |
| Reusable Components | Tools imported by agents — never rewritten per agent | Zero duplication across 17 agents |
| Thread Safety | All parallel workflow_state writes protected by threading.Lock() | No silent data loss in parallel execution |
| Model Split | Groq = reasoning, Gemini = tool calls | Cost efficiency + speed optimisation |

---

## Software Engineering Principles

### Single Responsibility Principle

Every function does exactly ONE thing.
If a function name contains "and" — it is doing too much.

```
BAD:
generate_llm_response_and_save_to_db_and_log_error()
→ Three responsibilities. One failure breaks all three silently.

GOOD:
generate_response()   → one job: call LLM, return text
save_response()       → one job: write to state
log_response()        → one job: append to execution_log
```

### Independent Reusable Functions

Functions must not depend on WHERE they are called from.
Every tool function must be callable from any agent without modification.

```
groq_tool.py → callable by MVPAdvisorAgent
groq_tool.py → callable by TechAdvisorAgent
groq_tool.py → callable by StartupScorerAgent
groq_tool.py → callable by GeneralChatAgent
Same function. Zero duplication. Zero modification per agent.
```

### Load Balance Across Files

No single file carries excess responsibility.
If a file grows beyond its single responsibility — split it.

```
BAD: one agents.py with all 17 agent classes → unmaintainable
GOOD: 17 separate agent files → each changeable independently
```

### FastAPI-Ready Structure

Business logic must never be coupled to API routes.
Every agent `run()` method must be callable directly — no HTTP dependency.

```
Phase 5: agent.run(state) called directly from OrchestratorAgent
Phase 6: router.post("/analyze") calls agent.run(state) — same method, zero change
```

### Deployment-Ready Modules

Every module designed as if it will eventually be an independent service.
Zero tight coupling between modules.

### `__main__` Guard Rule

Every file that contains test or batch-run code MUST have a `__main__` guard.

```python
# REQUIRED in every file — no exceptions
if __name__ == "__main__":
    # test code here — only runs when file executed directly
    # NEVER runs when file is imported by another module
```

Without this guard — importing the file triggers test code and real API calls silently.
This was a real bug in Phase 4. Enforced strictly in Phase 5.

### Function Calling — Explicitly Rejected

Python function calling (passing functions as LLM tools) is rejected for Phase 5.

```
REJECTED PATTERN:
llm.call(tools=[search_web, query_db, generate_text])
→ LLM decides which function to call — untestable at runtime

CORRECT PATTERN:
results = tavily_tool.search(query)      # explicit — predictable
response = groq_tool.text_call(prompt)   # explicit — predictable
```

Why rejected:
- Violates Single Responsibility — one call does many things
- Violates testability — runtime LLM decisions cannot be unit tested
- Deferred to future phase if explicitly needed

---

## Thread Safety — `threading.Lock()`

### The Problem — Race Condition

```
WITHOUT LOCK:

Time →    0ms         10ms        20ms        30ms
Thread A: reads state → modifies → writes back
Thread B:             reads state → modifies →            writes back
                                                                ↑
                              Thread A's write is overwritten here
                              market_data key lost silently — no error raised
```

### The Solution

```
WITH LOCK:

Thread A: acquires lock → reads → modifies → writes → releases lock
Thread B: BLOCKED ────────────────────────────────→ acquires lock → reads → writes
No data lost. Order guaranteed.
```

### Implementation

```python
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

state_lock = threading.Lock()  # defined ONCE in OrchestratorAgent

with ThreadPoolExecutor() as executor:
    futures = [executor.submit(agent.run, state) for agent in agents]
    for completed_future in as_completed(futures):
        result = completed_future.result()
        with state_lock:           # LOCK acquired before write
            state.update(result)   # safe write
        # LOCK automatically released — even if exception occurs
```

### Rules
- `state_lock` defined ONCE in `OrchestratorAgent` — never inside agent files
- ALL `state.update()` calls inside parallel batches wrapped with `with state_lock:`
- Sequential agents do NOT need lock — they run one at a time
- Lock never passed to or managed by agent files

---

## Model Split — Groq vs Gemini

### Three-Tier Model Assignment

| Model | Constant | Used By | Why |
|---|---|---|---|
| `llama-3.3-70b-versatile` | `GROQ_MODEL` | All reasoning agents | Fast structured reasoning |
| `gemini-2.5-flash` | `GEMINI_MODEL` | RAG, Risk, ReportWriter | Large context window |
| `gemini-3.5-flash-lite` | `GEMINI_LITE_MODEL` | Lightweight checks | Fastest + cheapest |
| `gemini-embedding-001` | `EMBEDDING_MODEL` | RAGAgent only | Embedding generation |
| `BAAI/bge-reranker-v2-m3` | `RERANKER_MODEL` | RAGAgent only | CrossEncoder reranking |

### Hard Rules
- Groq → IntentRouterAgent, MVPAdvisorAgent, TechAdvisorAgent, StartupScorerAgent,
  RecommendationAgent, IdeaGenerationAgent, NurturingAgent, AdvancementAgent,
  GeneralChatAgent, LLMJudgeAgent
- Gemini Flash → RAGAgent (non-embedding), RiskAnalystAgent, ReportWriterAgent
- Gemini Lite → lightweight intermediate checks only
- NEVER use Gemini for agent reasoning — use Groq
- NEVER use Groq for embedding calls — use Gemini
- Model constants always imported from `config/settings.py` — never hardcoded

---

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                               │
│     idea / question / PDF / partial concept / scaling ask       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                           │
│                                                                 │
│   ┌─────────────────────┐    ┌─────────────────────────────┐   │
│   │  OrchestratorAgent  │───▶│     IntentRouterAgent       │   │
│   │                     │◀───│                             │   │
│   │  - init state       │    │  - classify intent          │   │
│   │  - build plan       │    │  - detect document refs     │   │
│   │  - delegate         │    │  - return agent list        │   │
│   │  - track pipeline   │    │  - return execution order   │   │
│   │  - manage lock      │    └─────────────────────────────┘   │
│   │  - call LLMJudge    │                                       │
│   └─────────────────────┘                                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   VALIDATION LAYER                              │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                  LLMJudgeAgent                          │   │
│   │  run_mid()   → validates after Batch 1 + Batch 2        │   │
│   │  run_final() → validates after ReportWriterAgent        │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                           │
│                                                                 │
│   MarketResearchAgent    WebSearchAgent      RAGAgent           │
│   MVPAdvisorAgent        TechAdvisorAgent    RiskAnalystAgent   │
│   StartupScorerAgent     RecommendationAgent IdeaGenerationAgent│
│   NurturingAgent         AdvancementAgent    GeneralChatAgent   │
│   ReportWriterAgent      PDFGeneratorAgent                      │
│                                                                 │
│   [Only activated agents run — fully dynamic per request]       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       TOOL LAYER                                │
│                                                                 │
│   tavily_tool.py    chroma_tool.py    gemini_tool.py            │
│   groq_tool.py      bm25_tool.py      pdf_tool.py               │
│                                                                 │
│   [Standalone — no agent dependency — reusable across agents]   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Intent Classification System

### Why Intent Classification Exists

Not every user input needs all 17 agents.

```
"I have no startup idea"
→ needs IdeaGenerationAgent only
→ does NOT need RiskAnalystAgent — no idea to assess risk for

"Analyze my fintech startup"
→ needs full pipeline — all intelligence agents activated
```

### Document Reference Detection

RAGAgent activates for ANY intent — not just full_analysis.
IntentRouterAgent detects document references:

```
Signals that trigger RAGAgent addition to ANY pipeline:
- "based on my pitch deck"
- "from my document"
- "referring to the file I uploaded"
- pitch_deck_text is non-empty in workflow_state
```

If detected → RAGAgent added to execution plan regardless of intent.
Handled by IntentRouterAgent — no agent imports RAGAgent directly.

### User Entry Points

```
USER ARRIVES WITH...
        │
        ├──▶ Complete startup idea      → intent: full_analysis
        │
        ├──▶ Partial / rough concept    → intent: partial_idea
        │
        ├──▶ No idea at all             → intent: idea_exploration
        │
        ├──▶ Existing startup           → intent: nurturing
        │
        ├──▶ Wants to scale             → intent: advancement
        │
        ├──▶ General question           → intent: general_chat
        │
        └──▶ Requests PDF               → intent: pdf_request
```

### Intent → Agent Mapping

| Intent | Agents Activated | Output Type |
|---|---|---|
| `full_analysis` | 3,4,5*,6,7,8,9,10,15 + Judge mid + Judge final | Full 8-section report |
| `partial_idea` | 3,4,5*,6,7,10,12,15 + Judge final | Expanded idea + plan |
| `idea_exploration` | 11 | List of ranked startup ideas |
| `nurturing` | 5*,10,12 | Improved startup plan |
| `advancement` | 13 | Scaling roadmap |
| `general_chat` | 14 | Conversational response |
| `pdf_request` | 16 | Downloadable PDF |

*Agent 5 (RAGAgent) added to ANY intent if document reference detected

---

## 17 Agents — Complete Definition + Output Formats

### Agent 1 — OrchestratorAgent

```
File        : agents/orchestrator_agent.py
Triggered By: Every request — always first
Tools       : None — delegation only
Input       : user_input (str) + pitch_deck_path (str)
Output      : Complete final workflow_state dict

What it does NOT do:
    Does NOT call LLMs directly
    Does NOT contain business logic
    Does NOT write to keys owned by other agents

Execution Sequence:
    1. Init workflow_state — all keys at empty defaults
    2. Validate inputs — raise WorkflowStateError if user_input empty
    3. Extract pitch_deck_text via pdf_tool if path provided
    4. Create state_lock = threading.Lock()
    5. Run IntentRouterAgent — always first, always synchronous
    6. Read intent + execution_plan from workflow_state
    7. Execute parallel batch 1 via ThreadPoolExecutor + state_lock
    8. Execute parallel batch 2 via ThreadPoolExecutor + state_lock
    9. Call LLMJudgeAgent.run_mid() — validate mid-pipeline quality
    10. Execute sequential agents in defined order
    11. Call LLMJudgeAgent.run_final() — validate final report quality
    12. Trigger PDFGeneratorAgent if pdf_request intent
    13. Return final workflow_state

Failure Handling:
    IntentRouterAgent fails → raise PipelineInitError — stop pipeline
    Parallel batch agent fails → log, continue remaining agents
    All agents in batch fail → log all, continue to next stage
    Sequential agent fails → retry via decorator → skip + log
    LLMJudgeAgent.run_mid() rejects → log warning, continue with flag
    LLMJudgeAgent.run_final() rejects → deliver with quality warning
    ReportWriterAgent fails → return partial state with error note
    PDFGeneratorAgent fails → return text report, log PDF failure
```

### Agent 2 — IntentRouterAgent

```
File        : agents/intent_router_agent.py
Triggered By: Every request — called by OrchestratorAgent first
Tools       : groq_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["intent"] + workflow_state["execution_plan"]

Output Format:
    workflow_state["intent"] → str
        One of: "full_analysis" / "partial_idea" / "idea_exploration"
                "nurturing" / "advancement" / "general_chat" / "pdf_request"

    workflow_state["execution_plan"] → list of dicts
        [
            {
                "batch"   : 1,
                "agents"  : ["MarketResearchAgent", "WebSearchAgent", "RAGAgent"],
                "parallel": True
            },
            {
                "batch"   : 2,
                "agents"  : ["MVPAdvisorAgent", "TechAdvisorAgent"],
                "parallel": True
            },
            {
                "batch"   : 3,
                "agents"  : ["RiskAnalystAgent"],
                "parallel": False
            },
            ...
        ]

Failure Handling:
    Classification fails → default to "general_chat"
    Even default fails → raise PipelineInitError
    All failures logged to workflow_state["errors"]
```

### Agent 3 — MarketResearchAgent

```
File        : agents/market_research_agent.py
Triggered By: full_analysis, partial_idea
Tools       : tavily_tool.py (parallel tool execution internally)
Input       : workflow_state["user_input"]
Output      : workflow_state["market_data"]

Parallel Tool Execution Inside This Agent:
    Multiple Tavily calls run in parallel via ThreadPoolExecutor INSIDE the agent.
    This is parallel TOOLS within one agent — different from parallel AGENTS.

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(tavily_tool.search, market_size_query): "market_size",
            executor.submit(tavily_tool.search, trends_query)      : "trends",
            executor.submit(tavily_tool.search, demand_query)      : "demand"
        }
        results = {label: f.result() for f, label in futures.items()}

Output Format:
    workflow_state["market_data"] → str
        === Market Size ===
        Title: <title>
        Summary: <2-3 sentence summary>
        URL: <source url>

        === Industry Trends ===
        Title: <title>
        Summary: <2-3 sentence summary>
        URL: <source url>

        === Demand Signals ===
        Title: <title>
        Summary: <2-3 sentence summary>
        URL: <source url>
```

### Agent 4 — WebSearchAgent

```
File        : agents/web_search_agent.py
Triggered By: full_analysis, partial_idea
Tools       : tavily_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["web_search_results"]

Why separate from MarketResearchAgent:
    MarketResearchAgent → "what is the market?"
    WebSearchAgent      → "who exists in this market?"
    Different query intent = different results = different downstream value.

Output Format:
    workflow_state["web_search_results"] → str
        === Competitors ===
        Title: <title>
        Summary: <summary>
        URL: <url>

        === Funding Landscape ===
        Title: <title>
        Summary: <summary>
        URL: <url>

        === Existing Solutions ===
        Title: <title>
        Summary: <summary>
        URL: <url>
```

### Agent 5 — RAGAgent

```
File        : agents/rag_agent.py
Triggered By: full_analysis, nurturing — AND any intent with document reference
Tools       : chroma_tool.py + bm25_tool.py + gemini_tool.py
Input       : workflow_state["user_input"] + workflow_state["pitch_deck_text"]
Output      : workflow_state["rag_context"]

Dynamic Activation:
    RAGAgent added to ANY intent's plan if:
    - pitch_deck_text is non-empty
    - user references a document in their input
    IntentRouterAgent handles this — no agent imports RAGAgent directly.

Graceful Skip:
    No pitch deck uploaded → pitch_deck_text = "" → return []
    Downstream agents check: if rag_context == [] → skip pitch deck section
    Pipeline continues normally — no failure logged.

Retrieval Pipeline:
    1. Embed user_input via Gemini EMBEDDING_MODEL
    2. Vector search ChromaDB → top DEFAULT_VECTOR_TOP_K results
    3. BM25 lexical search via bm25_tool → top DEFAULT_VECTOR_TOP_K results
    4. Fuse vector + BM25 results (union, deduplicated)
    5. CrossEncoder reranking → top DEFAULT_RERANK_TOP_K results
    6. Return ranked chunks with metadata

Output Format:
    workflow_state["rag_context"] → list of dicts
        [
            {
                "text"        : str,
                "metadata"    : {
                    "page_number" : int,
                    "file_name"   : str
                },
                "rerank_score": float
            },
            ...  # DEFAULT_RERANK_TOP_K items maximum
        ]
        [] if no pitch deck uploaded
```

### Agent 6 — MVPAdvisorAgent

```
File        : agents/mvp_advisor_agent.py
Triggered By: full_analysis, partial_idea
Tools       : groq_tool.py
Input       : workflow_state["market_data"] + workflow_state["rag_context"]
Output      : workflow_state["mvp_suggestions"]

Output Format:
    workflow_state["mvp_suggestions"] → str
        ## Core Features
        [3-5 features grounded in market_data]

        ## Target User Personas
        [2-3 specific user types from market signals]

        ## 3-Month Build Scope
        [realistic scope for 1-3 person team]

        ## Launch Sequence
        [step-by-step order — what to build first and why]
```

### Agent 7 — TechAdvisorAgent

```
File        : agents/tech_advisor_agent.py
Triggered By: full_analysis, partial_idea
Tools       : groq_tool.py
Input       : workflow_state["market_data"]
Output      : workflow_state["tech_recommendations"]

Output Format:
    workflow_state["tech_recommendations"] → str
        ## Frontend
        [recommendation + justification]

        ## Backend
        [recommendation + justification]

        ## Database
        [recommendation + justification]

        ## Infrastructure
        [recommendation + justification]

        ## Rationale
        [why this stack suits THIS startup's market + team size]
```

### Agent 8 — RiskAnalystAgent

```
File        : agents/risk_analyst_agent.py
Triggered By: full_analysis
Tools       : gemini_tool.py (Gemini Flash — large context needed)
Input       : workflow_state["market_data"] + workflow_state["mvp_suggestions"]
Output      : workflow_state["risk_analysis"]

Why Gemini:
    Reads both market_data AND mvp_suggestions together.
    Combined context can be large — Gemini Flash handles this better.

Output Format:
    workflow_state["risk_analysis"] → str
        ### Feature: <Feature Name>
        Risk: <specific risk>
        Why: <grounded in market context>
        Impact: High / Medium / Low
        Mitigation: <concrete action>

        ## Highest Business Risk Overall
        Risk: <single biggest risk>
        Reason: <grounded in market_data>
        Mitigation: <concrete action>
```

### Agent 9 — StartupScorerAgent

```
File        : agents/startup_scorer_agent.py
Triggered By: full_analysis
Tools       : groq_tool.py
Input       : ALL previous workflow_state outputs
Output      : workflow_state["startup_score"]

Output Format:
    workflow_state["startup_score"] → dict
        {
            "score"             : int,   # 0-100 overall viability
            "reasoning"         : str,   # 2-3 sentence explanation
            "breakdown"         : {
                "market"        : int,   # 0-100
                "mvp"           : int,   # 0-100
                "tech"          : int,   # 0-100
                "risk"          : int    # 0-100 (100 = lowest risk)
            },
            "highest_risk_flag" : str    # name of lowest-scoring area
        }
```

### Agent 10 — RecommendationAgent

```
File        : agents/recommendation_agent.py
Triggered By: full_analysis, nurturing
Tools       : tavily_tool.py + groq_tool.py
Input       : ALL previous workflow_state outputs
Output      : workflow_state["recommendations"]

Why a THIRD Tavily search:
    MarketResearchAgent → "what is the market?"
    WebSearchAgent      → "who exists in this market?"
    RecommendationAgent → "how can THIS startup improve vs competitors?"
    Three different questions. Three different searches. Zero overlap.

Output Format:
    workflow_state["recommendations"] → list of dicts
        [
            {
                "title"           : str,
                "description"     : str,
                "evidence"        : str,  # URL from fresh Tavily search
                "linked_weakness" : str   # which agent flagged this weakness
            },
            ...  # 3-5 items maximum
        ]
```

### Agent 11 — IdeaGenerationAgent

```
File        : agents/idea_generation_agent.py
Triggered By: idea_exploration
Tools       : tavily_tool.py + groq_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["generated_ideas"]

Output Format:
    workflow_state["generated_ideas"] → list of dicts
        [
            {
                "rank"          : int,
                "idea"          : str,
                "market_signal" : str,
                "source_url"    : str
            },
            ...  # 5-10 items ranked by market demand
        ]
```

### Agent 12 — NurturingAgent

```
File        : agents/nurturing_agent.py
Triggered By: partial_idea, nurturing
Tools       : groq_tool.py
Input       : workflow_state["user_input"] + workflow_state["market_data"]
Output      : workflow_state["nurtured_idea"]

Output Format:
    workflow_state["nurtured_idea"] → str
        ## Refined Concept
        ## Value Proposition
        ## Missing Components Added
        ## Suggested Business Model
        ## Differentiators
```

### Agent 13 — AdvancementAgent

```
File        : agents/advancement_agent.py
Triggered By: advancement
Tools       : groq_tool.py + tavily_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["advancement_plan"]

Output Format:
    workflow_state["advancement_plan"] → str
        ## Current Stage Assessment
        ## Scaling Roadmap
        ## SaaS Transformation Path
        ## Enterprise Readiness Steps
        ## Market Benchmarks
```

### Agent 14 — GeneralChatAgent

```
File        : agents/general_chat_agent.py
Triggered By: general_chat
Tools       : groq_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["chat_response"]

Output Format:
    workflow_state["chat_response"] → str
        Plain conversational text.
        No markdown headers. No structured sections.
        Tone: startup mentor — knowledgeable, direct, encouraging.
```

### Agent 15 — ReportWriterAgent

```
File        : agents/report_writer_agent.py
Triggered By: full_analysis, partial_idea
Tools       : gemini_tool.py (Gemini Flash — large context assembly)
Input       : ALL workflow_state outputs
Output      : workflow_state["final_report"]

Critical Rule:
    ZERO new content generation — assembly and formatting only.
    Every fact must come from a previous agent's output.
    Only Section 8 (Strategic Summary) contains original writing.

Output Format:
    workflow_state["final_report"] → str
        # Startup Analysis Report
        ## 1. Market Overview
        ## 2. MVP Recommendations
        ## 3. Tech Stack
        ## 4. Risk Analysis
        ## 5. Startup Score
        ## 6. Improvement Recommendations
        ## 7. Pitch Deck Insights  ← skipped if rag_context == []
        ## 8. Strategic Summary
        All citations preserved exactly. All technical details preserved.
```

### Agent 16 — PDFGeneratorAgent

```
File        : agents/pdf_generator_agent.py
Triggered By: pdf_request — ON-DEMAND ONLY, never automatic
Tools       : pdf_tool.py (ReportLab)
Input       : workflow_state["final_report"]
Output      : workflow_state["pdf_path"]

PDF Rules:
    Text response ALWAYS shown in chat — PDF is additional
    PDF generated ONLY when user explicitly requests it
    Qualifies: full_analysis, partial_idea outputs only
    Does NOT qualify: general_chat, idea_exploration outputs
    Auto-cleanup → Phase 6 (frontend concern)

Output Format:
    workflow_state["pdf_path"] → str
        "data/outputs/cofoundr_report_20260714_143022.pdf"
        "" if not requested or generation failed
```

### Agent 17 — LLMJudgeAgent

```
File        : agents/llm_judge_agent.py
Triggered By: OrchestratorAgent at two specific checkpoints
Tools       : groq_tool.py
Input       : workflow_state (full state at checkpoint)
Output      : workflow_state["judge_feedback"]["mid_pipeline"]
              workflow_state["judge_feedback"]["final"]

Why Two Methods — Not One:
    run_mid() and run_final() are two separate responsibilities.
    One method with a stage parameter hides branching — violates SRP.
    Two methods = two independently testable, independently callable checks.

run_mid() — called AFTER Batch 1 + Batch 2, BEFORE sequential agents:
    Checks:
    - Intent classified correctly for this input?
    - market_data relevant to the startup type?
    - web_search_results contain competitor information?
    - rag_context populated if pitch deck was uploaded?
    - Data quality sufficient to proceed?
    On rejection: logs warning, pipeline CONTINUES with flag set

run_final() — called AFTER ReportWriterAgent, BEFORE user sees response:
    Checks:
    - All 8 sections present in final_report?
    - Citations intact and properly formatted?
    - startup_score breakdown internally consistent?
    - Report coherent end-to-end?
    On rejection: logs warning, report DELIVERED with quality warning

Output Format:
    workflow_state["judge_feedback"] → dict
        {
            "mid_pipeline": str,  # "PASS" or rejection reason
            "final"       : str   # "PASS" or rejection reason
        }
```

---

## Complete Execution Flowchart

```
┌──────────────────────────────────────────────┐
│                USER INPUT                    │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           OrchestratorAgent                  │
│  1. Init workflow_state                      │
│  2. Validate user_input                      │
│  3. Extract pitch_deck_text if PDF           │
│  4. Create state_lock = threading.Lock()     │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           IntentRouterAgent                  │
│  Reads  : user_input                         │
│  Detects: document references                │
│  Writes : intent + execution_plan            │
│  FAILURE → PipelineInitError — stop          │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  OrchestratorAgent builds dynamic pipeline   │
│  Shows plan in UI — hidden by default        │
│  User can expand to see agent activity log   │
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
    full_analysis?       Other intents?
    partial_idea?              │
         │                    ▼
         │         [SINGLE AGENT PATH]
         │         idea_exploration → IdeaGenerationAgent
         │         nurturing        → NurturingAgent (+RAGAgent if doc)
         │         advancement      → AdvancementAgent
         │         general_chat     → GeneralChatAgent
         │         pdf_request      → PDFGeneratorAgent
         │                    │
         │                    ▼
         │         Judge final if report generated
         │         Text response returned to user
         │
[FULL ANALYSIS / PARTIAL IDEA PATH]
         │
         ▼
┌──────────────────────────────────────────────────┐
│  PARALLEL BATCH 1 — ThreadPoolExecutor           │
│  state_lock protects every state.update()        │
│                                                  │
│  MarketResearchAgent ──┐                         │
│  WebSearchAgent        ├──▶ state (locked write) │
│  RAGAgent* ────────────┘                         │
│  *added if document reference detected           │
│  One agent fails → others continue               │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│  PARALLEL BATCH 2 — ThreadPoolExecutor           │
│  state_lock protects every state.update()        │
│                                                  │
│  MVPAdvisorAgent ──┐                             │
│  TechAdvisorAgent ─┴──▶ state (locked write)     │
│  One agent fails → other continues               │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│  LLMJudgeAgent.run_mid()                         │
│  PASS  → pipeline continues                      │
│  FAIL  → warning logged, pipeline continues      │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│  SEQUENTIAL — No lock needed                     │
│                                                  │
│  RiskAnalystAgent    → retry MAX_RETRIES → skip  │
│  StartupScorerAgent  → retry MAX_RETRIES → skip  │
│  RecommendationAgent → retry MAX_RETRIES → skip  │
│  ReportWriterAgent   → fails = partial state     │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│  LLMJudgeAgent.run_final()                       │
│  PASS  → clean response to user                  │
│  FAIL  → response delivered with quality warning │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│  ON-DEMAND ONLY                                  │
│  PDFGeneratorAgent — only if user requests PDF   │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│  FINAL OUTPUT                                    │
│  Text response → always shown in chat            │
│  PDF → only if explicitly requested              │
│  Agent log → hidden by default, expandable       │
│  Phase 5: log shown after pipeline completes     │
│  Phase 6: real-time via WebSocket                │
└──────────────────────────────────────────────────┘
```

---

## Error Handling Strategy

### MAX_RETRIES
```python
MAX_RETRIES = 3  # defined in src/config/settings.py
                 # imported by core/decorators.py
                 # never hardcoded in agent files
```

### Per-Scenario Failure Rules

| Scenario | Behaviour | Reason |
|---|---|---|
| IntentRouterAgent fails | PipelineInitError — stop pipeline | Cannot run without valid intent |
| Parallel batch agent fails | Log, continue remaining agents | Other agents are independent |
| All agents in batch fail | Log all, continue to next stage | Downstream handles empty inputs |
| Sequential agent fails | Retry MAX_RETRIES → skip + log | Multiple chances before skipping |
| LLMJudgeAgent.run_mid() fails | Log warning, continue with flag | Data issues noted, not blocking |
| LLMJudgeAgent.run_final() fails | Deliver with quality warning | User receives report with note |
| ReportWriterAgent fails | Return partial state with error | Individual outputs still useful |
| PDFGeneratorAgent fails | Return text report, log failure | Text is primary — PDF optional |

### Error Log Format

```python
{
    "agent"    : str,  # e.g. "MarketResearchAgent"
    "error"    : str,  # exception message
    "attempt"  : int,  # retry attempt number — 1, 2, or 3
    "timestamp": str   # ISO 8601 format
}
```

---

## Agent Visibility — UI Rules

```
Agent Activity Log:
- HIDDEN by default — does not clutter conversation
- User clicks "Show agent activity" to expand
- Similar to Claude's expandable thinking toggle
- Shows per agent: name + status + execution time
- Shows pipeline plan BEFORE agents start running
- Phase 5: complete log shown AFTER pipeline finishes
- Phase 6: real-time per-agent updates via WebSocket
```

---

## `workflow_state` Schema — Fully Locked

```python
# workflow_state.py — schema only, zero logic, zero imports
# LOCKED — zero changes mid-build without version bump

workflow_state = {

    # ── INPUTS ─────────────────────────────────────────────
    "user_input"          : str,     # raw user message
    "pitch_deck_text"     : str,     # extracted PDF text, "" if none

    # ── INTENT & PLAN ──────────────────────────────────────
    "intent"              : str,     # one of 7 intent strings
    "execution_plan"      : list,    # ordered batch dicts with parallel flags

    # ── AGENT OUTPUTS ──────────────────────────────────────
    "market_data"         : str,     # MarketResearchAgent
    "web_search_results"  : str,     # WebSearchAgent
    "rag_context"         : list,    # RAGAgent — chunk dicts, [] if no PDF
    "mvp_suggestions"     : str,     # MVPAdvisorAgent
    "tech_recommendations": str,     # TechAdvisorAgent
    "risk_analysis"       : str,     # RiskAnalystAgent
    "startup_score"       : {
        "score"           : int,     # 0-100
        "reasoning"       : str,
        "breakdown"       : dict,    # {"market":int,"mvp":int,"tech":int,"risk":int}
        "highest_risk_flag": str
    },
    "recommendations"     : list,    # RecommendationAgent — list of dicts
    "generated_ideas"     : list,    # IdeaGenerationAgent — ranked list
    "nurtured_idea"       : str,     # NurturingAgent
    "advancement_plan"    : str,     # AdvancementAgent
    "chat_response"       : str,     # GeneralChatAgent
    "final_report"        : str,     # ReportWriterAgent — full markdown
    "pdf_path"            : str,     # PDFGeneratorAgent — path or ""

    # ── VALIDATION ─────────────────────────────────────────
    "judge_feedback"      : {
        "mid_pipeline"    : str,     # "PASS" or rejection reason
        "final"           : str      # "PASS" or rejection reason
    },

    # ── PIPELINE TRACKING ──────────────────────────────────
    "pipeline_status"     : dict,    # per-agent: success/failed/skipped/pending
    "agent_retry_count"   : dict,    # per-agent: int vs MAX_RETRIES
    "execution_log"       : list,    # per-agent: name + timing + status
    "errors"              : list     # per-agent error dicts
}
```

---

## `src/config/settings.py` — Phase 5 Configuration

```python
# src/config/settings.py
# Single source of truth — zero logic, constants only
# API keys NEVER hardcoded — always from .env via os.getenv()

import os

# ── LLM MODELS ─────────────────────────────────────────────
GROQ_MODEL          = "llama-3.3-70b-versatile"    # all reasoning agents
GEMINI_MODEL        = "gemini-2.5-flash"            # standard tool calls
GEMINI_LITE_MODEL   = "gemini-3.5-flash-lite"       # lightweight checks
EMBEDDING_MODEL     = "gemini-embedding-001"         # RAGAgent embeddings
RERANKER_MODEL      = "BAAI/bge-reranker-v2-m3"     # RAGAgent reranking

# ── PIPELINE CONFIG ────────────────────────────────────────
MAX_RETRIES             = 3
API_COOLDOWN_SECONDS    = 60
MIN_COOLTIME_RETRY      = 3

# ── RETRIEVAL CONFIG ───────────────────────────────────────
DEFAULT_VECTOR_TOP_K    = 10
DEFAULT_RERANK_TOP_K    = 3
TAVILY_MAX_RESULTS      = 3

# ── STORAGE PATHS ──────────────────────────────────────────
CHROMA_DB_PATH      = "data/chroma_db"
BM25_INDEX_DIR      = "data/BM25"
BM25_CORPUS_FILE    = os.path.join(BM25_INDEX_DIR, "existing_corpus.json")
PDF_OUTPUT_DIR      = "data/outputs"

# ── API KEYS ───────────────────────────────────────────────
GEMINI_API_KEYS     = [
    os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 21)
]
GEMINI_API_KEYS     = [k for k in GEMINI_API_KEYS if k]

GROQ_API_KEYS       = [
    os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 6)
]
GROQ_API_KEYS       = [k for k in GROQ_API_KEYS if k]

TAVILY_API_KEY      = os.getenv("TAVILY_API_KEY")
```

---

## Complete File Structure

```
cofoundr/
│
├── src/
│   ├── agents/
│   │   ├── orchestrator_agent.py        ← pipeline manager only
│   │   ├── intent_router_agent.py       ← classification + plan only
│   │   ├── market_research_agent.py     ← Tavily market search + parallel tools
│   │   ├── web_search_agent.py          ← Tavily competitor search only
│   │   ├── rag_agent.py                 ← hybrid retrieval only
│   │   ├── mvp_advisor_agent.py         ← MVP generation only
│   │   ├── tech_advisor_agent.py        ← tech stack only
│   │   ├── risk_analyst_agent.py        ← risk evaluation only
│   │   ├── startup_scorer_agent.py      ← 0-100 scoring only
│   │   ├── recommendation_agent.py      ← improvement suggestions only
│   │   ├── idea_generation_agent.py     ← idea generation only
│   │   ├── nurturing_agent.py           ← idea improvement only
│   │   ├── advancement_agent.py         ← scaling strategy only
│   │   ├── general_chat_agent.py        ← Q&A only
│   │   ├── report_writer_agent.py       ← assembly only, no new content
│   │   ├── pdf_generator_agent.py       ← PDF generation, on-demand only
│   │   ├── llm_judge_agent.py           ← quality validation, two checkpoints
│   │   └── workflow_state.py            ← schema only, zero logic
│   │
│   ├── tools/
│   │   ├── tavily_tool.py               ← Tavily logic, standalone
│   │   ├── chroma_tool.py               ← ChromaDB logic, standalone
│   │   ├── gemini_tool.py               ← Gemini logic, standalone
│   │   ├── groq_tool.py                 ← Groq logic, standalone
│   │   ├── bm25_tool.py                 ← BM25 storage + retrieval, standalone
│   │   └── pdf_tool.py                  ← ReportLab + pdfplumber, standalone
│   │
│   ├── core/
│   │   ├── decorators.py                ← @log_execution @track_timing @retry @handle_errors
│   │   └── exceptions.py                ← all custom exception classes
│   │
│   ├── config/
│   │   └── settings.py                  ← ALL constants, single source of truth
│   │
│   ├── prompts/
│   │   └── prompts.py                   ← ALL agent prompts, named constants only
│   │
│   └── evaluation/
│       ├── evaluator.py
│       └── ground_truth.py
│
├── data/
│   ├── chroma_db/                       ← persistent vector store (gitignored)
│   ├── BM25/                            ← BM25 index + corpus (gitignored)
│   └── outputs/                         ← generated PDFs (gitignored)
│
└── tests/
    ├── test_tools.py
    ├── test_agents.py
    └── mock_workflow_state.py
```

### `tests/mock_workflow_state.py`

```python
# Every agent must be testable WITHOUT running full pipeline
# Import in any agent's __main__ block for standalone testing

MOCK_STATE_FULL = {
    "user_input"          : "AI tiffin delivery for college students",
    "pitch_deck_text"     : "",
    "intent"              : "full_analysis",
    "execution_plan"      : [],
    "market_data"         : "Sample market data with citations...",
    "web_search_results"  : "Sample competitor data with citations...",
    "rag_context"         : [],
    "mvp_suggestions"     : "## Core Features\n[sample]...",
    "tech_recommendations": "## Frontend\nReact...",
    "risk_analysis"       : "### Feature: AI Matching\nRisk:...",
    "startup_score"       : {
        "score": 72, "reasoning": "...",
        "breakdown": {"market":80,"mvp":65,"tech":75,"risk":68},
        "highest_risk_flag": "mvp"
    },
    "recommendations"     : [],
    "generated_ideas"     : [],
    "nurtured_idea"       : "",
    "advancement_plan"    : "",
    "chat_response"       : "",
    "final_report"        : "",
    "pdf_path"            : "",
    "judge_feedback"      : {"mid_pipeline": "", "final": ""},
    "pipeline_status"     : {},
    "agent_retry_count"   : {},
    "execution_log"       : [],
    "errors"              : []
}

MOCK_STATE_EMPTY = {
    "user_input"          : "AI tiffin delivery for students",
    "pitch_deck_text"     : "",
    "intent"              : "",
    "execution_plan"      : [],
    "market_data"         : "",
    "web_search_results"  : "",
    "rag_context"         : [],
    "mvp_suggestions"     : "",
    "tech_recommendations": "",
    "risk_analysis"       : "",
    "startup_score"       : {},
    "recommendations"     : [],
    "generated_ideas"     : [],
    "nurtured_idea"       : "",
    "advancement_plan"    : "",
    "chat_response"       : "",
    "final_report"        : "",
    "pdf_path"            : "",
    "judge_feedback"      : {"mid_pipeline": "", "final": ""},
    "pipeline_status"     : {},
    "agent_retry_count"   : {},
    "execution_log"       : [],
    "errors"              : []
}
```

---

## Tools Per Agent — Complete Map

| Agent | Tools | Model | Why |
|---|---|---|---|
| IntentRouterAgent | `groq_tool.py` | Groq | Fast classification |
| MarketResearchAgent | `tavily_tool.py` | N/A | Real web data |
| WebSearchAgent | `tavily_tool.py` | N/A | Real web data |
| RAGAgent | `chroma_tool.py` + `bm25_tool.py` + `gemini_tool.py` | Gemini (embed) | Hybrid retrieval |
| MVPAdvisorAgent | `groq_tool.py` | Groq | Structured reasoning |
| TechAdvisorAgent | `groq_tool.py` | Groq | Structured reasoning |
| RiskAnalystAgent | `gemini_tool.py` | Gemini Flash | Large context |
| StartupScorerAgent | `groq_tool.py` | Groq | Fast scoring |
| RecommendationAgent | `tavily_tool.py` + `groq_tool.py` | Groq | Search + synthesise |
| IdeaGenerationAgent | `tavily_tool.py` + `groq_tool.py` | Groq | Search + generate |
| NurturingAgent | `groq_tool.py` | Groq | Idea refinement |
| AdvancementAgent | `groq_tool.py` + `tavily_tool.py` | Groq | Strategy + benchmarks |
| GeneralChatAgent | `groq_tool.py` | Groq | Conversational |
| ReportWriterAgent | `gemini_tool.py` | Gemini Flash | Long-form assembly |
| PDFGeneratorAgent | `pdf_tool.py` | N/A (ReportLab) | Formatting only |
| LLMJudgeAgent | `groq_tool.py` | Groq | Fast validation |

---

## Agent Code Pattern — Enforced Across All 17

```python
# EXACT pattern — every agent follows this — no exceptions

from core.decorators import log_execution, track_timing, retry_on_failure, handle_errors
from tools.groq_tool import text_call
from prompts.prompts import AGENT_NAME_PROMPT
from config.settings import GROQ_MODEL


class AgentName:
    """
    Single responsibility: [one line]
    Reads  : workflow_state["key_a"], workflow_state["key_b"]
    Writes : workflow_state["output_key"]
    Tools  : groq_tool.py
    Model  : Groq
    """

    @log_execution
    @track_timing
    @retry_on_failure
    @handle_errors
    def run(self, workflow_state: dict) -> dict:

        # Step 1: Read ONLY the keys this agent needs
        user_input = workflow_state["user_input"]

        # Step 2: Call ONE tool
        result = text_call(
            prompt=AGENT_NAME_PROMPT.format(user_input=user_input),
            model=GROQ_MODEL
        )

        # Step 3: Write to THIS agent's assigned key ONLY
        workflow_state["output_key"] = result

        # Step 4: Update pipeline status
        workflow_state["pipeline_status"]["AgentName"] = "success"

        # Step 5: Return full workflow_state
        return workflow_state


if __name__ == "__main__":
    from tests.mock_workflow_state import MOCK_STATE_EMPTY
    agent = AgentName()
    result = agent.run(MOCK_STATE_EMPTY.copy())
    print(result["output_key"])
```

---

## Decorator Architecture — `core/decorators.py`

### Why Decorators

Without decorators — 17 agents × 20 lines of boilerplate = 340 lines of noise.
With decorators — every agent `run()` contains only business logic.

### The Four Decorators

```
@log_execution    → logs agent name + start + end time to execution_log
@track_timing     → records duration_ms to execution_log
@retry_on_failure → retries up to MAX_RETRIES — imported from config/settings.py
@handle_errors    → catches AgentExecutionError → logs to errors → pipeline continues
```

### Decorator Import Chain

```
config/settings.py          defines MAX_RETRIES = 3
        ↓
core/decorators.py          imports MAX_RETRIES from config/settings.py
        ↓
agents/any_agent.py         imports @retry_on_failure from core/decorators.py
        ↓
agent run() method          uses retry automatically with correct MAX_RETRIES
```

### Rules
- ALL decorator logic in `core/decorators.py` ONLY
- NO retry logic inside any agent file
- NO try/except blocks inside any agent file
- NO logging code inside any agent file
- MAX_RETRIES imported from settings.py — never hardcoded

---

## `core/exceptions.py`

```python
class PipelineInitError(Exception):
    """IntentRouterAgent fails — stops entire pipeline"""

class AgentExecutionError(Exception):
    """Agent fails after MAX_RETRIES exhausted"""

class ToolConnectionError(Exception):
    """Tool cannot connect — Tavily/Groq/Gemini/ChromaDB unreachable"""

class WorkflowStateError(Exception):
    """Required workflow_state key missing or wrong type"""
```

---

## `prompts/prompts.py` — All Prompt Constants

```python
# ALL agent prompts defined here as named constants
# Zero prompt strings inside any agent file — ever

ORCHESTRATOR_PROMPT       = "..."
INTENT_ROUTER_PROMPT      = "..."
MARKET_RESEARCH_PROMPT    = "..."
WEB_SEARCH_PROMPT         = "..."
RAG_AGENT_PROMPT          = "..."
MVP_ADVISOR_PROMPT        = "..."
TECH_ADVISOR_PROMPT       = "..."
RISK_ANALYST_PROMPT       = "..."
STARTUP_SCORER_PROMPT     = "..."
RECOMMENDATION_PROMPT     = "..."
IDEA_GENERATION_PROMPT    = "..."
NURTURING_PROMPT          = "..."
ADVANCEMENT_PROMPT        = "..."
GENERAL_CHAT_PROMPT       = "..."
REPORT_WRITER_PROMPT      = "..."
PDF_GENERATOR_PROMPT      = "..."
LLM_JUDGE_MID_PROMPT      = "..."
LLM_JUDGE_FINAL_PROMPT    = "..."
```

---

## Modularization Rules — Hard Enforced

### Agent Files
- Import ONLY from `tools/`, `prompts/`, `core/`, `config/`
- NEVER import from another agent file
- ONE `run(workflow_state: dict) -> dict` method per agent
- ONE responsibility per agent
- No business logic in OrchestratorAgent — delegation only
- Every agent independently testable via mock_workflow_state
- Every agent file MUST have `if __name__ == "__main__":` guard

### Tool Files
- Zero agent dependency — fully standalone
- One tool category per file
- Every function independently callable
- Pure API wrapping — no business logic
- Every tool file MUST have `if __name__ == "__main__":` guard

### `workflow_state.py`
- Schema ONLY — zero logic, zero imports, zero functions
- LOCKED — zero changes without version bump

### `config/settings.py`
- ALL constants here — nowhere else
- API keys via `os.getenv()` — never hardcoded

### `core/decorators.py`
- All cross-cutting concerns here exclusively
- MAX_RETRIES imported from settings — not hardcoded

---

## Documentation Update Rules

### `CHANGELOG.md` — after EVERY version
```
## v5.1.0
### Added
- MarketResearchAgent with parallel Tavily execution
### Fixed
- [bugs fixed]
```

### `LEARNING_LOG.md` — after EVERY session
```
## Session N — [date]
### Concepts Learned
### Mistakes Made
### Fixes Applied
### Recurring Patterns
```

### `ROADMAP.md` — after EVERY version
```
| v5.0 | ✅ Complete | settings + tools + core |
| v5.1 | 🔄 In Progress | agents batch 1 |
```

---

## Report Structure — 8 Sections

| # | Section | Source | Key Rule |
|---|---|---|---|
| 1 | Market Overview | MarketResearchAgent + WebSearchAgent | All URLs preserved |
| 2 | MVP Recommendations | MVPAdvisorAgent | All features preserved |
| 3 | Tech Stack | TechAdvisorAgent | All rationale preserved |
| 4 | Risk Analysis | RiskAnalystAgent | Per-feature risks preserved |
| 5 | Startup Score | StartupScorerAgent | Score + breakdown + reasoning |
| 6 | Improvement Recommendations | RecommendationAgent | All items + evidence |
| 7 | Pitch Deck Insights | RAGAgent | Skipped if rag_context == [] |
| 8 | Strategic Summary | ReportWriterAgent | Only section with original writing |

---

## Build Versions — Remaining

| Version | What Gets Built | Status |
|---|---|---|
| **v5.0** | settings + workflow_state + all tools + core + orchestrator + intent_router | ✅ Sessions 0–9 complete |
| **v5.1** | MarketResearchAgent + WebSearchAgent + RAGAgent | ⏳ Next |
| **v5.2** | MVPAdvisorAgent + TechAdvisorAgent | ⏳ Pending |
| **v5.3** | RiskAnalystAgent + StartupScorerAgent | ⏳ Pending |
| **v5.4** | RecommendationAgent + IdeaGenerationAgent | ⏳ Pending |
| **v5.5** | NurturingAgent + AdvancementAgent + GeneralChatAgent | ⏳ Pending |
| **v5.6** | ReportWriterAgent + PDFGeneratorAgent | ⏳ Pending |
| **v5.7** | LLMJudgeAgent + integration into Orchestrator | ⏳ Pending |
| **v5.8** | Parallel hardening + lock stress test + error isolation | ⏳ Pending |
| **v5.9** | Full integration — all 7 intents, all 17 agent paths | ⏳ Pending |

---

## What To Learn Before Each Agent Version

### Before v5.1 — MarketResearchAgent + WebSearchAgent + RAGAgent
- Parallel tool execution inside one agent — `ThreadPoolExecutor` within `run()`
- Tavily Python SDK — `TavilyClient`, result structure, `["results"]` list
- ChromaDB + BM25 hybrid fusion — how results are merged and deduplicated
- CrossEncoder reranking — why it improves RAG precision over vector-only

### Before v5.2 — MVPAdvisorAgent + TechAdvisorAgent
- Prompt engineering for structured plain text output from Groq
- Reading multiple `workflow_state` keys cleanly in one agent
- Parallel batch execution with lock — first time two agents run in parallel

### Before v5.3 — v5.5
- Groq structured output patterns — consistent section headers
- Sequential agent chain — each reads previous agent's output key

### Before v5.6 — ReportWriterAgent + PDFGeneratorAgent
- Gemini long-form generation — large input context handling
- ReportLab basics — `SimpleDocTemplate`, `Paragraph`, `Spacer`, styles

### Before v5.7 — LLMJudgeAgent
- LLM-as-judge pattern — prompting LLM to evaluate another LLM's output
- Evaluation rubrics — writing pass/fail criteria as prompt instructions
- Structured pass/fail parsing — extracting verdict + reason from response

---

## Future Scope — Explicitly Deferred

| Feature | Phase | Reason |
|---|---|---|
| `asyncio` execution | Phase 6 | No prior experience — dedicated learning needed |
| WebSocket live streaming | Phase 6 | Post-completion log shown in Phase 5 |
| LLMJudge restart on rejection | Phase 6 | Needs persistent memory |
| UserProfileAgent | Phase 6 | Needs SQLite |
| FinancialPlanningAgent | Phase 6 | Separate domain |
| PitchDeckAgent | Phase 7 | Separate product |
| Multi-brain orchestration | Phase 7 | After single brain mastered |
| GoToMarketAgent | Phase 6 | Scope expansion |
| Auto PDF cleanup | Phase 6 | Frontend concern |
| Persistent memory | Phase 6 | SQLite dependency |
| FastAPI endpoints | Phase 6 | Not in Phase 5 scope |
| Authentication | Phase 6+ | Separate concern |
| Docker/CI/CD | Phase 7 | Premature |
| Function calling pattern | Future | Violates SRP — explicitly rejected |

---

## Hard Rules — Always Active

- Every file has `if __name__ == "__main__":` guard
- `workflow_state.py` schema locked — zero changes without version bump
- All prompts in `prompts.py` — zero inline prompt strings in agent files
- All constants in `config/settings.py` — zero hardcoding anywhere
- All error handling via decorators — zero try/except in agent files
- All parallel writes protected by `state_lock`
- `CHANGELOG.md` updated after every version
- `LEARNING_LOG.md` updated after every session
- `ROADMAP.md` updated after every version
- Flowchart (Input / Output / Steps) before writing any function — no exceptions
- Client initialization inside functions only — never at module level
- Phase 4 confirmed closed at v4.1.0 ✅

---

> **Phase 4 Status: Closed at v4.1.0**
> **Sessions 0–9: Complete**
> **Current Status: Ready to build Agent 1 — OrchestratorAgent**
