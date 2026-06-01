# 📓 BizRadar AI — Learning Log

> A personal record of concepts learned, decisions made, mistakes caught, and what comes next. Updated after every meaningful session or milestone.

---

## 👤 Engineer
**Ankush Poonia** — B.Tech AI/ML, 2nd Year, Arya College of Engineering, Jaipur

---

## 📊 Current Status

```
Phase 1 ✅ Complete
Phase 2 ✅ Complete
Phase 3 🔄 Not Started
Phase 4 📋 Planned
Phase 5 📋 Planned
```

---

## ✅ Phase 1 Log — Foundation Agent

**Completed:** BizRadar AI v1.0

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
| `.env` file exposed | API keys nearly pushed to GitHub | Created `.gitignore` with `_env` listed |
| Vague tool outputs | Placeholder tools returned generic strings | Replaced with real Tavily + Gemini calls in Phase 2 |

### Key Insight From This Phase
> Tools called manually in a fixed sequence is not an agent — it is a pipeline. A real agent decides which tools to call and when. That realization led directly to Phase 2.

---

## ✅ Phase 2 Log — Real Tool Integrations

**Completed:** BizRadar AI v2.0

### Concepts Learned

- [x] **ReAct Pattern** — Reasoning + Acting. The LLM reasons about what it needs, calls a tool, observes the result, reasons again, and loops until the answer is complete.
- [x] **Groq LPU Inference** — Groq uses purpose-built Language Processing Units (LPUs) instead of GPUs. Dramatically faster token generation. Free tier available.
- [x] **Tool Calling / Function Calling** — The LLM does not run code. It returns a structured `tool_calls` object with the function name and arguments. The developer executes it.
- [x] **Tool Schema Design** — JSON schemas tell the LLM what tools exist, what they do, and what parameters they accept. Description quality directly affects tool selection accuracy.
- [x] **ThreadPoolExecutor** — Submits multiple tool calls simultaneously. Each call runs in its own thread. Results collected via `as_completed`.
- [x] **`as_completed` vs `executor.map`** — `as_completed` yields results as they finish. `map` waits for all and returns in order. `as_completed` is faster when tools have different response times.
- [x] **Fan-Out Fan-In Pattern** — Dispatch multiple tasks simultaneously (fan-out), collect all results before proceeding (fan-in).
- [x] **Multi-Provider Architecture** — Groq for fast reasoning, Gemini for analysis tools, Tavily for web search. Each provider used for what it does best.
- [x] **Tavily Search API** — `include_answer`, `search_depth`, `exclude_domains`, `country` parameters. Returns structured results with title, content, and URL.
- [x] **Provider-Specific Error Handling** — Each API has its own exception types. Groq: `AuthenticationError`, `RateLimitError`. Gemini: `ResourceExhausted`, `Unauthenticated`.

### Mistakes Made & Fixed

| Mistake | What Happened | Fix |
|---|---|---|
| `self.future` not cleared | Stale futures accumulated across loops | Added `self.future.clear()` after each tool round |
| Generic tool descriptions | LLM picked wrong tools | Rewrote descriptions with specific, precise language |

### Key Insight From This Phase
> The LLM does not execute tools — it only requests them. The developer bridges the gap. Understanding this boundary is fundamental to building any agent system.

---

## 🔄 Phase 3 Log — RAG & Document Intelligence

**Status:** Not Started

### Concepts To Learn
- [ ] Vector Embeddings — what they are, how text becomes numbers
- [ ] ChromaDB — local vector store setup, upsert, similarity query
- [ ] Chunking Strategies — fixed size, recursive, semantic
- [ ] Retrieval Pipeline — embed → search → retrieve → inject
- [ ] PDF Parsing — extracting clean text from documents
- [ ] Reranking — improving retrieval quality beyond top-k

### Questions I Have Right Now
- How do I decide chunk size? What is too small vs too large?
- When does RAG outperform web search? When does web search win?
- How do I evaluate retrieval quality — what metrics exist?

### Session Notes
*(Fill this in as you learn)*

---

## 📋 Phase 4 Log — Multi-Agent Architecture

**Status:** Not Started

### Concepts To Learn
- [ ] Orchestrator pattern
- [ ] Agent communication and handoffs
- [ ] Shared memory between agents
- [ ] Specialized agent design

### Questions I Have Right Now
*(Fill in before starting Phase 4)*

---

## 📋 Phase 5 Log — Autonomous Platform

**Status:** Not Started

### Concepts To Learn
- [ ] Long-term memory with SQLite
- [ ] asyncio fundamentals
- [ ] FastAPI REST layer
- [ ] Dynamic planning and goal decomposition

---

## 💡 Running Insights

> Capture any "aha moment" here regardless of which phase it belongs to.

| Date | Insight |
|---|---|
| Phase 1 | A fixed tool pipeline is not an agent — an agent decides |
| Phase 2 | The LLM requests tools, the developer executes them — never forget this boundary |
| Phase 2 | `as_completed` is better than `map` when tools have unequal response times |
| Phase 2 | Tool description quality directly determines tool selection accuracy |

---

## 🐛 Mistakes & Lessons

> Every mistake logged here is a concept permanently learned.

| Phase | Mistake | Root Cause | Lesson |
|---|---|---|---|
| Phase 1 | Nearly pushed API keys to GitHub | Did not create `.gitignore` early enough | Always create `.gitignore` before first `git add` |
| Phase 2 | Stale futures across ReAct loop iterations | Did not clear `self.future` dict | Stateful objects in loops must be explicitly reset |
| Phase 2 | Wrong tool selected by LLM | Vague tool descriptions | Precision in tool schemas directly affects agent behavior |

---

## 📚 Resources Used

| Resource | Topic | Rating |
|---|---|---|
| Groq Documentation | LPU inference, API setup | ⭐⭐⭐⭐⭐ |
| Tavily Documentation | Search API parameters | ⭐⭐⭐⭐⭐ |
| Gemini API Docs | `google.genai` client usage | ⭐⭐⭐⭐ |
| Python `concurrent.futures` docs | ThreadPoolExecutor, as_completed | ⭐⭐⭐⭐⭐ |

---

## 🎯 Next 3 Things To Study

Based on current progress, the next concepts to tackle before starting Phase 3:

1. **`git rm --cached`** — untracking accidentally committed files
2. **`as_completed` deep dive** — understand timeout handling and exception propagation in futures
3. **ChromaDB quickstart** — embed 10 sentences, query top-3, understand the output format

---

*Updated after every session. Honest entries only.*