# Changelog

All notable changes to CoFoundr AI are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## 📑 Table of Contents

- [v5.9.0 — Phase 5 Closure](#v590--2026-08-28--phase-5-closure)
- [Unreleased / Deferred](#unreleased--deferred)
- [v5.8.0 — Provider Hardening, API-Key Rotation & Integration Verification](#v580--2026-08-27--provider-hardening-api-key-rotation--integration-verification)
- [v5.7.0 — LLM Judge & Workflow Validation](#v570--2026-08-27--llm-judge--workflow-validation)
- [v5.6.0 — Report Writing & PDF Generation](#v560--2026-08-27--report-writing--pdf-generation)
- [v5.5.0 — Nurturing, Advancement & General Chat](#v550--2026-08-27--nurturing-advancement--general-chat)
- [v5.4.0 — Recommendations & Idea Generation](#v540--2026-08-27--recommendations--idea-generation)
- [v5.3.0 — Risk Analysis & Startup Scoring](#v530--2026-08-27--risk-analysis--startup-scoring)
- [v5.2.0 — MVP & Technology Advisors](#v520--2026-08-27--mvp--technology-advisors)
- [v5.1.0 — Research & Retrieval Agents](#v510--2026-08-27--research--retrieval-agents)
- [v5.0.0 — Multi-Agent Foundation](#v500--2026-08-27--multi-agent-foundation)
- [v4.5.0 — Phase 4 Closure: Debugging & Hardening](#v450--2026-06-27--phase-4-closure-debugging--hardening)
- [v4.4.0 — Hybrid Search, Reranking & Dynamic API Pool](#v440--2026-06-25--hybrid-search-reranking--dynamic-api-pool)
- [v4.3.0 — Chunking Rework & RAG Evaluation Suite](#v430--2026-06-22--chunking-rework--rag-evaluation-suite)
- [v4.2.0 — Document Relevance Classifier](#v420--2026-06-21--document-relevance-classifier)
- [v4.1.0 — Stage Gating Enforcement](#v410--2026-06-20--stage-gating-enforcement)
- [v4.0.0 — Multi-PDF Isolation](#v400--2026-06-19--multi-pdf-isolation)
- [v3.6.0 — Phase 3 Closure, RAG Integration & CLI Rewrite](#v360--2026-06-14--phase-3-closure-rag-integration--cli-rewrite)
- [v3.5.0 — Pipeline Verified & RAG Citation Fix](#v350--2026-06-13--pipeline-verified--rag-citation-fix)
- [v3.4.0 — summarize_text Architecture Refactor](#v340--2026-06-12--summarize_text-architecture-refactor)
- [v3.3.0 — Phase 3 Pipeline Debugging & Stage Enforcement](#v330--2026-06-11--phase-3-pipeline-debugging--stage-enforcement)
- [v3.2.0 — Agent Scoping Fixes & Prompt Pipeline](#v320--2026-06-10--agent-scoping-fixes--prompt-pipeline)
- [v3.1.0 — Tool Context & Exception Fixes](#v310--2026-06-09--tool-context--exception-fixes)
- [v3.0.0 — Phase 3 Complete](#v300--2026-06-08--phase-3-complete)
- [v2.0.0 — Phase 2 Complete](#v200--2026-06-07--phase-2-complete)
- [v1.0.0 — Phase 1 Complete](#v100--2026-06-01--phase-1-complete)

---

## [v5.9.0] — 2026-08-28 — Phase 5 Closure

### Changed
- **Phase 5 status:** moved from active development to **closed**.
- **Release state:** transitioned from implementation-complete to formally verified and release-ready.
- **Project identity:** documentation standardized on **CoFoundr AI**.

### Verified
- Final Phase 5 integration verification completed against the existing implementation.
- **7/7 intent workflows passed:**
  - `general_chat`
  - `full_analysis`
  - `partial_idea`
  - `idea_exploration`
  - `nurturing`
  - `advancement`
  - `pdf_request`
- Final `full_analysis` run completed with **0 workflow errors**.
- Expected and actual intent matched for the final `full_analysis` verification.
- Error-aware test reporting confirmed the successful run contained no recorded agent failures.
- Phase 5 functional release status: **READY**.

#### Key Insight
> Phase 5 is closed only after the existing implementation passes complete intent verification with zero recorded errors.

---

## Unreleased / Deferred

Every item explicitly punted to a future phase, consolidated here so nothing stays buried inside an old version entry.

| Item | Originally Logged | Target |
|---|---|---|
| Multi-agent orchestration (specialist sub-agents) | v4.0.0 | ✅ Complete — Phase 5 |
| FastAPI REST service layer | v3.0.0 | Phase 6 |
| SQLite persistent conversation history | v1.0.0 | Phase 6 |
| `embed_and_store()` per-chunk upsert (currently fails whole batch on any duplicate ID) | v3.5.0 | Backlog |
| `task_type` parameter (`RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY`) for `embed_content()` calls | v3.5.0 | Backlog |
| Retrieval relevance/chunking drift — correct theme retrieved, details paraphrase loosely | v4.0.0 | Backlog — needs multi-turn RAG design, not a quick fix |
| DS-033 bare-pronoun classifier limitation ("Explain it.") | v4.2.0 | Permanently deferred — documented architectural limitation, not a bug |
| Stage 2/3 context truncated to 1000 chars at injection (on top of 2000-char storage truncation) | v4.0.0 | Deferred to post-persistence work |
| `search_documents()`'s `file_name` argument is LLM-trusted, not validated against live file list | v4.0.0 | Deferred until `get_available_files()` supports multi-doc summary-based selection |
| Deterministic retry-forcing stress test for `MAX_STAGE_RETRIES` | v4.0.0 | **Formally dropped** in v4.5.0 — see below |

---

## [v5.8.0] — 2026-08-27 — Provider Hardening, API-Key Rotation & Integration Verification

### Added
- **Generic API-key rotation** — added `src/core/key_rotator.py` as a provider-agnostic utility used by provider tools.
- **Stateful provider rotation** — `GroqTool` and `GeminiTool` maintain rotation state at the tool-instance level across retry attempts.
- **Provider tool instances** — affected agents now consume shared `groq_tool` / `gemini_tool` instances instead of creating provider clients directly.
- **OpenRouter reasoning path** — migrated the large-context reasoning workload from Groq to OpenRouter using `openai/gpt-oss-120b`.
- **Structured provider outputs** — refined structured response handling for recommendations, mid-judge, final-judge, and startup-scoring workflows.
- **Integration test coverage** — added focused validation for `general_chat`, `full_analysis`, `partial_idea`, `idea_exploration`, `nurturing`, `advancement`, and `pdf_request`.

### Changed
- Large workflow contexts no longer depend exclusively on Groq's previous input-context limits; OpenRouter now handles the large-context reasoning workload.
- Provider-specific request construction remains inside provider tools, keeping agent logic independent of SDK details.
- Workflow failures are recorded in `workflow_state["errors"]` and failed agents are reflected in pipeline status.
- Test success criteria now require the expected intent and zero recorded workflow errors.

### Fixed
- API-key rotation logic is shared rather than duplicated across provider tools.
- Provider consumers were migrated to shared tool instances across the affected agent files without changing agent responsibilities.
- Structured-output request construction was corrected so prompts/messages and response schemas are passed separately.
- Error handling now preserves workflow state after handled agent failures instead of hiding the failure from downstream validation.

### Verified
- All seven Phase 5 intent workflows passed focused integration verification:
  - `general_chat`
  - `full_analysis`
  - `partial_idea`
  - `idea_exploration`
  - `nurturing`
  - `advancement`
  - `pdf_request`
- Final `full_analysis` verification: expected `full_analysis`, actual `full_analysis`, **PASS**, errors `0`.
- `pdf_request` verification: **PASS**.
- Phase 5 functional verification: **7/7 intent paths passed**.

#### Key Insight
> Provider abstraction should isolate provider failures and credentials from agent logic. Rotation belongs in the tool layer, not duplicated across agents.

---

## [v5.7.0] — 2026-08-24 — LLM Judge & Workflow Validation

### Added
- `LLMJudgeAgent` for evaluating workflow output at validation checkpoints.
- Structured judge responses containing `judgment`, `reason`, and `issues`.
- PASS/WARNING/FAIL validation for workflow quality.
- Mid-pipeline and final validation checkpoints integrated into the workflow.

### Verified
- Judge output is consumed as workflow validation data rather than being treated as an independent report-generation path.
- Validation remains separate from specialist-agent responsibilities.

---

## [v5.6.0] — 2026-08-23 — Report Writing & PDF Generation

### Added
- `ReportWriterAgent` for assembling completed specialist outputs into the final structured startup report.
- `PDFGeneratorAgent` for converting the completed report into a PDF artifact.
- Report generation consumes workflow outputs rather than performing independent research.
- PDF generation remains an output/formatting layer after report assembly.

### Changed
- Report-generation responsibilities were separated from research and analysis agents.
- Final report assembly preserves upstream workflow evidence instead of inventing replacement data.

---

## [v5.5.0] — 2026-08-22 — Nurturing, Advancement & General Chat

### Added
- `NurturingAgent` for startup-development and follow-up guidance workflows.
- `AdvancementAgent` for advancement/scaling-oriented workflows.
- `GeneralChatAgent` for non-analysis conversational requests.
- Dedicated intent paths for nurturing, advancement, and general-chat requests.

### Changed
- General conversation no longer needs to enter the full startup-analysis workflow.
- Specialist responsibilities remain isolated behind the orchestrator.

---

## [v5.4.0] — 2026-08-21 — Recommendations & Idea Generation

### Added
- `RecommendationAgent` for evidence-based startup improvement recommendations.
- `IdeaGenerationAgent` for startup opportunity and idea-exploration workflows.
- Structured recommendation outputs based on upstream workflow evidence.

### Changed
- Generated opportunities are grounded in available market/workflow signals rather than isolated model assumptions.

---

## [v5.3.0] — 2026-08-20 — Risk Analysis & Startup Scoring

### Added
- `RiskAnalystAgent` for structured startup risk analysis.
- `StartupScorerAgent` for startup viability scoring.
- Structured score breakdown covering market, MVP, technology, and risk dimensions.
- Highest-risk identification in scoring output.

### Changed
- Risk and scoring agents consume upstream workflow outputs through the shared state instead of directly depending on other agents.

---

## [v5.2.0] — 2026-08-19 — MVP & Technology Advisors

### Added
- `MVPAdvisorAgent` for MVP feature recommendations.
- `TechAdvisorAgent` for architecture and technology-stack recommendations.
- Structured outputs for MVP scope and technology decisions.

### Changed
- Advisor agents read upstream context from `workflow_state` while remaining independently callable and testable.

---

## [v5.1.0] — 2026-08-18 — Research & Retrieval Agents

### Added
- `MarketResearchAgent` for market and competitor research.
- `WebSearchAgent` for web-search-backed research workflows.
- `RAGAgent` for document-grounded retrieval using the existing hybrid RAG pipeline.
- Shared workflow-state outputs for downstream specialist agents.

### Changed
- Existing Phase 4 retrieval capabilities were wrapped behind a dedicated RAG specialist rather than being owned by the central agent.
- Research responsibilities were separated into independently testable specialist agents.

---

## [v5.0.0] — 2026-08-17 — Multi-Agent Foundation

### Added
- `workflow_state.py` shared communication schema for agent-to-agent handoffs.
- `OrchestratorAgent` for coordinating specialist agents.
- `IntentRouterAgent` for selecting the workflow path from user intent.
- Provider tool layer for Tavily, ChromaDB, Gemini, Groq, BM25, and PDF operations.
- `core/exceptions.py` and `core/decorators.py` for shared error handling and cross-cutting concerns.
- Centralized Phase 5 prompts and mock workflow-state fixtures.

### Changed
- Reorganized the application around independent specialist agents communicating only through `workflow_state`.
- Kept tools independent from agents and provider SDK details isolated inside tool modules.
- Established Phase 5's zero-framework architecture: no LangChain, CrewAI, or AutoGen.

#### Key Insight
> Phase 5 changes the unit of architecture from one tool-calling agent to a coordinated team of specialized agents.

---

## [v4.5.0] — 2026-06-27 — Phase 4 Closure: Debugging & Hardening

**Phase 4 is now fully closed.** This release is the debugging/stabilization pass across everything built in v4.0.0–v4.4.0 — every previously open bug is resolved, deferred with a stated reason, or reclassified. No new features; hardening only.

### Fixed
- `bm25_retrieve()` returned a `list`, but `query_rag()` called `.items()` on it expecting a `dict` — type mismatch caused a hard crash on every hybrid query. Changed `bm25_retrieve()` to return a dict keyed by chunk text.
- BM25 index was `None` on every evaluator/app restart — the in-memory `bm25_corpus`/`bm25_index` are plain Python globals and reset on process exit. Added `.save()` after every `build_bm25_index()` call and `.load()` + JSON corpus reload at module import.
- Rebuilding BM25 against an empty ChromaDB collection crashed inside `bm25s.tokenize()` on an empty corpus. Added an `if not bm25_corpus` guard before rebuild.
- `bm25_corpus` rebuild-from-ChromaDB condition was inverted — it printed "using cached corpus" in exactly the case it should have rebuilt. Condition flipped.
- Only 25 chunks appeared after a fresh `chroma_db/` delete + re-ingest — stale chunks from the *old* (pre-Phase-4) chunker were still cached in the BM25 corpus JSON on disk. Deleted both `chroma_db/` and `data/BM25/` and re-ingested clean.
- Duplicate `import os` in `rag.py` left over from the BM25 additions — removed.
- `CLASSIFICATION_PROMPT.format()` raised `KeyError` — the format string used `{filnames}`, the call site passed `filenames`. Typo fixed.
- BM25-only retrieved chunks (no matching vector hit) were missing the `metadata` key expected by the reranker and citation formatter — BM25 stores `page_number`/`file_name` as flat top-level keys, not nested under `metadata`. Added an explicit `chunk['metadata'] = {...}` construction step before adding BM25-only chunks to the unified candidate pool.
- Vector-only chunk fusion referenced `chunk['normalized']`, a key that only exists on BM25-sourced chunks — `KeyError` on any chunk found by vector search alone. Changed the fusion formula for vector-only chunks to `(alpha × vector_sim) + ((1 - alpha) × 0)`.
- **DS-008** — classifier returned `FALSE` for "Summarize the uploaded pitch deck" when it should return `TRUE`. Root cause: domain vocabulary gap — startup-specific document terms (pitch deck, term sheet, investor deck) weren't represented in the classifier's TRUE examples. Added a dedicated startup-document vocabulary block to `CLASSIFICATION_PROMPT`.
- **DQA-015, DQA-024** — classifier returned `FALSE` for implicit structural references ("What does the methodology section describe?", "Compare the introduction and conclusion.") that don't name a document explicitly. Added an instruction: infer document relevance from structural section language even without an explicit "uploaded"/"attached" keyword.

### Changed
- Rate-limit retry logic in `get_next_available_client()` — added an outer retry loop bounded by `MIN_COOLTIME_RETRY = 3`. On an all-keys-cooldown state, the function now computes the *minimum* remaining cooldown across the entire pool and sleeps exactly that long (not a fixed guess), then retries. `current_time` is now refreshed inside the loop on every iteration — the prior version captured it once outside the loop, so it went stale immediately after any `time.sleep()` call.
- `classify_document_relevance()`'s ~100-line prompt moved out of `rag.py` inline code and centralized as `CLASSIFICATION_PROMPT` in `prompts.py` — matches the existing convention that `prompts.py` is the single source of truth for every LLM-facing prompt string.

### Verified
- Classifier benchmark re-run across all 12 category datasets post-fix — per-category isolated accuracy now 95–100%.
- The previously alarming **29.58%** full-benchmark-run accuracy figure was root-caused to **test infrastructure contamination** (shared mutable state bleeding between sequential dataset runs in `classifier_evaluator.py`), not an actual classifier regression. Per-category isolated runs were correct throughout; only the aggregate full-run number was misleading.
- Hybrid retrieval (`query_rag()`) re-run end-to-end after all fixes above — zero crashes across 25 `HS_ALL_QUESTIONS` hybrid ground-truth queries and 25 `ALL_QUESTIONS` semantic queries.

### Reclassified
- The Groq TPD rate-limit error observed in earlier sessions was formally reclassified from "possible `temp_list` architecture defect" to **billing/quota constraint** — moved out of the open-bugs table entirely; it is not a code issue.
- Citation bug ("From Your Pitch Deck" missing page/filename) and Bug B Part 2 (Competitor Insights citation leak) — both re-verified live against the current forced-argument-overwrite architecture and confirmed **already fixed**; closed out of the open-bugs table.

### Dropped
- The deterministic `MAX_STAGE_RETRIES` stress test, designed across three prior sessions but never built, is **formally dropped** — inspection confirmed `temp_list` only ever accumulates a `"completed"` placeholder string per tool call, not raw tool output, so unbounded context growth was never actually possible. Closing this out rather than letting it carry over a fourth time.

#### Key Insight
> A failing aggregate metric and a failing system are not the same thing. The 29.58% number looked like a five-alarm regression until isolated per-category runs showed 95–100% — the bug was in the *test harness*, not the *classifier*. Always isolate before trusting an aggregate.

---

## [v4.4.0] — 2026-06-25 — Hybrid Search, Reranking & Dynamic API Pool

### Added
- **Hybrid Search (BM25 + Vector)** — `build_bm25_index(new_chunks)` in `rag.py` appends new chunks to the in-memory `bm25_corpus` (keyed by chunk text), rebuilds the full BM25 index from the *complete* corpus (BM25's IDF scoring is not incrementally updatable — a partial rebuild produces mathematically wrong scores), and persists both the index and the corpus JSON to disk. Called automatically inside `embed_and_store()` immediately after `collection.add()` succeeds.
- `bm25_retrieve(user_query, top_k)` — tokenizes the query and returns the top-k lexical matches with raw BM25 scores attached.
- `vector_retrieve()` — extracted as its own function from the old monolithic `query_rag()`, isolating the ChromaDB embed + query call for independent testing.
- **Score Fusion** — rewritten `query_rag()` now orchestrates both retrievers: vector distance is converted to `vector_sim = 1 - distance`; BM25 raw scores are min-max normalized to 0–1; final fused score is `(0.5 × vector_sim) + (0.5 × bm25_normalized)`.
- **CrossEncoder Reranking** (`reranker.py`) — `BAAI/bge-reranker-v2-m3` reranks the fused top-10 candidate pool (`DEFAULT_VECTOR_TOP_K=10`) down to the final top-3 (`DEFAULT_RERANK_TOP_K=3`) delivered to the LLM. Adds retrieval *precision* on top of the recall the fusion step already provides.
- **BM25 Persistence** — module-load block in `rag.py`: load corpus JSON → if empty, rebuild from ChromaDB via `collection.get()` → load the BM25 index via `.load()`. New settings `BM25_INDEX_DIR`, `BM25_CORPUS_FILE` added to `settings.py`.
- **Dynamic Gemini API Pool** — `api_pool` of up to 20 keys with per-key failure tracking, exponential cooldown (`min(300, 60 × 2^(failures-1))`), and last-successful-key stickiness. New functions `get_next_available_client()`, `mark_api_success()`, `mark_api_failed()`, `print_api_pool_status()`.
- **Hybrid Search Ground Truth** — 25 hand-verified lexical queries (`HS_ALL_QUESTIONS`) across all 5 documents, with every named term confirmed present verbatim in the source PDF via manual search. Kept in separate per-document datasets (`HS_AGI_DATASET`, `HS_CYBERSECURITY_DATASET`, `HS_QUANTUM_DATASET`, `HS_RENEWABLE_ENERGY_DATASET`, `HS_CLIMATE_CHANGE_DATASET`) distinct from the existing semantic `ALL_QUESTIONS` set.

### Changed
- `query_rag(user_input, where)` signature and internals fully rewritten — now fuses two retrieval sources and reranks, rather than a single ChromaDB `collection.query()` call.
- `settings.py` — added `DEFAULT_RERANK_TOP_K`, `RERANKER_MODEL`, `BM25_INDEX_DIR`, `BM25_CORPUS_FILE`.

### Verified
| Dataset | Recall@1 | Recall@3 | MRR |
|---|---|---|---|
| `ALL_QUESTIONS` (vector-only) | 88% | 100% | 0.94 |
| `HS_ALL_QUESTIONS` (hybrid) | 72% | 100% | 0.86 |

Both pipelines hit 100% Recall@3. The Recall@1 gap is attributed to corpus size — 5 PDFs producing ~25 total chunks gives BM25 too little candidate diversity to show a discrimination edge over vector search alone. Expected to close on larger corpora; not treated as a defect.

#### Key Insight
> BM25 is lexical (keyword-exact), vector search is semantic (meaning-based) — hybrid combines both, but only pays off once the corpus is large enough that lexical exactness actually disambiguates between candidates. On a 25-chunk corpus, both retrievers are essentially looking at the same small pool.

---

## [v4.3.0] — 2026-06-22 — Chunking Rework & RAG Evaluation Suite

### Added
- **Paragraph-Aware Fixed-Token Chunker** — replaces pure `\n\n` paragraph splitting. Small paragraphs (≤ `CHUNK_SIZE` words) are kept whole; large paragraphs are split via a sliding window (`CHUNK_SIZE=250`, `OVERLAP=50`, `STEP=200`) so no chunk exceeds a usable embedding size while the overlap prevents an idea from being fully lost at a cut point.
- **`evaluator.py`** — offline RAG evaluation tool. Runs 25 hand-written ground-truth question/page/filename triples across 5 documents through `query_rag()`, reports Recall@1, Recall@3, MRR, Average Rank, and per-query latency.
- **`ground_truth.py`** — the 25-question hand-verified benchmark dataset (every question written by reading the actual source PDF, never generated by the pipeline under test — avoids circular evaluation bias).

### Fixed
- A dense 2-page PDF that previously produced only **2 total chunks** under pure `\n\n` splitting now produces properly granular chunks under the new chunker — confirmed no drop in retrieval quality.

### Verified
- 100% Recall@3 across all 5 documents, 25 questions, full-corpus evaluation, on the vector-only pipeline (pre-hybrid-search baseline).

#### Key Insight
> Chunk granularity is invisible until you measure it. A report that "looked fine" was silently producing only 2 retrievable units for an entire PDF — the evaluator is what surfaced this, not manual inspection.

---

## [v4.2.0] — 2026-06-21 — Document Relevance Classifier

### Added
- **`classify_document_relevance(user_input, filenames)`** — a dedicated, low-temperature (`0.0`) Gemini call whose only job is a binary decision: does answering this specific query require reading the uploaded documents? Centralizes a decision that was previously left to the main LLM's own prompt-following discipline, which proved unreliable — the agent would sometimes call `search_documents()` just because file names were visible to it, independent of whether the query needed them.
- **`get_available_files(user_input)`** upgraded from an unconditional "return every filename" function into a gated one: returns `""` immediately if the collection is empty (no wasted classifier call), otherwise calls the classifier and returns real filenames only on `TRUE`.
- **Classifier Benchmark** — 12 categorized test datasets (`document_summary`, `document_qa`, `document_search`, `information_extraction`, `document_comparison`, `startup_analysis`, `mvp`, `tech_stack`, `coding`, `general_knowledge`, `greetings`, `startup_documents`), plus `ambiguous.py` and `adversarial.py` for qualitative-only robustness checks (prompt injection, routing traps, contradictory instructions — not scored, inspected).

### Known Issues
- **DS-033** — bare-pronoun phrasing ("Explain it.") is inherently ambiguous with no antecedent in the query itself; the classifier's accuracy here is bounded by the information available, not by prompt quality. Documented as an architectural limitation.
- One ambiguous case — "analyze this idea with full tech stack and MVP suggestion" — intermittently misclassifies as `TRUE` even with `temperature=0.0` and explicit `FALSE` examples in the prompt.

#### Key Insight
> Prompt-only classification has a real, non-zero, irreducible error rate on genuinely ambiguous natural language. A fourth prompt rewrite is not guaranteed to close a case that survived three rewrites already — at some point the fix is structural (e.g. a retrieval-similarity second opinion), not another sentence added to the prompt.

---

## [v4.1.0] — 2026-06-20 — Stage Gating Enforcement

### Added
- **`validate_stage_tools(stage, tool_call_list, document_access_allowed)`** in `orchestrator.py` — real, code-enforced gatekeeping. Before this, `stage` was purely a print-label counter with zero power to stop the LLM from calling a tool out of order. This function checks every `tool_call` the LLM makes against a `STAGE_MAP`, rejects the *entire batch* if any single call is wrong-stage or unrecognized, and detects missing required tool calls for the current stage — injecting a `role: "user"` correction message so the LLM can self-correct on retry.
- `TOOL_TO_STAGE` reverse-lookup so rejection messages can tell the LLM exactly which stage a misplaced tool actually belongs to.
- `MAX_STAGE_RETRIES = 3` ceiling — prevents an unbounded retry loop from silently burning API quota if the LLM can't self-correct.

### Fixed
- Caught and correctly rejected a real, repeated LLM behavior: bundling `risk_analysis()` (Stage 3) together with `search_documents()` (Stage 4) in a single tool-call batch. The gate now rejects the whole batch and forces a clean retry rather than executing a partially-valid call.

#### Key Insight
> A counter that only labels the current stage but has no power to reject a bad call is decoration, not enforcement. Real gating requires inspecting every tool call against the expected set *before* execution, not just printing what stage the code believes it's in.

---

## [v4.0.0] — 2026-06-19 — Multi-PDF Isolation

### Added
- **`where={"file_name": ...}` filtering** added to `query_rag()`'s ChromaDB `collection.query()` call — enables document-scoped retrieval across multiple uploaded PDFs living in a single shared collection, without needing a separate collection per file.
- Metadata (`file_name`, `page_number`) now consistently stored per chunk at ingestion time — the foundation the `where` filter depends on.
- **`temp_list`/`self.messages` isolation pattern** in `orchestrator.py` — `temp_list = self.messages.copy()`, conditional replacement of `temp_list[0]` with a *new* dict (never in-place mutation) when `FILE_PROMPT` injection is needed that turn, then `self.messages.extend(temp_list[length:])` on exit. Keeps `self.messages[0]` permanently static across the whole session regardless of which files are relevant turn-to-turn.
- **Forced argument overwrite** — `function_args` for `market_context` / `mvp_context` / `startup_idea` are forcibly overwritten from `workflow_state` in code immediately before tool execution, completely bypassing LLM-constructed argument values for these three keys.

### Fixed
- **Hallucinated context bug** — earlier versions let the LLM construct `market_context`/`mvp_context` itself when calling Stage 2/3 tools, and it would sometimes fabricate plausible-looking context instead of using real upstream tool output. Forced overwrite eliminates this failure mode entirely — the LLM still decides *when* to call a tool, never *what context* it receives for these three keys.
- Missing system prompt in the final report-assembly Groq call — the call previously had no `role: "system"` message, producing ungrounded final output. Fixed by properly splitting `SYSTEM_PROMPT` (system role) and `final_prompt` (user role).

### Verified
- Cross-document isolation — 100% of retrieved chunks matched the requested file across multi-PDF tests, zero contamination between documents.
- `temp_list`/`self.messages` isolation — `self.messages[0]` confirmed static across multiple turns in a live multi-turn session.

#### Key Insight
> Shallow-copy mutation through a shared dict reference is invisible until you trace it directly. `temp_list[0]["content"] = X` silently corrupts `self.messages[0]["content"]` too, because `.copy()` on a list of dicts only copies the outer list — the dicts inside are still shared references. Reassigning a brand-new dict at the index (`temp_list[0] = {...}`) is the actual fix; mutating the existing one in place is not.

---

## [v3.6.0] — 2026-06-14 — Phase 3 Closure, RAG Integration & CLI Rewrite

### Added
- Rule 11 in `prompts.py` — explicit prohibition: `search_documents()` never called during Stages 1, 2, or 3.
- Rule 13 in `prompts.py` — Stage 2/3 failure handling distinct from the Rule 12 footer.
- Stage 4 explicitly defined in `TOOL CALL ORDER` — "ONLY after Stage 3, never during Stages 1, 2, or 3."
- Chain-of-thought block in `SYSTEM_PROMPT` — LLM reasons about required stages before acting.
- Inner `try/except` per URL in `summarize_text()` Fan-In — failed URLs skipped individually, not propagated to the caller.
- `client.heartbeat()` in `embed_and_store()` — verifies ChromaDB connection before write.
- Full keyboard interrupt handling in `app.py` — Ctrl+C, Ctrl+D, EOF all handled cleanly with a shared `handle_exit()`.

### Changed
- All Stage 2/3 error returns normalized to `"<X> unavailable — service error, no data retrieved."`
- `search_documents()` return format changed from a stringified dict to plain text `[Page N, filename]: text` — enables direct LLM citation without parsing.
- `text-embedding-004` → `gemini-embedding-001` — 404 NOT_FOUND on free-tier API key.
- `n_results` reduced from 5 to 3 — prevents Stage 4 RAG results from bloating the message context.

### Fixed
- Formatting bug — missing newline between Rule 9 and Rule 10 concatenated them into a single rule.
- Per-URL failure in `summarize_text()` was discarding all successful results — inner try/except fixes partial-failure handling.
- `search_documents` batched into Stage 1 — explicit Stage 4 with prohibition language fixed ordering.

### Verified
- Full 4-stage pipeline confirmed working — correct order, RAG triggers correctly on document reference.
- PDF citations appear with page numbers and filename in the final report.
- Phase 3 closed ✅

---

## [v3.5.0] — 2026-06-13 — Pipeline Verified & RAG Citation Fix

### Changed
- `SYSTEM_PROMPT` Rule 10 corrected from "four stages" → "three stages" — fixed a contradiction with `TOOL CALL ORDER` that was causing the LLM to narrate instructions as prose instead of executing them.
- `query_rag()` now returns `{"text": ..., "metadata": ...}` dicts via `zip(documents, metadatas)` — enables proper source citations with page numbers and filenames.

### Fixed
- Stage print-label edge case — cosmetic mislabeling on edge cases.

### Verified
- 3-stage pipeline confirmed working across 2 different startup ideas — correct order, no stage skipping, no batching.

---

## [v3.4.0] — 2026-06-12 — summarize_text Architecture Refactor

### Changed
- `summarize_text()` removed as an LLM-callable tool — now called internally by `analyze_market()` and `search_knowledge_base()` before they return.
- `market_context` split into two separate parameters — `market_analysis` and `market_search` — across `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()`.
- Pipeline reduced from 4 stages to 3 from the LLM's perspective.

### Fixed
- LLM no longer constructs nested JSON from raw Tavily results — summarization happens internally before results ever reach the agent, eliminating special-character schema validation failures.

---

## [v3.3.0] — 2026-06-11 — Phase 3 Pipeline Debugging & Stage Enforcement

### Added
- Iteration markers in `agent.py` — diagnostic prints for pipeline debugging.
- Rules 10–13 in `SYSTEM_PROMPT` — enforce stage execution order and context passing.
- Hallucinated tool name guard — unknown tool names append a clean error to history instead of crashing.

### Changed
- Temperature `0.5` → `0.3` — increases instruction-following for strict stage ordering.

### Fixed
- LLM skipping Stages 2–4 entirely after Stage 1, hallucinating a full report from partial data.
- `risk_analysis()` batched with Stage 3 tools before `suggest_mvp()` returned — hallucinated `mvp_context`.
- `rag.py` — `genai.Client()` was missing its API key.
- Wrong `requests.exceptions` handlers on Gemini-backed tools, replaced with correct Gemini exception types.

---

## [v3.2.0] — 2026-06-10 — Agent Scoping Fixes & Prompt Pipeline

### Added
- Four-stage tool call pipeline in `prompts.py` — explicit sequential ordering.
- Hallucinated tool name guard.
- `self.context_loaded` boolean flag — prevents `get_context()` from reloading history every turn.

### Fixed
- `self.future` was an instance variable — two rapid calls shared and corrupted the same dict. Moved to a local variable inside `run()`.
- System prompt was appended inside `run()`, duplicating on every follow-up — moved to `__init__()`.

---

## [v3.1.0] — 2026-06-09 — Tool Context & Exception Fixes

### Added
- `market_context` parameter threaded through `suggest_mvp()`, `recommend_tech_stack()`, and `risk_analysis()`.
- `mvp_context` parameter added to `risk_analysis()`.

### Fixed
- `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()` were using `requests.exceptions` handlers — these tools call the Gemini client, which raises `google.api_core.exceptions`, not `requests.exceptions`. Replaced with correct types.

---

## [v3.0.0] — 2026-06-08 — Phase 3 Complete

### Added
- `rag.py` — complete RAG pipeline built from scratch: `ingest_pdf()`, `embed_and_store()`, `query_rag()`.
- `search_documents` tool connecting the RAG pipeline to the ReAct agent.
- PDF ingestion trigger in `app.py` before the conversation loop starts.
- `database/chroma_db/` persistent ChromaDB store.

### Fixed
- `requirements.txt` was missing `groq`, `google-genai`, `tavily-python`, `chromadb`, `pdfplumber`.

---

## [v2.0.0] — 2026-06-07 — Phase 2 Complete

### Added
- ReAct agent loop — `while True` with `tool_calls` detection.
- Parallel tool execution via `ThreadPoolExecutor` + `as_completed`.
- Groq LPU inference (Llama 3.3 70B) replacing local Ollama.
- Live Tavily web search — `analyze_market()`, `search_knowledge_base()`.
- Gemini 2.5 Flash analysis tools — `suggest_mvp()`, `recommend_tech_stack()`, `risk_analysis()`.
- `tools_description.py` — separate JSON schema layer for all tools.

### Changed
- Replaced placeholder tools with real API integrations; replaced local Ollama with Groq LPU.

---

## [v1.0.0] — 2026-06-01 — Phase 1 Complete

### Added
- `agent.py` — core agent class with manual tool execution.
- `app.py` — CLI conversation loop.
- `context_manager.py` — sliding window memory, last 6 turns.
- `tools.py` — placeholder tools for market, MVP, tech stack, risk analysis.
- `prompts.py` — system prompt with structured output format.
- `.env` support via `python-dotenv`.
- `.gitignore` — secrets and cache excluded from day one.