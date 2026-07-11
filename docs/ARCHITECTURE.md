<div align="center">

# 🏗️ BizRadar AI — Architecture Deep Dive

<sub>A technical breakdown of every design decision made in BizRadar AI v4.5.0 — what was built, why it was built that way, and what tradeoffs were made.</sub>

[![Version](https://img.shields.io/badge/Version-v4.5.0-orange?style=for-the-badge)]()
[![Phase](https://img.shields.io/badge/Phase_4-Complete-brightgreen?style=for-the-badge)]()
[![Approach](https://img.shields.io/badge/Frameworks-Zero-red?style=for-the-badge)]()

</div>

---

## 🎯 Design Philosophy

<div align="center">

> *"Architecture First. Frameworks Later."*

</div>

BizRadar is intentionally built **without LangChain or LlamaIndex**. Every component a framework would abstract — the ReAct loop, tool calling, parallel execution, context management, the RAG pipeline, hybrid retrieval, reranking — is implemented manually.

**Why?**
- Understanding internals makes you a better engineer when you eventually use frameworks
- Frameworks hide bugs behind abstractions — manual code exposes them
- Provider independence — swapping Groq for another provider requires changing one file, not relearning a framework

---

## 📁 Component Map
```
bizradar-ai/
│
├── app.py                        ← CLI interface + PDF ingestion trigger
│
├── src/
│   ├── core/
│   │   ├── orchestrator.py       ← ReAct loop + stage-gated tool orchestration
│   │   └── context_manager.py    ← Sliding window memory
│   │
│   ├── tools/
│   │   ├── tools.py              ← Tool implementations (Tavily + Gemini + RAG bridge)
│   │   └── tools_description.py  ← Tool schemas for LLM function calling
│   │
│   ├── prompts/
│   │   └── prompts.py            ← SYSTEM_PROMPT, FILE_PROMPT, CLASSIFICATION_PROMPT
│   │
│   ├── rag/
│   │   ├── rag.py                ← Ingestion + hybrid retrieval + relevance classifier
│   │   └── reranker.py           ← CrossEncoder reranking layer
│   │
│   ├── config/
│   │   └── settings.py           ← Central constants (models, chunk sizes, top-K)
│   │
│   └── evaluation/
│       ├── evaluator.py          ← Recall@K RAG evaluation
│       ├── ground_truth.py       ← Semantic + hybrid-search ground-truth datasets
│       ├── classifier_evaluator.py
│       ├── classifier_ground_truth.py
│       └── datasets/             ← 12 categorized classifier benchmark datasets
│
└── data/
    ├── uploads/                  ← User-uploaded PDFs
    ├── chroma_db/                ← Persistent ChromaDB vector store (gitignored)
    └── BM25/                     ← Persistent BM25 index + corpus JSON (gitignored)
```

---

## 🔁 orchestrator.py — The ReAct Loop + Stage Gating

### What It Does
Implements the **ReAct (Reasoning + Acting)** pattern plus real stage enforcement — the core intelligence loop of BizRadar. Lives at `src/core/orchestrator.py`.

### How It Works
```
messages built → Groq API call → tool_calls in response?
│
YES ────────────┘
│
validate_stage_tools() gate
(rejects wrong-stage / batched / hallucinated calls)
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
confirms this specific question requires reading an uploaded document
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
        # validate, execute, append results, loop again
    else:
        return response_message.content  # done
```

**Why not a fixed number of iterations?**
A fixed loop either cuts off early (incomplete answer) or wastes API calls (unnecessary loops). Letting the LLM decide is more efficient and accurate — bounded by `MAX_STAGE_RETRIES = 3` per stage so a confused model can't loop forever.

---

**2. `validate_stage_tools()` — real stage enforcement**

Before Phase 4, `stage` was only a print label — it had no power to stop the LLM from calling the wrong tool or batching tools across stages. This function checks every tool call against `STAGE_MAP` *before* execution and rejects the whole batch if anything is out of place.

```python
STAGE_MAP = {
    1: ["analyze_market", "search_knowledge_base"],
    2: ["suggest_mvp", "recommend_tech_stack"],
    3: ["risk_analysis"],
    4: ["search_documents"],
}
TOOL_TO_STAGE = {tool: stg for stg, tools in STAGE_MAP.items() for tool in tools}

def validate_stage_tools(stage, tool_call_list, document_access_allowed):
    # 1. search_documents() blocked entirely if document_access_allowed is False
    # 2. every tool_call checked against STAGE_MAP[stage]
    #    - correct stage  → "Success" tool message
    #    - wrong stage     → rejected, TOOL_TO_STAGE names the correct stage
    #    - unrecognized     → rejected, hallucination guard
    # 3. missing-tool check — were ALL required tools for this stage called?
    #    (calling only one of two parallel Stage 1 tools is not enough)
    return {"valid": bool, "message": [...], "missing_tool_call": [...]}
```

Rejection is **whole-batch, not per-tool** — partially executing a batch would leave `workflow_state` inconsistently populated for that stage. Missing-tool corrections are injected as `role: "user"` messages (not `system` — one-time setup only; not `assistant` — the LLM doesn't talk to itself) so Groq reliably reads them as "new instruction, act now."

Caught a real, repeated bug: the LLM bundling `risk_analysis` + `search_documents` together in Stage 3.

---

**3. `ThreadPoolExecutor` for parallel tool execution**

```python
with ThreadPoolExecutor() as executor:
    for tool_call in tool_calls:
        future[executor.submit(function_to_call, **args)] = tool_call.id
    for completed_future in as_completed(future):
        # collect results as they finish
```

`as_completed` yields results as they finish rather than waiting for the slowest — a fast tool never blocks on a slow one. `future` is a **local variable**, not `self.future` — an instance attribute would be shared and corrupted across concurrent `run()` calls.

---

**4. `temp_list` — per-turn disposable context**

`current_files` (which uploaded filenames are relevant) can change every turn — the relevance classifier re-decides on every message. Injecting `FILE_PROMPT` directly into `self.messages[0]` would make that injection permanent and leak into unrelated future turns.

```python
length = len(self.messages)
temp_list = self.messages.copy()          # shallow copy — dicts inside are shared refs

if current_files:
    temp_list[0] = {                       # NEW dict — never mutate in place
        "role": "system",
        "content": SYSTEM_PROMPT + "\n\n" + file_prompt,
    }

# ReAct loop runs entirely on temp_list, never self.messages directly
...

self.messages.extend(temp_list[length:])   # only the NEW turns persist
```

`self.messages[0]` stays the static `SYSTEM_PROMPT` for the entire session, guaranteed. The critical detail: `temp_list[0] = {...}` (new dict) vs. `temp_list[0]["content"] = X` (in-place mutation of a shared reference) — the latter would silently corrupt `self.messages[0]` too, since `.copy()` on a list of dicts only copies the outer list.

---

**5. Forced argument overwrite**

```python
if function_name in ["suggest_mvp", "recommend_tech_stack"]:
    function_args["startup_idea"] = workflow_state["user_query"]
    function_args["market_context"] = (
        workflow_state["stage_1"]["analyze_market"][:1000]
        + "\n\n" + workflow_state["stage_1"]["search_knowledge_base"][:1000]
    )
```

Earlier versions let the LLM construct `market_context`/`mvp_context`/`startup_idea` itself — it would sometimes hallucinate plausible-looking context instead of using real upstream output. Overwriting these three keys in code, immediately before execution, removes that failure mode entirely: the LLM still decides *when* to call a tool, never *what context* it receives for these specific keys.

---

**6. Provider-specific exception handling**

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
Stores conversation history and returns the last 6 turns to the agent on each run. Lives at `src/core/context_manager.py`.

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

**`self.context_loaded` guard** — `get_context()` runs exactly once per `StartupAgent` session, on the first `run()` call. Without this, every follow-up turn would reload and re-append the same history, duplicating it.

**Current limitation:** memory resets on process exit — no disk persistence. Planned for Phase 6 via SQLite.

</details>

---

## 🛠️ tools.py — The Tool Layer

### Architecture
```
User Input
↓
analyze_market()        ← Tavily live web search, self-summarizes before returning
search_knowledge_base() ← Tavily deep search, self-summarizes before returning
suggest_mvp()            ← Gemini 2.5 Flash prompt
recommend_tech_stack()   ← Gemini 2.5 Flash prompt
risk_analysis()           ← Gemini 2.5 Flash prompt, feature-by-feature risk breakdown
search_documents()       ← Hybrid RAG retrieval — Stage 4, on-demand
Internal only (not LLM-callable):
summarize_text()          ← called inside analyze_market() and search_knowledge_base()
before they return — LLM never sees this directly
```

<details>
<summary><b>⚙️ Key Design Decisions</b></summary>
<br>

**1. Per-tool dedicated Gemini clients**

```python
gemini_analyze_client          = genai.Client(api_key=GEMINI_API_KEY_7)  # analyze_market
gemini_search_knowledge_client = genai.Client(api_key=GEMINI_API_KEY_9)  # search_knowledge_base
gemini_mvp_client               = genai.Client(api_key=GEMINI_API_KEY_3)  # suggest_mvp
gemini_tech_stack_client        = genai.Client(api_key=GEMINI_API_KEY_4)  # recommend_tech_stack
gemini_risk_client               = genai.Client(api_key=GEMINI_API_KEY_5)  # risk_analysis
```

Free-tier Gemini quotas are per-key. Stage 1 alone can fire several parallel Gemini summarization calls — funneling everything through one key risks exhausting it and stalling the entire pipeline. Spreading calls across dedicated keys per tool reduces (doesn't eliminate) that risk.

---

**2. `summarize_text()` — internal-only, parallel summarization**

```python
with ThreadPoolExecutor() as executor:
    future = {}
    for url in message:
        future[executor.submit(_call_gemini_with_retry, prompt)] = url
        time.sleep(25)   # partial RPM throttle — Stage 1's two tools run in parallel,
                          # each firing up to 3 Gemini calls; unthrottled that's 6
                          # simultaneous calls against a 5 RPM free-tier limit
    for complete_future in as_completed(future):
        try:
            result = complete_future.result(timeout=60)
            response += f"Title: ...\nSummary: {result.text}\nURL: {url}\n\n"
        except Exception:
            continue   # skip failed URLs individually — never poison the whole batch
```

Not LLM-callable — earlier versions had the LLM construct nested JSON from raw Tavily results, which broke on special characters in real web content (`\xa0`, smart quotes, em-dashes). Moving summarization fully internal eliminated that fragility category entirely, rather than patching it with character replacement.

---

**3. `search_documents()` — thin bridge to the RAG pipeline**

```python
def search_documents(user_input: str, file_name: str) -> str:
    search_response = query_rag(user_input=user_input, where={"file_name": file_name})
    if not search_response:
        return "No data found in document store."

    formatted = ""
    for chunk in search_response:
        page, fname = chunk["metadata"]["page_number"], chunk["metadata"]["file_name"]
        formatted += f"[Page {page}, {fname}]: {chunk['text'][:300]}\n\n"
    return formatted
```

Intentionally thin — all retrieval logic (vector search, BM25, fusion, reranking) lives in `rag.py`. This keeps `tools.py` a clean dispatch layer and lets `rag.py` be tested and evolved independently.

</details>

---

## 🗄️ rag.py — The Hybrid RAG Pipeline

### What It Does
Ingests PDFs, embeds and stores them for semantic search, maintains a parallel BM25 lexical index, fuses both retrieval signals, and reranks the result with a CrossEncoder. Lives at `src/rag/rag.py`.

### The Problem It Solves
BizRadar's early agent produced a citation that was never in Tavily's results — pure LLM fabrication from training memory. RAG solves document-grounding the same way: constrain the LLM to answer only from retrieved, reranked chunks.

### Three-Phase Architecture
```
PHASE 1 — Ingestion (runs once per document)
PDF → pdfplumber → paragraph-aware sliding-window chunks
→ Gemini embeddings → ChromaDB
→ build_bm25_index() → BM25 index + corpus JSON (disk-persisted)
PHASE 2 — Hybrid Retrieval (runs every query)
User question
├─→ vector_retrieve()  → ChromaDB cosine search → top-10, distance-scored
└─→ bm25_retrieve()    → BM25 lexical search    → top-10, BM25-scored
│
▼
Score Fusion (min-max normalize BM25, vector_sim = 1 - distance)
final = (0.5 × vector_sim) + (0.5 × bm25_normalized)
│
▼
PHASE 3 — Reranking
CrossEncoder (BAAI/bge-reranker-v2-m3) reranks fused top-10 → top-3
│
▼
Returned to LLM with page/filename citations
```
### Ingestion — Chunking

```python
CHUNK_SIZE = 250
OVERLAP    = 50
STEP       = CHUNK_SIZE - OVERLAP   # 200

for page_number, page in enumerate(pdf.pages, start=1):
    paragraphs = [p.strip() for p in page.extract_text().split("\n\n") if p.strip()]
    for paragraph_text in paragraphs:
        words = paragraph_text.split()
        if len(words) <= CHUNK_SIZE:
            # small paragraph — one complete idea, kept whole
            chunks.append({"text": paragraph_text, "page_number": ..., "file_name": ...})
        else:
            # large paragraph — sliding window with overlap so no idea is
            # fully lost at a window cut point
            left, right = 0, CHUNK_SIZE
            while left < len(words):
                window_text = " ".join(words[left:right])
                if len(window_text.split()) < MIN_CHUNK_WORDS:
                    break   # skip tiny trailing chunks
                chunks.append({"text": window_text, ...})
                left += STEP; right += STEP
```

Replaced pure `\n\n` splitting, which under-chunked dense PDFs badly — a 2-page report with few paragraph breaks could produce only 2 total chunks for the *entire document*, destroying retrieval granularity.

### Retrieval — Vector + BM25 + Fusion

```python
def vector_retrieve(user_input: str, where: dict) -> list:
    response = gemini_client_1.models.embed_content(model=EMBEDDING_MODEL, contents=[user_input])
    results = collection.query(
        query_embeddings=[response.embeddings[0].values],
        where=where,
        n_results=DEFAULT_VECTOR_TOP_K,   # 10
        include=["documents", "metadatas", "distances"],
    )
    return [{"text": t, "metadata": m, "distance": d}
            for t, m, d in zip(results["documents"][0], results["metadatas"][0], results["distances"][0])]

def bm25_retrieve(user_query: str, top_k: int) -> dict:
    query_tokens = bm25s.tokenize(user_query)
    result, score = bm25_index.retrieve(query_tokens, k=top_k)
    return {bm25_corpus[result[0][k]]['text']: {**bm25_corpus[result[0][k]], 'score': score[0][k]}
            for k in range(top_k)}

def query_rag(user_input: str, where: dict) -> list:
    vector_chunks = vector_retrieve(user_input, where)
    bm25_chunks   = bm25_retrieve(user_input, DEFAULT_VECTOR_TOP_K)
    bm25_chunks   = {t: c for t, c in bm25_chunks.items() if c['file_name'] == where['file_name']}

    # vector_sim = 1 - distance (ChromaDB gives distance, we want similarity)
    for chunk in vector_chunks:
        chunk['vector_sim'] = 1 - chunk['distance']

    # BM25 scores min-max normalized to [0, 1] within this query's candidate set
    scores = [c['score'] for c in bm25_chunks.values()]
    min_s, max_s = min(scores, default=0), max(scores, default=0)
    for chunk in bm25_chunks.values():
        chunk['normalized'] = (chunk['score'] - min_s) / (max_s - min_s) if max_s != min_s else 1

    # Fusion — chunks found by only one retriever get 0 for the missing half,
    # not skipped, so single-method hits still surface
    alpha = 0.5
    unified = {}
    for chunk in vector_chunks:
        bm25_norm = bm25_chunks.get(chunk['text'], {}).get('normalized', 0)
        chunk['fusion_score'] = (alpha * chunk['vector_sim']) + ((1 - alpha) * bm25_norm)
        unified[chunk['text']] = chunk
    for text, chunk in bm25_chunks.items():
        if text in unified:
            continue
        chunk['fusion_score'] = (1 - alpha) * chunk['normalized']
        chunk['metadata'] = {"page_number": chunk["page_number"], "file_name": chunk["file_name"]}
        unified[text] = chunk

    return rerank(query=user_input, retrieved_chunks=list(unified.values()), top_k=DEFAULT_RERANK_TOP_K)
```

### Document Relevance Classifier

```python
def get_available_files(user_input: str) -> str:
    unique_filenames = sorted({m["file_name"] for m in collection.get(include=["metadatas"])["metadatas"] if m})
    if not unique_filenames:
        return ""   # nothing ingested — skip the classifier call entirely, no wasted Gemini call

    if classify_document_relevance(user_input, " ".join(unique_filenames)):
        return "\n".join(unique_filenames)
    return ""
```

`classify_document_relevance()` is a dedicated, `temperature=0.0` Gemini call using `CLASSIFICATION_PROMPT` (centralized in `prompts.py`) whose only job is a binary decision — does *this specific query* require reading the uploaded documents? This closes a gap where the main LLM would call `search_documents()` just because filenames were visible to it, regardless of whether the question actually needed them.

### Dynamic Gemini API Pool

```python
api_pool = [{"client": genai.Client(api_key=key), "cooldown_until": 0.0, "failures": 0} for key in GEMINI_API_KEYS]

def get_next_available_client() -> tuple[int, genai.Client]:
    for _ in range(MIN_COOLTIME_RETRY):          # bounded retry — won't hang forever
        current_time = time.time()               # refreshed every loop iteration
        for offset in range(len(api_pool)):
            index = (_current_api_index + offset) % len(api_pool)
            if current_time >= api_pool[index]["cooldown_until"]:
                return index, api_pool[index]["client"]
        min_wait = min(s["cooldown_until"] for s in api_pool) - time.time()
        time.sleep(max(0, min_wait))              # sleep exactly until the soonest key frees up
    raise RuntimeError("All Gemini API keys are currently in cooldown.")

def mark_api_failed(api_index: int) -> None:
    state = api_pool[api_index]
    state["failures"] += 1
    state["cooldown_until"] = time.time() + min(300, 60 * (2 ** (state["failures"] - 1)))  # exponential, capped
```

`current_time` is deliberately re-read **inside** the retry loop — an earlier version captured it once outside the loop and went stale immediately after any `time.sleep()`, causing incorrect availability checks.

<details>
<summary><b>⚙️ Key Design Decisions</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| `PersistentClient` over `Client()` | Vector data must survive between sessions |
| `gemini-embedding-001` | `text-embedding-004` returned 404 on free-tier keys — switched to a stable production alternative |
| Same embedding model for ingestion and query | Different models produce different vector spaces — similarity search breaks otherwise |
| MD5 hash of chunk text as ChromaDB ID | Prevents duplicate storage even when the same PDF is renamed and re-uploaded |
| `where={"file_name": ...}` filter | Isolates retrieval to one document in a shared collection — no per-file collections needed |
| BM25 full rebuild on every ingestion | BM25's IDF scoring is not incrementally updatable — a partial index produces mathematically wrong scores |
| BM25 index + corpus persisted to disk | Global Python variables reset on every process restart — without persistence, BM25 silently returns nothing after a restart |
| `DEFAULT_VECTOR_TOP_K=10` → `DEFAULT_RERANK_TOP_K=3` | Retrieve wide for recall, rerank narrow for precision — a CrossEncoder is too slow to run over the whole collection but very effective on a small candidate pool |
| `alpha=0.5` fusion weight | Equal trust in lexical and semantic signal — no corpus-specific tuning done yet |
| Min-wait sleep in `get_next_available_client()` | Sleeping a fixed guess wastes time or under-waits; computing the actual minimum cooldown across the pool sleeps exactly as long as needed |

</details>

---

## 🎯 reranker.py — CrossEncoder Precision Layer

### What It Does
Reranks a candidate pool retrieved by fusion (recall-oriented) into a precision-ordered top-K, using `BAAI/bge-reranker-v2-m3`. Lives at `src/rag/reranker.py`.

### Why It Exists
Embedding/BM25 fusion is optimized for **recall** — is the right chunk *somewhere* in the top 10? A CrossEncoder jointly evaluates the query and each candidate chunk together (rather than comparing precomputed vectors independently), which is far more expensive per-comparison but dramatically better at **precision** — is the right chunk at position 1?

```python
def rerank(query: str, retrieved_chunks: list[dict], top_k: int) -> list[dict]:
    sentence_pairs = [(query, chunk["text"]) for chunk in retrieved_chunks]
    scores = reranker.predict(sentence_pairs, convert_to_numpy=True)
    for chunk, score in zip(retrieved_chunks, scores):
        chunk["rerank_score"] = float(score)
    retrieved_chunks.sort(key=lambda c: c["rerank_score"], reverse=True)
    return retrieved_chunks[:top_k]
```

<details>
<summary><b>⚙️ Key Design Decisions</b></summary>
<br>

| Decision | Reasoning |
|---|---|
| Rerank *after* fusion, not instead of it | CrossEncoder over the full collection would be far too slow; running it only on the fused top-10 keeps latency bounded |
| `BAAI/bge-reranker-v2-m3` | Strong open-weight cross-encoder with good multilingual + long-context behavior for this use case |
| `reranker.model.eval()` at load time | Explicit inference mode — disables dropout/batchnorm training behavior |
| Expected gains: Recall@1 ↑, Recall@3 ≈ unchanged | Reranking reorders an already-correct candidate set — it can't retrieve a chunk that fusion missed entirely, but it can promote the right one to position 1 |

</details>

---

## 📋 tools_description.py — Tool Schemas

### What It Does
Defines the JSON schema for each tool so the LLM knows what the tool is called, what it does, what parameters it accepts, and which are required. Lives at `src/tools/tools_description.py`.

### Why This File Exists Separately
Tool schemas are configuration, not logic — keeping them separate means `orchestrator.py` stays clean, schemas can be updated without touching tool logic, and every tool interface is auditable in one place.

### How Description Quality Affects Tool Selection
```
❌ Vague:   "searches the web"
✅ Precise: "Analyzes market potential, competition, and trends for a startup
idea by performing a live web search. Always call in Stage 1,
in parallel with search_knowledge_base()."
❌ Vague:   "searches documents"
✅ Precise: "Call this tool as Stage 4 — ONLY after Stages 1, 2, and 3 have
all completed. Trigger ONLY when the user explicitly references
an uploaded file, pitch deck, document, or attachment."
```
Every tool description includes explicit cross-stage prohibitions ("Do not call in this stage") — vague descriptions were the direct cause of stage-bundling bugs before `validate_stage_tools()` and precise schema language closed the gap together.

---

## 📝 prompts.py — System Prompt Design

### Structure
Lives at `src/prompts/prompts.py`. Five constants:

1. **`SYSTEM_PROMPT`** — role, 13 numbered rules, chain-of-thought block, `TOOL CALL ORDER` (all 4 stages), output format, limitations
2. **`USER_PROMPT_TEMPLATE`** — minimal wrapper for the user's raw question
3. **`FILE_PROMPT`** — formatted per-turn with live filenames, injected into `temp_list[0]` only when files are relevant
4. **`CLASSIFICATION_PROMPT`** — the document-relevance classifier's full instruction set, centralized here in Phase 4 (previously inline in `rag.py`)

### Key Design Decision — Rule 9
Every market claim MUST be backed by a cited URL from tool results.
No URL = no claim.
Forces the LLM to use Tavily's URLs as citations, reducing hallucination and increasing credibility of the final report.

### Key Design Decision — Rules 12 vs 13
Two failure-handling rules, deliberately scoped to different tiers:
- **Rule 12** — fires only if **both** Stage 1 tools fail. Triggers a full disclaimer footer on the report.
- **Rule 13** — fires for any Stage 2/3 tool failure. Notes the specific section as unavailable, does **not** trigger the Rule 12 footer.

Earlier versions conflated these — a Stage 2/3 failure would incorrectly trigger the Stage 1 disclaimer, masking a genuinely successful Stage 1 result.

---

## ⚖️ Tradeoffs & Known Limitations

| Decision | Benefit | Tradeoff |
|---|---|---|
| Groq over local Ollama | 10x faster inference | Requires internet + API key |
| `ThreadPoolExecutor` over `asyncio` | Simpler code, works with sync libraries | Not truly async, GIL-limited |
| In-memory conversation context | Zero setup, fast | Lost on process exit |
| No framework | Deep understanding | More boilerplate code |
| Gemini for analysis tools | High quality output | Additional API dependency |
| Paragraph-aware sliding-window chunking | Better granularity than pure `\n\n` split | Still struggles with tables, complex multi-column headers |
| `DEFAULT_RERANK_TOP_K=3` | Covers most answers, lighter context footprint | May miss an answer that genuinely needs more than 3 chunks |
| CrossEncoder reranking | Meaningfully better precision at rank 1 | Adds latency — must run on a bounded candidate pool, not the full collection |
| Hybrid search (BM25 + vector) | Combines lexical exactness with semantic recall | On a small corpus (~25 chunks), BM25 shows little discrimination advantage — benefit scales with corpus size |
| `alpha=0.5` fixed fusion weight | Simple, no tuning required | Not corpus- or query-adaptive; a future version could learn or adjust this per query type |
| Multi-key Gemini pool with exponential cooldown | Reduces single-key quota bottlenecks | Adds pool-management complexity; still hard-fails if *every* key is simultaneously exhausted |
| Classifier-based document relevance gating | Stops Stage 4 firing on unrelated queries | Prompt-only classification has a non-zero, irreducible error rate on genuinely ambiguous phrasing (e.g. bare pronouns) |

---

## 🔮 What Changes Next (Phase 5 → Phase 6)

| Component | Current (v4.5.0) | Next |
|---|---|---|
| Agent architecture | Single agent, ReAct + stage gating | Orchestrator + specialized sub-agents (Phase 5) |
| Retrieval | Hybrid (BM25 + vector) + CrossEncoder rerank | Adaptive fusion weighting, larger-corpus validation |
| `context_manager.py` | In-memory list | SQLite persistent storage (Phase 6) |
| `app.py` | CLI only | FastAPI REST endpoints (Phase 6) |
| Execution | `ThreadPoolExecutor` | `asyncio` (Phase 6) |
| Relevance classification | Single-shot prompt classifier | Structural safety net — retrieval-similarity second opinion (deferred) |

---

<div align="center">

<sub>BizRadar AI v4.5.0 — Architecture Document | Phase 4 Complete</sub>

</div>