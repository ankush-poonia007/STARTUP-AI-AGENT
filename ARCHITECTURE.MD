<div align="center">

# 🏗️ BizRadar AI — Architecture Deep Dive

<sub>A technical breakdown of every design decision made in BizRadar AI v3.0.0 — what was built, why it was built that way, and what tradeoffs were made.</sub>

[![Version](https://img.shields.io/badge/Version-v3.0.0-orange?style=for-the-badge)]()
[![Phase](https://img.shields.io/badge/Phase_3-Complete-brightgreen?style=for-the-badge)]()
[![Approach](https://img.shields.io/badge/Frameworks-Zero-red?style=for-the-badge)]()

</div>

---

## 🎯 Design Philosophy

<div align="center">

> *"Architecture First. Frameworks Later."*

</div>

BizRadar is intentionally built **without LangChain or LlamaIndex**. Every component that a framework would abstract — the ReAct loop, tool calling, parallel execution, context management, RAG pipeline — is implemented manually.

**Why?**
- Understanding internals makes you a better engineer when you eventually use frameworks
- Frameworks hide bugs behind abstractions — manual code exposes them
- Provider independence — swapping Groq for another provider requires changing one file, not relearning a framework

---

## 📁 Component Map

```
bizradar-ai/
│
├── agent.py              ← ReAct loop + tool orchestration
├── app.py                ← CLI interface + PDF ingestion trigger
├── context_manager.py    ← Sliding window memory
├── tools.py              ← Tool implementations (Tavily + Gemini + RAG)
├── tools_description.py  ← Tool schemas for LLM function calling
├── prompts.py            ← System prompt + output format
├── rag.py                ← RAG pipeline (ingest, embed, store, query)
│
└── database/
    └── chroma_db/        ← Persistent ChromaDB vector store (gitignored)
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

<details>
<summary><b>⚙️ Key Design Decisions</b></summary>
<br>

**1. `while True` loop**

The agent keeps calling the LLM until there are no more tool calls. The LLM itself decides when it has enough information to stop.

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

When the LLM calls multiple tools simultaneously, they run in parallel — not sequentially.

```python
with ThreadPoolExecutor() as executor:
    for tool_call in tool_calls:
        future[executor.submit(function_to_call, **args)] = tool_call.id
    for completed_future in as_completed(future):
        # collect results as they finish
```

**Why <kbd>as_completed</kbd> over <kbd>executor.map</kbd>?**
`executor.map` blocks until ALL tasks finish and returns in submission order. `as_completed` yields results as they finish — faster when tools have different response times. A fast tool does not wait for a slow one.

---

**3. `self.future.clear()` after each tool round**

The future dictionary is cleared after each execution round so the next loop iteration starts clean. Without this, stale futures from previous rounds accumulate.

---

**4. `self.messages` as shared state**

All context — system prompt, conversation history, tool results — lives in `self.messages`. This is the single source of truth the LLM sees on every iteration. Tool results are appended as `role: "tool"` messages.

---

**5. Provider-specific exception handling**

| Exception | Cause | Recovery |
|---|---|---|
| `AuthenticationError` | Bad API key | Check `.env` |
| `NotFoundError` | Wrong model name | Check model string |
| `RateLimitError` | Too many requests | Implement backoff |
| `BadRequestError` | Invalid parameters | Check tool schemas |
| `APIConnectionError` | Network failure | Check internet |

</details>

---

## 🧠 context_manager.py — Sliding Window Memory

### What It Does
Stores conversation history and returns the last 6 turns to the agent on each run.

```python
conversation_history = []

def add_message(role, content):
    conversation_history.append({"role": role, "content": content})

def get_context():
    return conversation_history[-6:]
```

<details>
<summary><b>⚙️ Key Design Decisions</b></summary>
<br>

**Why 6 turns?**

| Too few turns | Too many turns | 6 turns |
|---|---|---|
| Agent loses context | Context window fills up | Practical balance |
| Generic answers | Higher token cost | 3 user + 3 assistant |

**Current Limitation:**
Memory resets when the process exits. No persistent storage — intentional for Phase 1–3. Persistence added in Phase 6 via SQLite.

</details>

---

## 🛠️ tools.py — The Tool Layer

### Architecture

```
User Input
    ↓
analyze_market()        ← Tavily live web search
search_knowledge_base() ← Tavily deep search
suggest_mvp()           ← Gemini 2.5 Flash prompt
recommend_tech_stack()  ← Gemini 2.5 Flash prompt
risk_analysis()         ← Gemini 2.5 Flash prompt
summarize_text()        ← Gemini 2.5 Flash (parallel summarization)
search_documents()      ← ChromaDB RAG retrieval (Phase 3)
```

<details>
<summary><b>⚙️ Key Design Decisions</b></summary>
<br>

**1. Shared client initialization at module level**

```python
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
tavily_client = TavilyClient(TAVILY_API_KEY)
```

Clients are initialized once when the module loads — not inside each function call. Avoids re-authenticating on every tool execution.

---

**2. Tavily returns a dictionary keyed by URL**

```python
message[result["url"]] = [result["title"], content]
```

Keying by URL serves two purposes:
- Deduplication — same URL cannot appear twice
- Citation tracking — the LLM can reference the source URL in its response

---

**3. Gemini tools use focused prompt templates**

Each Gemini tool has a specific, focused prompt:
- `suggest_mvp()` — frames Gemini as a startup advisor focused on 3-month builds
- `recommend_tech_stack()` — frames Gemini as a CTO focused on speed to market
- `risk_analysis()` — frames Gemini as a venture analyst focused on fatal flaws

A single generic prompt produces generic answers. Focused framing produces expert-level output per domain.

---

**4. `search_documents()` bridges RAG and ReAct**

```python
def search_documents(user_input: str):
    search_response = query_rag(user_input)
    if not search_response:
        return "No data found. The file does not exist."
    return search_response
```

The tool is intentionally thin — it delegates entirely to `query_rag()`. All RAG logic lives in `rag.py`. This keeps `tools.py` clean and `rag.py` independently testable.

---

**5. `summarize_text()` uses parallel summarization**

When Tavily returns multiple results, each URL's content is summarized in parallel using `ThreadPoolExecutor` — same pattern as the agent's tool execution.

</details>

<details>
<summary><b>⚠️ Known Issue — summarize_text() URL reference</b></summary>
<br>

Current code has a bug in the URL return line:

```python
# ❌ Bug — returns [title, content] list instead of the URL string
URL:{message[future[complete_future]]}

# ✅ Fix — the key itself is the URL
URL:{future[complete_future]}
```

The dictionary key in `future` is the URL string. Referencing `message[url]` returns the value (a list), not the key. Fix in Phase 4 cleanup.

</details>

---

## 🗄️ rag.py — The RAG Pipeline

### What It Does
Implements a two-phase Retrieval Augmented Generation pipeline that allows BizRadar to answer questions grounded in uploaded documents — eliminating hallucination for document-specific queries.

### The Problem It Solves
BizRadar's original agent produced a McKinsey citation that was never in Tavily's search results. It came from the LLM's own training memory — unverified and potentially wrong. RAG solves this by constraining the LLM to answer only from retrieved document chunks.

### Two-Phase Architecture

```
PHASE 1 — Ingestion (runs once per document)
PDF → pdfplumber → paragraph chunks → Gemini embeddings → ChromaDB

PHASE 2 — Retrieval (runs every query)
User question → Gemini embedding → cosine search → top 5 chunks → LLM
```

### Complete Implementation

```python
# Setup — runs once at module load
client = chromadb.PersistentClient(path="./database/chroma_db")
gemini_client = genai.Client()
collection = client.get_or_create_collection(name="data_storage")

# Phase 1a — PDF to chunks
def ingest_pdf(file_path: str) -> list:
    file_name = os.path.basename(file_path)
    chunks = []
    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                for para in paragraphs:
                    chunks.append({
                        "text": para,
                        "page_number": page_number,
                        "file_name": file_name
                    })
    return chunks

# Phase 1b — chunks to ChromaDB
def embed_and_store(new_chunks: list):
    texts = [item["text"] for item in new_chunks]
    response = gemini_client.models.embed_content(
        model="text-embedding-004",
        contents=texts
    )
    ids, embeddings, documents, metadatas = [], [], [], []
    for chunk, embedding in zip(new_chunks, response.embeddings):
        ids.append(hashlib.md5(chunk["text"].encode()).hexdigest())
        embeddings.append(embedding.values)
        documents.append(chunk["text"])
        metadatas.append({
            "page_number": chunk["page_number"],
            "file_name": chunk["file_name"]
        })
    try:
        collection.add(ids=ids, documents=documents,
                      metadatas=metadatas, embeddings=embeddings)
        return "Data ingestion complete."
    except chromadb.errors.DuplicateIDError:
        return "Document already ingested. Query directly."

# Phase 2 — query
def query_rag(user_input: str):
    response = gemini_client.models.embed_content(
        model="text-embedding-004",
        contents=[user_input]
    )
    results = collection.query(
        query_embeddings=response.embeddings,
        n_results=5
    )
    return results["documents"][0]
```

<details>
<summary><b>⚙️ Key Design Decisions</b></summary>
<br>

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

</details>

---

## 📋 tools_description.py — Tool Schemas

### What It Does
Defines the JSON schema for each tool so the LLM knows what the tool is called, what it does, what parameters it accepts, and which are required.

### Why This File Exists Separately
Tool schemas are configuration, not logic. Keeping them separate means:
- `agent.py` stays clean — it just passes `tools` to the API
- Schemas can be updated without touching tool logic
- Easy to audit — all tool interfaces visible in one place

### How Description Quality Affects Tool Selection

```
❌ Vague:   "searches the web"
✅ Precise: "Analyzes market potential, competition, and trends for a startup
            idea by performing a live web search"

❌ Vague:   "searches documents"
✅ Precise: "Use this tool when the user explicitly references or relies on
            their uploaded file, specific document, or local attachment"
```

The LLM reads the `description` field to decide which tool to call. Vague descriptions cause wrong tool selection.

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
| `\n\n` paragraph chunking | Simple, fast | Fails on tables, headers, bullet lists |
| Top-5 RAG retrieval | Covers most answers | May miss answer if it needs more chunks |

---

## 🔮 What Changes in Phase 4+

| Component | Current (v3.0.0) | Phase 4+ |
|---|---|---|
| `query_rag()` | Searches all documents | Metadata filter by filename |
| `app.py` | Single PDF at startup | Multiple PDFs, session management |
| Chunking | `\n\n` paragraph split | Fixed token or semantic chunking |
| RAG evaluation | None | Precision/recall measurement |
| `context_manager.py` | In-memory list | SQLite persistent storage (Phase 6) |
| `agent.py` | Single agent | Orchestrator + sub-agents (Phase 5) |
| `app.py` | CLI only | FastAPI REST endpoints (Phase 6) |

---

<div align="center">

<sub>BizRadar AI v3.0.0 — Architecture Document</sub>

</div>
