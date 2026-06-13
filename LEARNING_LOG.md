<div align="center">

# 📓 BizRadar AI — Learning Log

<sub>A personal record of concepts learned, decisions made, mistakes caught, and what comes next. Updated after every meaningful session or milestone.</sub>

[![Phase](https://img.shields.io/badge/Current_Phase-4_Next-blue?style=for-the-badge)]()
[![Phase 3](https://img.shields.io/badge/Phase_3-Complete-brightgreen?style=for-the-badge)]()
[![Version](https://img.shields.io/badge/Version-v3.5.0-orange?style=for-the-badge)]()
</div>

---

## 👤 Engineer

**Ankush Poonia** — B.Tech AI/ML, 2nd Year, Arya College of Engineering, Jaipur

---

## 📊 Current Status

```
Phase 1 ✅ Complete
Phase 2 ✅ Complete
Phase 3 ✅ Complete
Phase 4 🔜 Next
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
| `text-embedding-004` | Consistent with existing Gemini stack in `tools.py` |
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
### 🎯 Phase 4 Entry Checklist
 
Before starting Phase 4 — complete these:
 
1. **Confirm `query_rag()` citation fix end-to-end** — upload a real PDF, query it, verify `{"text": ..., "metadata": ...}` dicts are returned and citations appear correctly in agent response
2. **Resolve Phase 4 backlog items in order:**
   - `task_type` in `embed_content()` — add `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY`
   - Batch duplicate ID failure in `embed_and_store()` — implement per-chunk upsert
   - Conversation history persistence — SQLite or disk
3. **Answer before starting Phase 4** — right now BizRadar ingests one PDF at startup. What architectural changes are needed to support multiple PDFs with metadata filtering per document? Do not code. Reason first. Flowchart second. Code third.

---

## 🎯 Phase 4 Entry Checklist

Before starting Phase 4 — complete these:

1. **Confirm `query_rag()` citation fix end-to-end** — upload a real PDF, query it, verify `{"text": ..., "metadata": ...}` dicts are returned and citations appear correctly in agent response
2. **Resolve Phase 4 backlog items in order:**
   - `task_type` in `embed_content()` — add `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY`
   - Batch duplicate ID failure in `embed_and_store()` — implement per-chunk upsert
   - Conversation history persistence — SQLite or disk
3. **Answer before starting Phase 4** — right now BizRadar ingests one PDF at startup. What architectural changes are needed to support multiple PDFs with metadata filtering per document? Do not code. Reason first. Flowchart second. Code third.

### Questions I Have Right Now
- How does ChromaDB `where` filtering interact with `n_results`? Does it filter before or after ranking?
- What is the right chunk size for a pitch deck vs a research paper?
- How do I evaluate if RAG is actually returning the right chunks?

### Session Notes
*(Fill this in as you learn)*

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

## 🎯 Next 3 Things — Before Phase 4

1. **Run the complete system end to end with a real PDF.** Test every path. Document every error and diagnose root cause before fixing anything.
2. **Push complete codebase to GitHub** including `rag.py`. Verify `.gitignore` is excluding `database/chroma_db/` and `.env`.
3. **Reason through this before next session** — right now BizRadar ingests one PDF at startup. What happens if a user wants to analyze three different pitch decks and compare them? What architectural changes would that require? Do not code. Just reason.

---

<div align="center">

<sub>Updated after every session. Honest entries only. — BizRadar AI v3.5.0 | Phase 3 Complete | Phase 4 Next</sub>

</div>