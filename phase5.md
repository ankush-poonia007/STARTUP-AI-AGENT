# CoFoundr AI — Phase 5 Master Plan
> Version: v5.0 Planning Document | Status: Locked | Phase 4 Closed: v4.1.0

---

## Vision

Build a fully dynamic multi-agent AI startup mentor.

Every user input triggers a **different combination** of specialized agents.  
No two requests run the same pipeline.  
One orchestrator brain coordinates all 16 independent agents dynamically.

---

## Core Principles

| Principle | Rule |
|---|---|
| Zero Frameworks | Pure Python only — no LangChain, no CrewAI, no AutoGen |
| Agent Independence | No agent imports from another agent — ever |
| Single Communication Channel | Agents communicate ONLY via `workflow_state` |
| Single Responsibility | One responsibility per file, per function |
| Testability | Every agent testable with mock `workflow_state` independently |
| Tool Isolation | Every tool in `tools/` works standalone — zero agent dependency |
| Prompt Centralization | All prompts in `prompts.py` — zero prompt strings inside agent files |
| Schema Separation | `workflow_state.py` contains schema only — zero logic |
| Cross-Cutting Concerns | Decorators handle logging, timing, retry, error handling |
| FastAPI Ready | Structure supports FastAPI migration without rewrite |
| Deployment Ready | Every module designed as an independently deployable service |
| Reusable Components | Tools imported by agents — never rewritten per agent |
| Thread Safety | All parallel workflow_state writes protected by threading.Lock() |

---

## Software Engineering Principles

### Single Responsibility Principle

Every function does exactly ONE thing.

```
BAD:
generate_llm_response_and_save_to_db_and_log_error()

GOOD:
generate_response()
save_response()
log_response()
```

### Independent Reusable Functions

Functions must not depend on where they are used.
Every tool function must be callable from any agent without modification.

```
groq_tool.py → callable by MVPAdvisorAgent
groq_tool.py → callable by TechAdvisorAgent
groq_tool.py → callable by StartupScorerAgent
Same function. Zero duplication.
```

### Load Balance Across Files

No single file carries excess responsibility.
If a file grows beyond its single responsibility — split it.

### FastAPI-Ready Structure

Business logic must never be coupled to API routes.
Every agent `run()` method must be callable directly — no HTTP dependency.

### Deployment-Ready Modules

Every module designed as if it will eventually be an independent service.
Zero tight coupling between modules.

### `__main__` Guard Rule

Every file that contains test or batch-run code MUST have a `__main__` guard.

```python
# REQUIRED in every file with executable test code
if __name__ == "__main__":
    # test code here
```

Without this guard, importing the file anywhere triggers test code silently.
This was a real bug in Phase 4 — enforced strictly in Phase 5.

---

## Thread Safety — `threading.Lock()`

### The Problem

When two agents run in parallel — both write to `workflow_state` simultaneously.

```
WITHOUT LOCK:

Thread A reads state → modifies → writes back
Thread B reads state → modifies → writes back
                                        ↑
                   Thread A's write is overwritten
                   Data lost silently — no error raised
```

### The Solution

```
WITH LOCK:

Thread A acquires lock → reads → modifies → writes → releases lock
Thread B WAITS for lock → then reads → modifies → writes → releases lock
No data lost. No silent overwrite. One writer at a time.
```

### Implementation

```python
import threading

# Defined once in OrchestratorAgent — passed to all parallel batches
state_lock = threading.Lock()

# Inside parallel batch Fan-In — every result write is locked
for completed_future in as_completed(futures):
    result = completed_future.result()
    with state_lock:
        state.update(result)
    # Lock automatically released after block exits
```

### Rules
- `state_lock` defined ONCE in `OrchestratorAgent`
- Passed to every parallel batch execution
- ALL `state.update()` calls inside parallel batches wrapped with `with state_lock:`
- Sequential agents do NOT need lock — they run one at a time
- Lock lives in `OrchestratorAgent` only — not in agent files

---

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                               │
│          (idea / question / PDF / partial concept)              │
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
│   │  - build plan       │    │  - return agent list        │   │
│   │  - delegate         │    │  - return execution order   │   │
│   │  - track pipeline   │    └─────────────────────────────┘   │
│   │  - handle failures  │                                       │
│   │  - manage lock      │                                       │
│   └─────────────────────┘                                       │
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
│   groq_tool.py      pdf_tool.py                                 │
│                                                                 │
│   [Standalone — no agent dependency — reusable across agents]   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Intent Classification System

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
| `full_analysis` | 3,4,5,6,7,8,9,10,15 | Full 8-section report |
| `partial_idea` | 3,4,6,7,10,12,15 | Expanded idea + plan |
| `idea_exploration` | 11 | List of startup ideas |
| `nurturing` | 5,10,12 | Improved startup plan |
| `advancement` | 13 | Scaling roadmap |
| `general_chat` | 14 | Conversational response |
| `pdf_request` | 16 | Downloadable PDF |

---

## 16 Agents — Complete Definition + Output Formats

### Agent 1 — OrchestratorAgent
```
File        : agents/orchestrator_agent.py
Triggered By: Every request
Tools       : None — delegation only
Input       : user_input + pitch_deck_path
Output      : Final workflow_state dict

Output Format:
    Returns complete workflow_state dict with all keys populated
    by the agents that ran for this intent.

Responsibilities:
- Initialize workflow_state from schema
- Validate all inputs before processing
- Extract pitch_deck_text via pdf_tool if PDF provided
- Delegate to IntentRouterAgent first — always
- Read intent + execution_plan from workflow_state
- Build dynamic pipeline from execution_plan
- Execute parallel batches via ThreadPoolExecutor + threading.Lock()
- Execute sequential agents in defined order
- Handle per-agent failures with retry logic
- Log pipeline status per agent
- Return final workflow_state

Failure Handling:
- IntentRouterAgent fails → raise PipelineInitError, stop pipeline
- Parallel batch agent fails → log error, continue other agents
- Sequential agent fails → retry up to MAX_RETRIES, then skip + log
- ALL agents fail → return workflow_state with full error log
```

### Agent 2 — IntentRouterAgent
```
File        : agents/intent_router_agent.py
Triggered By: Every request (called by Orchestrator first — always)
Tools       : groq_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["intent"] + workflow_state["execution_plan"]

Output Format:
    workflow_state["intent"] → str
        One of: "full_analysis" / "partial_idea" / "idea_exploration"
                "nurturing" / "advancement" / "general_chat" / "pdf_request"

    workflow_state["execution_plan"] → list of dicts
        [
            {"batch": 1, "agents": ["MarketResearchAgent", "WebSearchAgent", "RAGAgent"], "parallel": True},
            {"batch": 2, "agents": ["MVPAdvisorAgent", "TechAdvisorAgent"], "parallel": True},
            {"batch": 3, "agents": ["RiskAnalystAgent"], "parallel": False},
            ...
        ]

Responsibilities:
- Classify user input into one of 7 intent types
- Return ordered execution plan with parallel + sequential flags
- If classification fails → default to general_chat intent

Failure Handling:
- Fails → PipelineInitError raised — pipeline stops entirely
- Error logged to workflow_state["errors"]
```

### Agent 3 — MarketResearchAgent
```
File        : agents/market_research_agent.py
Triggered By: full_analysis, partial_idea
Tools       : tavily_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["market_data"]

Output Format:
    workflow_state["market_data"] → str
        Summarized plain text block with inline URL citations.
        Format per source:
            Title: <title>
            Summary: <summary>
            URL: <url>
        Multiple sources concatenated into one string.

Responsibilities:
- Targeted Tavily search for market size
- Search for industry trends
- Search for market demand signals
- Return summarized market data string with citations
```

### Agent 4 — WebSearchAgent
```
File        : agents/web_search_agent.py
Triggered By: full_analysis, partial_idea
Tools       : tavily_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["web_search_results"]

Output Format:
    workflow_state["web_search_results"] → str
        Summarized plain text block with inline URL citations.
        Format per source:
            Title: <title>
            Summary: <summary>
            URL: <url>
        Multiple sources concatenated into one string.

Responsibilities:
- Tavily search for competitors
- Search for funding landscape
- Search for existing market solutions
- Return summarized competitor string with citations
```

### Agent 5 — RAGAgent
```
File        : agents/rag_agent.py
Triggered By: full_analysis, nurturing
Tools       : chroma_tool.py + gemini_tool.py
Input       : workflow_state["user_input"] + workflow_state["pitch_deck_text"]
Output      : workflow_state["rag_context"]

Output Format:
    workflow_state["rag_context"] → list of dicts
        [
            {
                "text"    : str,   # chunk text (max 300 chars)
                "metadata": {
                    "page_number": int,
                    "file_name"  : str
                },
                "rerank_score": float
            },
            ...
        ]
        Empty list [] if no pitch deck uploaded.

Responsibilities:
- Embed query via Gemini embeddings
- Hybrid ChromaDB search (vector + BM25)
- CrossEncoder reranking on top-k results
- Return top-k relevant chunks with page + filename citations
- If no pitch deck → return [], skip gracefully
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
        Structured plain text with sections:
            ## Core Features
            ## Target User Personas
            ## 3-Month Build Scope
            ## Launch Sequence
        All grounded in market_data. No fabricated claims.

Responsibilities:
- Generate MVP feature list grounded in market data
- Prioritize features by user impact
- Suggest 3-month build scope for small team
- Reference pitch deck insights if rag_context available
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
        Structured plain text with sections:
            ## Frontend
            ## Backend
            ## Database
            ## Infrastructure
            ## Rationale
        Each choice justified against startup type + market context.

Responsibilities:
- Recommend tech stack aligned to startup type
- Justify each choice against market context
- Prioritize speed to market over complexity
- Suggest lean architecture for small team
```

### Agent 8 — RiskAnalystAgent
```
File        : agents/risk_analyst_agent.py
Triggered By: full_analysis
Tools       : gemini_tool.py
Input       : workflow_state["market_data"] + workflow_state["mvp_suggestions"]
Output      : workflow_state["risk_analysis"]

Output Format:
    workflow_state["risk_analysis"] → str
        Structured plain text per MVP feature:
            ### Feature: <Feature Name>
            Risk:
            Why:
            Impact:
            Mitigation:
        Followed by:
            ## Highest Business Risk
            Risk:
            Reason:
            Mitigation:

Responsibilities:
- Evaluate market risks with mitigation
- Evaluate technical risks with mitigation
- Evaluate execution risks with mitigation
- Ground every risk in specific MVP feature context
- No generic risks — every risk tied to actual MVP feature
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
            "score"    : int,       # 0-100 overall viability score
            "reasoning": str,       # 2-3 sentence explanation
            "breakdown": {
                "market"    : int,  # 0-100
                "mvp"       : int,  # 0-100
                "tech"      : int,  # 0-100
                "risk"      : int   # 0-100 (higher = lower risk)
            },
            "highest_risk_flag": str  # name of lowest-scoring area
        }

Responsibilities:
- Score startup viability 0-100
- Provide per-section breakdown scores
- Provide clear reasoning for overall score
- Flag highest risk area explicitly
```

### Agent 10 — RecommendationAgent
```
File        : agents/recommendation_agent.py
Triggered By: full_analysis, nurturing
Tools       : tavily_tool.py + groq_tool.py
Input       : ALL previous workflow_state outputs
Output      : workflow_state["recommendations"]

Output Format:
    workflow_state["recommendations"] → list of dicts
        [
            {
                "title"         : str,  # short improvement title
                "description"   : str,  # what to improve + why
                "evidence"      : str,  # URL or search evidence
                "linked_weakness": str  # which agent flagged this weakness
            },
            ...  # 3-5 items maximum
        ]

Responsibilities:
- Run FRESH Tavily search — comparison + improvement focused
- Query: "how can [startup type] improve vs competitors"
- Generate 3-5 specific actionable improvements
- Ground each recommendation in fresh search evidence
- Tie each recommendation to a specific weakness from previous agents
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
                "rank"          : int,  # 1 = highest demand
                "idea"          : str,  # one-line startup concept
                "market_signal" : str,  # why this market is trending
                "source_url"    : str   # Tavily evidence URL
            },
            ...  # 5-10 items
        ]

Responsibilities:
- Search trending markets and opportunities via Tavily
- Generate 5-10 startup ideas from trends
- Match ideas to user interests or skills if provided
- Rank ideas by market demand signal
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
        Structured plain text with sections:
            ## Refined Concept
            ## Value Proposition
            ## Missing Components Added
            ## Suggested Business Model
            ## Differentiators
        Grounded in market_data if available.

Responsibilities:
- Fill missing gaps in partial startup concept
- Strengthen value proposition
- Suggest missing components
- Improve business model clarity
- Return complete fleshed-out startup idea
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
        Structured plain text with sections:
            ## Current Stage Assessment
            ## Scaling Roadmap
            ## SaaS Transformation Path
            ## Enterprise Readiness Steps
            ## Market Benchmarks
        Each section grounded in Tavily search results.

Responsibilities:
- Assess current startup stage
- Build concrete scaling roadmap
- Suggest SaaS transformation path if applicable
- Recommend enterprise readiness steps
- Search market for scaling benchmarks via Tavily
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
        No markdown headers.
        No structured sections.
        Direct answer to user question.

Responsibilities:
- Handle startup Q&A conversationally
- Provide mentoring and guidance
- Answer business, funding, technology questions
- Output conversational text — NOT report format
```

### Agent 15 — ReportWriterAgent
```
File        : agents/report_writer_agent.py
Triggered By: full_analysis, partial_idea
Tools       : gemini_tool.py
Input       : ALL workflow_state outputs
Output      : workflow_state["final_report"]

Output Format:
    workflow_state["final_report"] → str
        Full markdown document with 8 sections:
            # Startup Analysis Report
            ## 1. Market Overview
            ## 2. MVP Recommendations
            ## 3. Tech Stack
            ## 4. Risk Analysis
            ## 5. Startup Score
            ## 6. Improvement Recommendations
            ## 7. Pitch Deck Insights
            ## 8. Strategic Summary
        All citations preserved exactly.
        All technical details preserved — no summarization.

Responsibilities:
- Assemble all agent outputs into structured report
- Preserve ALL citations exactly as provided by agents
- Preserve ALL technical details — no summarization
- ZERO new content generation — assembly + formatting only
```

### Agent 16 — PDFGeneratorAgent
```
File        : agents/pdf_generator_agent.py
Triggered By: pdf_request — ON-DEMAND ONLY
Tools       : pdf_tool.py
Input       : workflow_state["final_report"]
Output      : workflow_state["pdf_path"]

Output Format:
    workflow_state["pdf_path"] → str
        Absolute file path to generated PDF.
        "" (empty string) if not requested or generation failed.
        Example: "data/outputs/cofoundr_report_20260714.pdf"

PDF Rules:
- Text response ALWAYS shown in chat — PDF is optional
- PDF generated ONLY on explicit user request
- Qualifies for PDF: full_analysis, partial_idea outputs only
- Does NOT qualify: general_chat, idea_exploration outputs
- Auto-cleanup of unrequested PDFs → Phase 6 (frontend concern)

Responsibilities:
- Convert final_report markdown to professionally formatted PDF
- Apply clean formatting via ReportLab
- Return absolute download file path
- Triggered ONLY when user explicitly requests PDF
```

---

## Complete Execution Flowchart

```
┌──────────────────────────────────────────┐
│              USER INPUT                  │
│   idea / question / PDF / rough concept  │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│           OrchestratorAgent              │
│                                          │
│  1. Init workflow_state from schema      │
│  2. Validate inputs                      │
│  3. Extract pitch_deck_text if PDF       │
│  4. Create state_lock = threading.Lock() │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│          IntentRouterAgent               │
│                                          │
│  Input  : user_input                     │
│  Output : intent + execution_plan        │
│                                          │
│  Classifies into one of 7 intents        │
│                                          │
│  FAILURE → PipelineInitError             │
│            pipeline stops entirely       │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│     OrchestratorAgent reads plan         │
│     Builds dynamic pipeline              │
│     Shows plan to user                   │
│     [HIDDEN by default in UI]            │
│     [User clicks to expand + see log]    │
└─────────────────┬────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
   full_analysis?      Other intents?
        │                    │
        ▼                    ▼
                    [SINGLE AGENT PATH]
                    idea_exploration → IdeaGenerationAgent
                    nurturing        → NurturingAgent
                    advancement      → AdvancementAgent
                    general_chat     → GeneralChatAgent
                    pdf_request      → PDFGeneratorAgent
                             │
                             ▼
                      workflow_state updated
                      Text response returned

[FULL ANALYSIS PATH]
        │
        ▼
┌────────────────────────────────────────────┐
│  PARALLEL BATCH 1 — ThreadPoolExecutor     │
│  state_lock protects all state.update()    │
│                                            │
│  MarketResearchAgent ──┐                   │
│  WebSearchAgent        ├──▶ state (locked) │
│  RAGAgent ─────────────┘                   │
│                                            │
│  One agent fails → others continue         │
│  All agents fail → log + continue          │
└───────────────┬────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│  PARALLEL BATCH 2 — ThreadPoolExecutor     │
│  state_lock protects all state.update()    │
│                                            │
│  MVPAdvisorAgent ──┐                       │
│  TechAdvisorAgent ─┴──▶ state (locked)     │
│                                            │
│  One agent fails → other continues         │
└───────────────┬────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│  SEQUENTIAL — No lock needed               │
│                                            │
│  RiskAnalystAgent                          │
│       ↓ fails → retry MAX_RETRIES → skip   │
│  StartupScorerAgent                        │
│       ↓ fails → retry MAX_RETRIES → skip   │
│  RecommendationAgent                       │
│       ↓ fails → retry MAX_RETRIES → skip   │
│  ReportWriterAgent                         │
└───────────────┬────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│  ON-DEMAND ONLY                            │
│                                            │
│  PDFGeneratorAgent                         │
│  triggered ONLY if user requests PDF       │
└───────────────┬────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│  FINAL OUTPUT                              │
│                                            │
│  Text response → always shown in chat      │
│  PDF → only if explicitly requested        │
│  Agent activity log:                       │
│    → HIDDEN by default in UI               │
│    → User clicks to expand                 │
│    → Shows: agent name + status + timing   │
│    → Similar to Claude thinking toggle     │
└────────────────────────────────────────────┘
```

---

## Error Handling Strategy

### MAX_RETRIES
```
MAX_RETRIES = 3   # defined in src/config/settings.py
                  # imported by core/decorators.py
                  # applies to ALL agents uniformly
```

### Per-Scenario Failure Rules

| Scenario | Behaviour |
|---|---|
| IntentRouterAgent fails | Raise `PipelineInitError` — stop entire pipeline |
| Parallel batch agent fails | Log error, continue remaining agents in batch |
| All agents in parallel batch fail | Log all errors, continue to next stage with empty fields |
| Sequential agent fails | Retry up to MAX_RETRIES, then skip + log |
| ReportWriterAgent fails | Return partial workflow_state with error note |
| PDFGeneratorAgent fails | Return text report, log PDF failure separately |

### Error Log Format

```python
# Every error appended to workflow_state["errors"]
{
    "agent"    : str,   # agent class name
    "error"    : str,   # exception message
    "attempt"  : int,   # which retry attempt failed (1, 2, or 3)
    "timestamp": str    # ISO 8601 format
}
```

---

## Agent Visibility — UI Rules

```
Agent Activity Log:
- HIDDEN by default in chat UI
- User clicks "Show agent activity" to expand
- Displays per-agent: name + status + execution time
- Similar to Claude's expandable thinking toggle
- Shows pipeline execution plan before agents start
- Phase 5: complete log shown AFTER pipeline finishes
- Phase 6: real-time updates via WebSocket streaming
```

---

## `workflow_state` Schema — Fully Locked

```python
# workflow_state.py — schema only, zero logic, zero imports

workflow_state = {

    # ── INPUTS ──────────────────────────────────────────
    "user_input"          : str,     # raw user message
    "pitch_deck_text"     : str,     # extracted PDF text, "" if none

    # ── INTENT & PLAN ───────────────────────────────────
    "intent"              : str,     # classified by IntentRouterAgent
    "execution_plan"      : list,    # ordered agent execution list with parallel flags

    # ── AGENT OUTPUTS ────────────────────────────────────
    "market_data"         : str,     # MarketResearchAgent — plain text + citations
    "web_search_results"  : str,     # WebSearchAgent — plain text + citations
    "rag_context"         : list,    # RAGAgent — list of chunk dicts with metadata
    "mvp_suggestions"     : str,     # MVPAdvisorAgent — structured plain text
    "tech_recommendations": str,     # TechAdvisorAgent — structured plain text
    "risk_analysis"       : str,     # RiskAnalystAgent — per-feature risk plain text
    "startup_score"       : {
        "score"           : int,     # 0-100 overall
        "reasoning"       : str,     # explanation
        "breakdown"       : dict,    # per-section scores
        "highest_risk_flag": str     # lowest scoring area name
    },
    "recommendations"     : list,    # RecommendationAgent — list of dicts
    "generated_ideas"     : list,    # IdeaGenerationAgent — list of ranked dicts
    "nurtured_idea"       : str,     # NurturingAgent — structured plain text
    "advancement_plan"    : str,     # AdvancementAgent — structured plain text
    "chat_response"       : str,     # GeneralChatAgent — plain conversational text
    "final_report"        : str,     # ReportWriterAgent — full markdown document
    "pdf_path"            : str,     # PDFGeneratorAgent — file path, "" if none

    # ── PIPELINE TRACKING ────────────────────────────────
    "pipeline_status"     : dict,    # per-agent: "success"/"failed"/"skipped"/"pending"
    "agent_retry_count"   : dict,    # per-agent: int — tracks retries vs MAX_RETRIES
    "execution_log"       : list,    # per-agent: name + timing + status entries
    "errors"              : list     # per-agent error log — see Error Log Format above
}
```

---

## `src/config/settings.py` — Phase 5 Configuration

```python
# src/config/settings.py
# Single source of truth for all configuration constants
# No logic — constants only

import os

# ── LLM MODELS ───────────────────────────────────────────────
GROQ_MODEL          = "llama-3.3-70b-versatile"
GEMINI_MODEL        = "gemini-2.5-flash"
EMBEDDING_MODEL     = "gemini-embedding-001"
RERANKER_MODEL      = "BAAI/bge-reranker-v2-m3"

# ── PIPELINE CONFIG ──────────────────────────────────────────
MAX_RETRIES         = 3
API_COOLDOWN_SECONDS = 60
MIN_COOLTIME_RETRY  = 3

# ── RETRIEVAL CONFIG ─────────────────────────────────────────
DEFAULT_VECTOR_TOP_K = 10
DEFAULT_RERANK_TOP_K = 3
TAVILY_MAX_RESULTS   = 3

# ── STORAGE PATHS ────────────────────────────────────────────
CHROMA_DB_PATH      = "data/chroma_db"
BM25_INDEX_DIR      = "data/BM25"
BM25_CORPUS_FILE    = os.path.join(BM25_INDEX_DIR, "existing_corpus.json")
PDF_OUTPUT_DIR      = "data/outputs"

# ── GEMINI API KEYS ──────────────────────────────────────────
# Loaded from .env — do not hardcode
GEMINI_API_KEYS     = [
    os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 21)
]
GEMINI_API_KEYS     = [k for k in GEMINI_API_KEYS if k]

# ── GROQ API KEYS ────────────────────────────────────────────
GROQ_API_KEYS       = [
    os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 6)
]
GROQ_API_KEYS       = [k for k in GROQ_API_KEYS if k]

# ── TAVILY ───────────────────────────────────────────────────
TAVILY_API_KEY      = os.getenv("TAVILY_API_KEY")
```

---

## Complete File Structure

```
cofoundr/
│
├── src/
│   │
│   ├── agents/
│   │   ├── orchestrator_agent.py        ← pipeline manager only
│   │   ├── intent_router_agent.py       ← classification only
│   │   ├── market_research_agent.py     ← Tavily market search only
│   │   ├── web_search_agent.py          ← Tavily competitor search only
│   │   ├── rag_agent.py                 ← ChromaDB hybrid retrieval only
│   │   ├── mvp_advisor_agent.py         ← MVP generation only
│   │   ├── tech_advisor_agent.py        ← tech stack only
│   │   ├── risk_analyst_agent.py        ← risk evaluation only
│   │   ├── startup_scorer_agent.py      ← 0-100 scoring only
│   │   ├── recommendation_agent.py      ← improvement suggestions only
│   │   ├── idea_generation_agent.py     ← idea generation only
│   │   ├── nurturing_agent.py           ← idea improvement only
│   │   ├── advancement_agent.py         ← scaling strategy only
│   │   ├── general_chat_agent.py        ← Q&A only
│   │   ├── report_writer_agent.py       ← report assembly only
│   │   ├── pdf_generator_agent.py       ← PDF generation only
│   │   └── workflow_state.py            ← schema only, zero logic
│   │
│   ├── tools/
│   │   ├── tavily_tool.py               ← all Tavily logic, standalone
│   │   ├── chroma_tool.py               ← all ChromaDB logic, standalone
│   │   ├── gemini_tool.py               ← all Gemini logic, standalone
│   │   ├── groq_tool.py                 ← all Groq logic, standalone
│   │   └── pdf_tool.py                  ← ReportLab + pdfplumber, standalone
│   │
│   ├── core/
│   │   ├── decorators.py                ← logging, timing, retry, error handling
│   │   └── exceptions.py                ← custom exception classes
│   │
│   ├── config/
│   │   └── settings.py                  ← all config constants, single source of truth
│   │
│   ├── prompts/
│   │   └── prompts.py                   ← ALL agent prompts, single source of truth
│   │
│   └── evaluation/
│       ├── evaluator.py                 ← existing RAG evaluator
│       └── ground_truth.py              ← existing benchmark dataset
│
├── data/
│   ├── chroma_db/                       ← persistent vector store (gitignored)
│   ├── BM25/                            ← BM25 index + corpus (gitignored)
│   └── outputs/                         ← generated PDF reports (gitignored)
│
└── tests/
    ├── test_tools.py                    ← standalone tool function tests
    ├── test_agents.py                   ← agent tests with mock workflow_state
    └── mock_workflow_state.py           ← test fixtures
```

### `tests/mock_workflow_state.py` — Purpose

```python
# Provides pre-filled workflow_state dicts for testing each agent independently
# Every agent must be testable WITHOUT running the full pipeline

MOCK_STATE_FULL = {
    "user_input"          : "AI-powered tiffin delivery for college students",
    "pitch_deck_text"     : "",
    "intent"              : "full_analysis",
    "execution_plan"      : [...],
    "market_data"         : "Sample market data with citations...",
    "web_search_results"  : "Sample competitor data with citations...",
    "rag_context"         : [],
    "mvp_suggestions"     : "Sample MVP suggestions...",
    "tech_recommendations": "Sample tech stack...",
    "risk_analysis"       : "Sample risk analysis...",
    "startup_score"       : {"score": 72, "reasoning": "...", "breakdown": {}, "highest_risk_flag": "market"},
    "recommendations"     : [],
    "generated_ideas"     : [],
    "nurtured_idea"       : "",
    "advancement_plan"    : "",
    "chat_response"       : "",
    "final_report"        : "",
    "pdf_path"            : "",
    "pipeline_status"     : {},
    "agent_retry_count"   : {},
    "execution_log"       : [],
    "errors"              : []
}

MOCK_STATE_EMPTY = {
    # All keys initialized to None / "" / [] as per schema
    # Used for testing early-stage agents like MarketResearchAgent
}
```

---

## Tools Per Agent — Complete Map

| Agent | Tools Used | Purpose |
|---|---|---|
| IntentRouterAgent | `groq_tool.py` | Fast intent classification |
| MarketResearchAgent | `tavily_tool.py` | Market size + trends search |
| WebSearchAgent | `tavily_tool.py` | Competitor + funding search |
| RAGAgent | `chroma_tool.py` + `gemini_tool.py` | Hybrid retrieval + embeddings |
| MVPAdvisorAgent | `groq_tool.py` | Fast MVP feature generation |
| TechAdvisorAgent | `groq_tool.py` | Fast stack recommendations |
| RiskAnalystAgent | `gemini_tool.py` | Deep risk evaluation |
| StartupScorerAgent | `groq_tool.py` | 0-100 viability scoring |
| RecommendationAgent | `tavily_tool.py` + `groq_tool.py` | Comparison search + suggestions |
| IdeaGenerationAgent | `tavily_tool.py` + `groq_tool.py` | Trend search + idea generation |
| NurturingAgent | `groq_tool.py` | Idea gap filling + improvement |
| AdvancementAgent | `groq_tool.py` + `tavily_tool.py` | Scaling strategy + benchmarks |
| GeneralChatAgent | `groq_tool.py` | Conversational Q&A |
| ReportWriterAgent | `gemini_tool.py` | Long-form report assembly |
| PDFGeneratorAgent | `pdf_tool.py` | PDF generation via ReportLab |

---

## Agent Code Pattern — Enforced Across All 16

```python
# Every agent follows this EXACT pattern — no exceptions

from core.decorators import log_execution, track_timing, retry_on_failure, handle_errors
from tools.groq_tool import call_groq           # import ONLY what agent uses
from prompts.prompts import AGENT_NAME_PROMPT   # always from prompts.py
from config.settings import GROQ_MODEL          # always from settings.py

class AgentName:
    """
    Single responsibility: [one line description]
    Reads  : workflow_state["key_a"], workflow_state["key_b"]
    Writes : workflow_state["output_key"]
    Tools  : tool_name.py
    """

    @log_execution
    @track_timing
    @retry_on_failure
    @handle_errors
    def run(self, workflow_state: dict) -> dict:
        # 1. Read ONLY required keys from workflow_state
        # 2. Call ONE tool from tools/
        # 3. Write result to assigned workflow_state key
        # 4. Update workflow_state["pipeline_status"][agent_name]
        # 5. Append entry to workflow_state["execution_log"]
        # 6. Return workflow_state
        return workflow_state


if __name__ == "__main__":
    # Standalone test using mock workflow_state
    from tests.mock_workflow_state import MOCK_STATE_EMPTY
    agent = AgentName()
    result = agent.run(MOCK_STATE_EMPTY.copy())
    print(result["output_key"])
```

---

## Orchestrator Pattern

```python
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class OrchestratorAgent:
    def run(self, user_input: str, pitch_deck_path: str) -> dict:

        # 1. Init workflow_state from schema
        state = init_workflow_state(user_input, pitch_deck_path)

        # 2. Validate inputs — raise on critical failure
        # 3. Extract PDF text via pdf_tool if pitch_deck_path provided

        # 4. Create thread lock for parallel state writes
        state_lock = threading.Lock()

        # 5. Run IntentRouterAgent — always first
        state = IntentRouterAgent().run(state)

        # 6. Read dynamic execution plan
        plan = state["execution_plan"]

        # 7. Execute parallel batches with lock protection
        for batch in [b for b in plan if b["parallel"]]:
            agents = [AGENT_REGISTRY[name]() for name in batch["agents"]]
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(agent.run, state) for agent in agents]
                for f in as_completed(futures):
                    result = f.result()
                    with state_lock:           # LOCK — prevents race condition
                        state.update(result)   # safe write

        # 8. Execute sequential agents in order
        for batch in [b for b in plan if not b["parallel"]]:
            for agent_name in batch["agents"]:
                agent = AGENT_REGISTRY[agent_name]()
                state = agent.run(state)

        # 9. Return final workflow_state
        return state
```

---

## Decorator Architecture — `core/decorators.py`

```
Every agent run() method wrapped with 4 decorators:

@log_execution    → logs agent name + start time + end time
@track_timing     → records duration to workflow_state["execution_log"]
@retry_on_failure → retries up to MAX_RETRIES on any failure
@handle_errors    → catches ALL exceptions, logs to workflow_state["errors"]

Decorator import chain:
    core/decorators.py imports MAX_RETRIES from config/settings.py
    Agents import decorators from core/decorators.py
    Agents NEVER define retry or error logic themselves

Rules:
- ALL decorator logic lives in core/decorators.py ONLY
- NO retry logic written inside any agent file
- NO try/except blocks inside any agent file
- NO logging code inside any agent file
- Agents stay clean — zero boilerplate
- MAX_RETRIES defined once in settings.py — imported by decorators.py
```

---

## `core/exceptions.py` — Custom Exceptions

```python
class PipelineInitError(Exception):
    """Raised when IntentRouterAgent fails — stops entire pipeline"""

class AgentExecutionError(Exception):
    """Raised when an agent fails after MAX_RETRIES exhausted"""

class ToolConnectionError(Exception):
    """Raised when a tool (Tavily/Groq/Gemini/ChromaDB) is unreachable"""

class WorkflowStateError(Exception):
    """Raised when a required workflow_state key is missing or wrong type"""
```

---

## Modularization Rules — Hard Enforced

### Agent Files
- Import ONLY from `tools/`, `prompts/`, `core/`, and `config/`
- NEVER import from another agent file
- ONE `run(workflow_state: dict) -> dict` method per agent
- ONE responsibility per agent — no exceptions
- No business logic in OrchestratorAgent — delegation only
- Every agent independently testable via mock_workflow_state
- Every agent file MUST have `if __name__ == "__main__":` guard

### Tool Files
- Zero agent dependency — fully standalone
- One tool category per file
- Every function independently callable and testable
- Pure API wrapping — no business logic inside tools
- Every tool file MUST have `if __name__ == "__main__":` guard

### `prompts.py` — All Prompt Constants
```
ORCHESTRATOR_PROMPT
INTENT_ROUTER_PROMPT
MARKET_RESEARCH_PROMPT
WEB_SEARCH_PROMPT
RAG_AGENT_PROMPT
MVP_ADVISOR_PROMPT
TECH_ADVISOR_PROMPT
RISK_ANALYST_PROMPT
STARTUP_SCORER_PROMPT
RECOMMENDATION_PROMPT
IDEA_GENERATION_PROMPT
NURTURING_PROMPT
ADVANCEMENT_PROMPT
GENERAL_CHAT_PROMPT
REPORT_WRITER_PROMPT
PDF_GENERATOR_PROMPT
```

Zero prompt strings inside any agent file.
Named constants only. Single source of truth.

### `workflow_state.py`
- Schema definition only
- Zero logic — zero imports — zero functions
- Single source of truth for ALL keys
- LOCKED before v5.0 starts — zero schema changes mid-build

### `config/settings.py`
- All configuration constants here — nowhere else
- No logic — constants only
- Imported by tools, decorators, agents
- API keys loaded from `.env` via `os.getenv()`

### `core/decorators.py`
- All cross-cutting concerns live here exclusively
- Agents import decorators — never reimplement them
- MAX_RETRIES imported from settings.py — not hardcoded here

---

## Documentation Update Rules

### `CHANGELOG.md`
- Updated after EVERY version release
- Format: version number + what was built + what was fixed
- No version ships without a CHANGELOG entry

### `LEARNING_LOG.md`
- Updated after EVERY session
- Log: concepts learned + mistakes made + fixes applied
- Recurring patterns tracked across sessions

### `ROADMAP.md`
- Updated after EVERY version release
- Flip status: In Progress → Complete per version
- Add new items discovered during build

---

## Report Structure — Full Analysis (8 Sections)

| # | Section | Source Agent |
|---|---|---|
| 1 | Market Overview | MarketResearchAgent + WebSearchAgent |
| 2 | MVP Recommendations | MVPAdvisorAgent |
| 3 | Tech Stack | TechAdvisorAgent |
| 4 | Risk Analysis | RiskAnalystAgent |
| 5 | Startup Score | StartupScorerAgent |
| 6 | Improvement Recommendations | RecommendationAgent |
| 7 | Pitch Deck Insights | RAGAgent |
| 8 | Strategic Summary | ReportWriterAgent |

---

## Build Versions

| Version | What Gets Built | Days |
|---|---|---|
| **v5.0** | `config/settings.py` + `workflow_state.py` schema + all `tools/` standalone tested + `core/decorators.py` + `core/exceptions.py` + `OrchestratorAgent` + `IntentRouterAgent` + `mock_workflow_state.py` | 4–5 |
| **v5.1** | `MarketResearchAgent` + `WebSearchAgent` + `RAGAgent` | 3–4 |
| **v5.2** | `MVPAdvisorAgent` + `TechAdvisorAgent` — parallel + lock tested | 2–3 |
| **v5.3** | `RiskAnalystAgent` + `StartupScorerAgent` | 2–3 |
| **v5.4** | `RecommendationAgent` + `IdeaGenerationAgent` | 2–3 |
| **v5.5** | `NurturingAgent` + `AdvancementAgent` + `GeneralChatAgent` | 3–4 |
| **v5.6** | `ReportWriterAgent` + `PDFGeneratorAgent` | 3–4 |
| **v5.7** | Parallel execution hardening + lock stress test + full error isolation | 3–4 |
| **v5.8** | Full integration test — all 7 intents, all 16 agent paths | 2–3 |
| **Total** | | **24–33 days** |

---

## First Build Step — v5.0 Sequence

```
Before writing a single agent:

STEP 1  → Define workflow_state.py schema completely — lock it
STEP 2  → Write config/settings.py with all constants
STEP 3  → Build + test tavily_tool.py standalone
STEP 4  → Build + test chroma_tool.py standalone
STEP 5  → Build + test gemini_tool.py standalone
STEP 6  → Build + test groq_tool.py standalone
STEP 7  → Build + test pdf_tool.py standalone
STEP 8  → Build core/exceptions.py
STEP 9  → Build core/decorators.py + test all 4 decorators
STEP 10 → Create prompts.py skeleton with all 16 named constants
STEP 11 → Create mock_workflow_state.py — MOCK_STATE_FULL + MOCK_STATE_EMPTY
STEP 12 → Build IntentRouterAgent + test with MOCK_STATE_EMPTY
STEP 13 → Build OrchestratorAgent + wire IntentRouterAgent + threading.Lock()
STEP 14 → End-to-end test: raw input → intent → execution_plan → output
```

---

## Future Scope — Explicitly Deferred

| Feature | Target Phase | Reason |
|---|---|---|
| `asyncio` execution | Phase 6 | Needs dedicated learning — no prior experience |
| WebSocket live streaming | Phase 6 | Agent log shown post-completion in Phase 5 |
| UserProfileAgent | Phase 6 | Requires persistent storage (SQLite) |
| FinancialPlanningAgent | Phase 6 | Too deep — separate domain |
| PitchDeckAgent | Phase 7 | Separate product entirely |
| Multi-brain orchestration | Phase 7 | After single brain fully mastered |
| GoToMarketAgent | Phase 6 | Scope expansion |
| Auto PDF cleanup | Phase 6 | Frontend concern |
| Persistent memory | Phase 6 | SQLite dependency |
| CompetitorIntelligenceAgent | Phase 6 | Covered by WebSearchAgent for now |
| BusinessModelAgent | Phase 6 | Can extend MVPAdvisorAgent later |
| Rate limit sharing across agents | Phase 6 | Complex infrastructure concern |
| Database schema / SQLite | Phase 6 | Persistent memory not in Phase 5 |
| Frontend component structure | Phase 6 | UI out of Phase 5 scope |
| API endpoint definitions | Phase 6 | FastAPI layer not built in Phase 5 |
| Authentication / user management | Phase 6+ | Separate concern entirely |
| Deployment configs (Docker/CI/CD) | Phase 7 | Premature for now |

---

## Three Concepts To Master Before v5.0

- **Python Decorators** — `@wraps`, `functools`, chaining multiple decorators correctly
- **`threading.Lock()`** — context manager usage, race condition prevention
- **`ThreadPoolExecutor` batching** — parallel agent groups, not just parallel tools

---

## Hard Rules Before v5.0 Starts

- `workflow_state.py` schema fully locked — zero changes mid-build
- `config/settings.py` written before any tool or agent file
- All `tools/` files built and tested independently before any agent uses them
- `core/decorators.py` built and tested before first agent is written
- `core/exceptions.py` defined before any error handling is wired
- `prompts.py` skeleton created with all 16 named prompt constants
- `mock_workflow_state.py` created before any agent test is written
- Every file has `if __name__ == "__main__":` guard before being committed
- `CHANGELOG.md` updated after every version
- `LEARNING_LOG.md` updated after every session
- `ROADMAP.md` updated after every version
- Phase 4 confirmed closed at v4.1.0 ✅

---

> **Phase 4 Status: Closed at v4.1.0**
> Hybrid Search + BM25 Persistence + CrossEncoder Reranking + Rate-Limit Retry + Classifier Prompt Centralization — all complete and verified.
>
> **Phase 5 Status: Ready to Start**
