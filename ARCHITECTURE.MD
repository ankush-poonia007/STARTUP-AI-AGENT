# 🏗️ BizRadar AI — Architecture Deep Dive

> A technical breakdown of every design decision made in BizRadar AI v2.0 — explaining what was built, why it was built that way, and what tradeoffs were made.

---

## 🎯 Design Philosophy

> *"Architecture First. Frameworks Later."*

BizRadar is intentionally built **without LangChain or LlamaIndex**. Every component that a framework would abstract — the ReAct loop, tool calling, parallel execution, context management — is implemented manually.

**Why?**
- Understanding the internals makes you a better engineer when you eventually use frameworks
- Frameworks hide bugs behind abstractions — manual code exposes them
- Provider independence — swapping Groq for another provider requires changing one file, not relearning a framework

---

## 📁 Component Map

```
bizradar-ai/
│
├── agent.py             ← ReAct loop + tool orchestration
├── app.py               ← CLI interface + conversation loop
├── context_manager.py   ← Sliding window memory
├── tools.py             ← Tool implementations (Tavily + Gemini)
├── tools_description.py ← Tool schemas for LLM function calling
└── prompts.py           ← System prompt + output format
```

---

## 🔁 agent.py — The ReAct Loop

### What It Does
Implements the **ReAct (Reasoning + Acting)** pattern — the core intelligence loop of BizRadar.

### How It Works

```
messages built → Groq API call → tool_calls in response?
                                        │
                        YES ────────────┘
                         │
                 ThreadPoolExecutor
                 (parallel tool execution)
                         │
                 results appended to messages
                         │
                 loop back to Groq API
                         │
                        NO → return final response
```

### Key Design Decisions

**1. `while True` loop**
The agent keeps calling the LLM until there are no more tool calls. This is the ReAct loop. The LLM itself decides when it has enough information to stop.

```python
while True:
    response = client.chat.completions.create(...)
    tool_calls = response_message.tool_calls or []
    if tool_calls:
        # execute tools, append results, loop again
    else:
        return response_message.content  # done
```

**Why not a fixed number of iterations?**
A fixed loop would either cut off early (incomplete answer) or waste API calls (unnecessary loops). Letting the LLM decide is more efficient and accurate.

---

**2. `ThreadPoolExecutor` for parallel tool execution**
When the LLM calls multiple tools simultaneously, they run in parallel — not one after another.

```python
with ThreadPoolExecutor() as executor:
    for tool_call in tool_calls:
        future[executor.submit(function_to_call, **args)] = tool_call.id
    for completed_future in as_completed(self.future):
        # collect results as they finish
```

**Why `as_completed` over `executor.map`?**
`executor.map` blocks until ALL tasks finish and returns results in submission order. `as_completed` yields results as they finish — faster overall when tools have different response times. A fast tool does not wait for a slow one.

---

**3. `self.future.clear()` after each tool round**
The future dictionary is cleared after each tool execution round so the next loop iteration starts clean. Without this, stale futures from previous rounds would accumulate.

---

**4. `self.messages` as the shared state**
All context — system prompt, conversation history, tool results — lives in `self.messages`. This is the single source of truth the LLM sees on every iteration. Tool results are appended as `role: "tool"` messages.

---

**5. Provider-specific exception handling**
Each Groq exception maps to a specific failure mode:

| Exception | Cause | Recovery |
|---|---|---|
| `AuthenticationError` | Bad API key | Check `.env` |
| `NotFoundError` | Wrong model name | Check model string |
| `RateLimitError` | Too many requests | Implement backoff |
| `BadRequestError` | Invalid parameters | Check tool schemas |
| `APIConnectionError` | Network failure | Check internet |

---

## 🧠 context_manager.py — Sliding Window Memory

### What It Does
Stores conversation history and returns the last 6 turns to the agent on each run.

### Design Decision — Why 6 turns?
- Too few turns: agent loses context, gives generic answers
- Too many turns: context window fills up, costs more tokens, slower inference
- 6 turns (3 user + 3 assistant) is a practical balance for a CLI agent

### Current Limitation
Memory resets when the process exits. There is no persistent storage. This is intentional for V1/V2 — complexity is added in Phase 5.

---

## 🛠️ tools.py — The Tool Layer

### Architecture

```
User Input
    ↓
analyze_market()      ← Tavily live web search
search_knowledge_base() ← Tavily deep search
suggest_mvp()         ← Gemini 2.5 Flash prompt
recommend_tech_stack() ← Gemini 2.5 Flash prompt
risk_analysis()       ← Gemini 2.5 Flash prompt
summarize_text()      ← Gemini 2.5 Flash (parallel summarization)
```

### Tool Design Decisions

**1. Shared client initialization at module level**
```python
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
tavily_client = TavilyClient(TAVILY_API_KEY)
```
Clients are initialized once when the module loads — not inside each function call. This avoids re-authenticating on every tool execution.

---

**2. Tavily returns a dictionary keyed by URL**
```python
message[result["url"]] = [result["title"], content]
```
Keying by URL serves two purposes:
- Deduplication — same URL cannot appear twice
- Citation tracking — the LLM can reference the source URL in its response

---

**3. Gemini tools use prompt templates**
Each Gemini-powered tool has a specific, focused prompt template:
- `suggest_mvp()` — frames Gemini as a startup advisor focused on 3-month builds
- `recommend_tech_stack()` — frames Gemini as a CTO focused on speed to market
- `risk_analysis()` — frames Gemini as a venture analyst focused on fatal flaws

**Why separate prompts per tool?**
A single generic prompt produces generic answers. Focused framing produces expert-level output per domain.

---

**4. `summarize_text()` uses parallel summarization**
When Tavily returns multiple results, each URL's content is summarized in parallel using `ThreadPoolExecutor` — same pattern as the agent's tool execution.

---

## 📋 tools_description.py — Tool Schemas

### What It Does
Defines the JSON schema for each tool so the LLM knows:
- What the tool is called
- What it does (description)
- What parameters it accepts
- Which parameters are required

### Why This File Exists Separately
Tool schemas are configuration, not logic. Keeping them in a separate file means:
- `agent.py` stays clean — it just passes `tools` to the API
- Schemas can be updated without touching tool logic
- Easy to audit — all tool interfaces visible in one place

### How Description Quality Affects Tool Selection
The LLM reads the `description` field to decide which tool to call. A vague description leads to wrong tool selection. Compare:

```
❌ Vague: "searches the web"
✅ Precise: "Analyzes market potential, competition, and trends for a startup idea by performing a live web search"
```

The precise version tells the LLM exactly when to use it.

---

## 📝 prompts.py — System Prompt Design

### Structure
The system prompt has 5 sections:
1. **Role definition** — who BizRadar is
2. **Rules** — behavioral constraints (no fake stats, no legal guarantees)
3. **Workflow** — step-by-step thinking process
4. **Output format** — exact markdown structure expected
5. **Limitations** — honest boundaries (no real-time data without tools)

### Key Design Decision — Rule 9
```
Always include sources and URLs from tool results in your final response.
Every claim must be backed by a cited URL.
```
This rule forces the LLM to use Tavily's URLs as citations — reducing hallucination and increasing response credibility.

---

## ⚖️ Tradeoffs & Known Limitations

| Decision | Benefit | Tradeoff |
|---|---|---|
| Groq over local Ollama | 10x faster inference | Requires internet + API key |
| `ThreadPoolExecutor` over `asyncio` | Simpler code, works with sync libraries | Not truly async, GIL limitations |
| In-memory context | Zero setup, fast | Lost on process exit |
| No framework | Deep understanding | More boilerplate code |
| Gemini for analysis tools | High quality output | Additional API dependency |

---

## 🔮 What Changes in Phase 3+

| Component | Current | Phase 3+ |
|---|---|---|
| `search_knowledge_base()` | Tavily web search | Real vector store retrieval |
| `context_manager.py` | In-memory list | SQLite persistent storage |
| `agent.py` | Single agent | Orchestrator + sub-agents |
| `app.py` | CLI only | FastAPI REST endpoints |

---

*BizRadar AI v2.0 — Architecture Document*