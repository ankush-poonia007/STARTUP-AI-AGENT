<div align="center">

# 🏗️ BizRadar AI — Architecture Deep Dive

<sub>A technical breakdown of every design decision made in BizRadar AI v4.0.0 — what was built, why it was built that way, and what tradeoffs were made.</sub>

[![Version](https://img.shields.io/badge/Version-v4.0.0-orange?style=for-the-badge)]()
[![Phase](https://img.shields.io/badge/Phase_4-In_Progress-blue?style=for-the-badge)]()
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
├── app.py                       ← CLI interface + PDF ingestion trigger
│
├── src/
│   ├── core/
│   │   ├── orchestrator.py      ← ReAct loop + stage-gated tool orchestration
│   │   └── context_manager.py   ← Sliding window memory
│   ├── tools/
│   │   ├── tools.py              ← Tool implementations (Tavily + Gemini + RAG)
│   │   └── tools_description.py  ← Tool schemas for LLM function calling
│   ├── prompts/
│   │   └── prompts.py            ← System prompt, FILE_PROMPT, output format
│   ├── rag/
│   │   └── rag.py                ← RAG pipeline + Phase 4 relevance classifier
│   └── evaluation/
│       ├── evaluator.py          ← Recall@K evaluation tool
│       └── ground_truth.py       ← Hand-written benchmark dataset
│
└── data/
    └── chroma_db/                 ← Persistent ChromaDB vector store (gitignored)
```

---

## 🔁 orchestrator.py — The ReAct Loop + Stage Gating

### What It Does
Implements the **ReAct (Reasoning + Acting)** pattern plus Phase 4 stage enforcement — the core intelligence loop of BizRadar.

### How It Works

```
messages built → Groq API call → tool_calls in response?
                                        │
                        YES ────────────┘
                         │
                 validate_stage_tools() gate
                 (rejects wrong-stage / batched calls)
                         │
                 ThreadPoolExecutor
                 (parallel tool execution per stage)
                         │
                 results appended to messages
                         │
                 loop back to Groq API
                         │
                        NO → return final response

Pipeline stages (LLM-driven, gated by validate_stage_tools()):
Stage 1 → analyze_market() + search_knowledge_base() in parallel
Stage 2 → suggest_mvp() + recommend_tech_stack() in parallel
Stage 3 → risk_analysis() alone
Stage 4 → search_documents() alone, on-demand, only if get_available_files()
           confirms this question requires reading an uploaded document
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

**3. `future` as a local variable, not `self.future`**

The future dictionary is declared fresh inside each `run()` call rather than stored as an instance attribute. `self.future` would persist across concurrent calls and risk corruption if two calls overlapped. A local variable resets cleanly every loop iteration — no manual `.clear()` needed.


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

---

**6. `validate_stage_tools()` — real stage enforcement (Phase 4)**

Before Phase 4, `stage` was only a print label — it had no power to stop the LLM from calling the wrong tool or batching tools across stages. This function checks every tool call against `STAGE_MAP` before execution and rejects the whole batch if anything is out of place.

```python
def validate_stage_tools(stage, tool_call_list, document_access_allowed):
    # checks each tool_call against STAGE_MAP[stage]
    # rejects whole batch if any tool is wrong-stage or hallucinated
    # detects missing required tools for the stage
    return {"valid": bool, "message": [...], "missing_tool_call": [...]}
```

Caught a real, repeated bug: the LLM bundling `risk_analysis` + `search_documents` together in Stage 3.

---

**7. `temp_list` — per-turn disposable context (Phase 4)**

`current_files` (which uploaded filenames are relevant) can change every turn. Injecting `FILE_PROMPT` directly into `self.messages[0]` would make that injection permanent. Instead, `run()` builds a disposable `temp_list = self.messages.copy()` each turn, conditionally replaces `temp_list[0]` with `SYSTEM_PROMPT + FILE_PROMPT`, runs the loop on `temp_list`, then extends `self.messages` with only the new turns. `self.messages[0]` stays the static system prompt forever.

</details>

---

## 🔄 Phase 4 Additions — Multi-PDF, Stage Gating, RAG Evaluation

| Capability | File | Summary |
|---|---|---|
| Cross-document isolation | `rag.py` | `query_rag(user_input, where)` — scopes retrieval to one filename via ChromaDB `where` filter, even with multiple PDFs in one collection |
| Document relevance gating | `rag.py` | `classify_document_relevance()` + `get_available_files(user_input)` — a dedicated Gemini call decides per-turn whether Stage 4 should even be reachable |
| Stage enforcement | `orchestrator.py` | `validate_stage_tools()` — real gatekeeping, not just a print counter |
| Improved chunking | `rag.py` | Paragraph-aware fixed-token chunker (`CHUNK_SIZE=250`, `OVERLAP=50`) replacing pure `\n\n` splitting |
| RAG evaluation | `evaluator.py`, `ground_truth.py` | Recall@K against 25 hand-written ground-truth questions across 5 documents — 100% recall@3 |

</details>

---

## 🧠 context_manager.py — Sliding Window Memory

### What It Does
Stores conversation history and returns the last 6 turns to the agent on each run.

```python
conversation_history = []

def add_message(role, content):
    if role not in ("user", "assistant"):
        print(f"Warning: invalid role '{role}'", file=sys.stderr)
        return
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
analyze_market()        ← Tavily live web search, self-summarizes before returning
search_knowledge_base() ← Tavily deep search, self-summarizes before returning
suggest_mvp()           ← Gemini 2.5 Flash prompt
recommend_tech_stack()  ← Gemini 2.5 Flash prompt
risk_analysis()         ← Gemini 2.5 Flash prompt
search_documents()      ← ChromaDB RAG retrieval — Stage 4, on-demand

Internal only (not LLM-callable):
summarize_text()        ← called inside analyze_market() and search_knowledge_base()
                           before they return — LLM never sees this directly
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
def search_documents(user_input: str) -> str:
    search_response = query_rag(user_input)
    if not search_response:
        return "No data found in document store."

    # Plain text with inline citations — LLM can cite directly without parsing
    formatted = ""
    for chunk in search_response:
        page, fname = chunk["metadata"]["page_number"], chunk["metadata"]["file_name"]
        formatted += f"[Page {page}, {fname}]: {chunk['text'][:300]}\n\n"
    return formatted
```

The tool is intentionally thin — it delegates entirely to `query_rag()`. All RAG logic lives in `rag.py`. This keeps `tools.py` clean and `rag.py` independently testable.

---

**5. `summarize_text()` uses parallel summarization**

When Tavily returns multiple results, each URL's content is summarized in parallel using `ThreadPoolExecutor` — same pattern as the agent's tool execution.

</details>

<details>
<summary><b>✅ Resolved Issues This Phase</b></summary>
<br>

| Issue | Fix |
|---|---|
| Per-URL failure poisoning entire summarize_text() result | Inner try/except per URL — failures skipped, partial success preserved |
| All-URLs-failed case returned no signal | `if not response:` returns distinct fallback string for downstream guard |
| Stage 2/3 errors masked as Stage 1 failures | Rule 13 added — distinct per-section handling, no shared footer |

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
User question → Gemini embedding → cosine search → top 3 chunks → LLM
```

### Complete Implementation

```python
# Setup — runs once at module load
EMBEDDING_MODEL = "gemini-embedding-001"
client = chromadb.PersistentClient(path="./data/chroma_db")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
collection = client.get_or_create_collection(name="data_storage")

# Phase 1a — PDF to chunks (paragraph-aware fixed-token chunking, Phase 4)
def ingest_pdf(file_path: str) -> list:
    file_name = os.path.basename(file_path)
    chunks = []
    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                for para in paragraphs:
                    # small paragraphs kept whole; large ones split via
                    # sliding window (CHUNK_SIZE=250, OVERLAP=50)
                    chunks.append({
                        "text": para,
                        "page_number": page_number,
                        "file_name": file_name
                    })
    return chunks

# Phase 1b — chunks to ChromaDB
def embed_and_store(new_chunks: list):
    client.heartbeat()  # verify DB connection before write
    texts = [item["text"] for item in new_chunks]
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
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

# Phase 2 — query, scoped to one document via where filter (Phase 4)
def query_rag(user_input: str, where: dict):
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[user_input]
    )
    results = collection.query(
        query_embeddings=[response.embeddings[0].values],
        where=where,
        n_results=3
    )
    return [
        {"text": text, "metadata": metadata}
        for text, metadata in zip(results["documents"][0], results["metadatas"][0])
    ]

# Phase 4 — relevance gate, decides if Stage 4 unlocks this turn
def get_available_files(user_input: str) -> str:
    unique_filenames = list(set(
        m["file_name"] for m in collection.get(include=["metadatas"])["metadatas"]
    ))
    if not unique_filenames:
        return ""
    file_list = " ".join(unique_filenames)
    if classify_document_relevance(user_input, file_list):
        return file_list
    return ""
```

<details>
<summary><b>⚙️ Key Design Decisions</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| `PersistentClient` over `Client()` | Data must survive between sessions |
| `get_or_create_collection` | Safe for repeated initialization — no crash on restart |
| `gemini-embedding-001` | `text-embedding-004` returned 404 NOT_FOUND on free tier API key — switched to stable production alternative |
| Same model for Phase 1 and Phase 2 | Different models produce different vector spaces — similarity search breaks |
| MD5 hash of chunk text as ID | Prevents duplicates even when the same PDF is renamed |
| Flat list structure for chunks | Simplifies the embedding loop — no nested iteration |
| `n_results=3` (reduced from 5) | Prevents Stage 4 RAG results from bloating self.messages and crowding out Stage 2/3 reasoning room |
| `client.heartbeat()` before write | Verifies ChromaDB connection live before ingestion — clear error instead of cryptic mid-write failure |
| pdfplumber over PyPDF2 | Better handling of complex PDF layouts like pitch decks |
| `\n\n` paragraph chunking | Each paragraph contains one complete idea — meaningful retrieval unit |
| `try/except DuplicateIDError` | Graceful duplicate handling — user gets a clear message instead of a crash |
| `if not search_response` in tool | Handles empty collection edge case before returning to agent |
| `where={"file_name": ...}` filter | Phase 4 — isolates retrieval to one document in a shared collection, no per-file collections needed |
| Paragraph-aware fixed-token chunking | Phase 4 — pure `\n\n` splitting under-chunked dense PDFs; sliding window fixes granularity while keeping small paragraphs whole |

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
| `\n\n` + fixed-token chunking | Better granularity than pure paragraph split | Still fails on tables, complex headers |
| Top-3 RAG retrieval | Covers most answers, lighter context footprint | May miss answer if it needs more chunks |
| Classifier-based relevance gating | Stops Stage 4 firing on unrelated queries | Prompt-only classification has a non-zero error rate on ambiguous phrasing |

---

## 🔮 What Changes Next (Phase 4 Remaining → Phase 5/6)

| Component | Current (v4.0.0) | Next |
|---|---|---|
| Retrieval | Vector search only | Hybrid search (BM25 + vector), then reranking |
| `context_manager.py` | In-memory list | SQLite persistent storage (Phase 6) |
| `orchestrator.py` | Single agent | Orchestrator + sub-agents (Phase 5) |
| `app.py` | CLI only | FastAPI REST endpoints (Phase 6) |
| Execution | `ThreadPoolExecutor` | `asyncio` (Phase 6) |

---

<div align="center">

<sub>BizRadar AI v4.0.0 — Architecture Document</sub>

</div>