# Phase 5 — Engineering Audit

**Scope:** Phase 5 only — API-key rotation, `core/key_rotator.py`, Gemini/Groq/
Tavily tools, provider tool instance migration, Phase 5-relevant `decorators.py`
and `orchestrator_agent.py` behaviour, Gemini structured-response handling,
large-context execution, parallel execution, focused testing.

**Method:** `bb5d96c` (baseline) → `adaa312` (Phase 5 HEAD), plus the current
uncommitted working tree. Committed history and working tree are reported
separately.

**Status:** Audit only. No source file was modified. No runtime calls were made —
every conclusion is from code, diff, or the existing `tests_output.txt`.

## Evidence classification

| Class | Meaning |
|---|---|
| **CONFIRMED** | Directly established from code or diff evidence. |
| **RUNTIME-VERIFIED** | Confirmed by an existing test, log, or output artifact. |
| **NEEDS-VERIFICATION** | Plausible from code, but manifestation requires a runtime test. |
| **INFORMATIONAL** | Observation; not a demonstrated defect. |

## Severity model

| Level | Meaning |
|---|---|
| **CRITICAL** | Blocks reliable Phase 5 operation or causes systemic failure. |
| **HIGH** | Causes significant workflow or provider failure. |
| **MEDIUM** | Materially affects reliability, observability, or maintainability. |
| **LOW** | Minor defect or technical debt. |
| **INFORMATIONAL** | Observation without demonstrated failure. |

Severity reflects demonstrated impact, not theoretical possibility. Where a
mechanism is confirmed but its manifestation is not, that is stated.

## Phase 5 commit range

| Commit | Subject |
|---|---|
| `fd2bd6c` | add generic API key rotation utility |
| `2dc3a92` / `6882a0c` / `42447e3` | rotation for Groq / Gemini / Tavily |
| `d12333b` | configure provider API key lists |
| `26483f7` | migrate consumers to provider tool instances |
| `8adc4f5` | merge Session 28 — dynamic API key rotation |
| `a9c6676` / `adaa312` | improve / integrate testing workflow |

Committed footprint vs baseline: 27 files, +3557/−4871. New file:
`src/core/key_rotator.py` (+100).

---

# Part 1 — Known Working

Phase 5 behaviour verified as correct. Recorded so the audit is not read as a
blanket condemnation.

| # | Behaviour | Evidence | Class |
|---|---|---|---|
| W1 | **Provider tool instance migration is complete.** All 21 agent call sites go through the shared `groq_tool` / `gemini_tool` / `tavily_tool` singletons. No agent instantiates a provider SDK directly. | grep of all `*_tool.` call sites | CONFIRMED |
| W2 | **`key_rotator` is correctly provider-agnostic.** Imports only `collections.abc` and the local exception type — no provider SDK, matching its stated constraint. | `key_rotator.py:14-16` | CONFIRMED |
| W3 | **Rotation state is correctly encapsulated.** State lives in a closure; no module-level mutable rotation state, as designed. | `key_rotator.py:48-49` | CONFIRMED |
| W4 | **Key selection works end to end.** Distinct keys are selected and requests succeed. | `tests_output.txt:29-30, 73-83` | RUNTIME-VERIFIED |
| W5 | **Groq calls succeed.** ADVANCEMENT ran 4 sequential Groq calls, 0 errors. | `tests_output.txt:73-104` | RUNTIME-VERIFIED |
| W6 | **Gemini calls succeed.** NURTURING and ADVANCEMENT completed Gemini calls with 0 errors. | `tests_output.txt:29-33, 100-104` | RUNTIME-VERIFIED |
| W7 | **Intent routing works for every intent tested.** 5 focused intents pass on classification. | `tests_output.txt` (all 5 blocks) | RUNTIME-VERIFIED |
| W8 | **Phase 5 strengthened the test pass criteria.** `and not errors` was **added** by Phase 5 — absent at baseline `bb5d96c`, present in HEAD. | `app.py:774-777, 994-997`; `git show bb5d96c:app.py` | CONFIRMED |
| W9 | **Judge response schemas are Gemini-array-compatible.** Both specify `items` on their array property, which Gemini requires. | `llm_judge_agent.py:194-196, 235-237` | CONFIRMED |
| W10 | **Structured schemas are not Groq-wrapped.** They are bare JSON Schema objects, not `{"type": "json_schema", ...}` envelopes — correct for Gemini's `response_schema`. | `startup_scorer_agent.py:189`, `llm_judge_agent.py:170, 211` | CONFIRMED |
| W11 | **Gemini client lifecycle is correct.** Client closed in `finally` on both methods — the only tool that does. | `gemini_tool.py:115-116, 200-201` | CONFIRMED |
| W12 | **Decorator order is correct on every agent.** `retry_on_failure` is innermost, so retries execute before `handle_errors` observes anything. Retry is functionally live. | all agent decorator stacks | CONFIRMED |
| W13 | **Rotator exhaustion is explicit, not silent.** Raises a typed `ToolConnectionError` rather than returning `None` or reusing a stale key. | `key_rotator.py:54-57` | CONFIRMED |
| W14 | **Empty-key configuration is rejected at construction.** Prevents a tool initialising with zero keys. | `key_rotator.py:43-46` | CONFIRMED |
| W15 | **Settings filters falsy keys.** Unset `*_API_KEY_n` slots are dropped rather than passed as `None`. | `settings.py:34-36, 42-44, 50-52` | CONFIRMED |

---

# Part 2 — Findings by root cause

Consolidated so cascading failures are attributed to their originating defect
rather than counted as separate root causes. **9 root causes.**

---

## RC-1 — Key rotation is one-shot consumption, not rotation

**Severity: CRITICAL** · **Evidence: CONFIRMED + RUNTIME-VERIFIED** · Phase 5 (new)

### Root cause

`get_next_key()` increments `current_index` on **every call**, with no modulo and
no failure-triggered advance ([key_rotator.py:51-62](../src/core/key_rotator.py#L51)):

```python
if current_index >= len(key_list):
    raise ToolConnectionError("All configured API keys have been exhausted.")
key = key_list[current_index]
current_index += 1
```

The index advances *before* the request, so success or failure is irrelevant to
rotation. All three tool docstrings state *"Rotates to the next key when a
rate-limit error occurs"* — the implementation rotates on every request. Code and
documented contract disagree.

**Runtime evidence:** `tests_output.txt:73-83` — the ADVANCEMENT test consumes
four distinct Groq keys (`...T0rb`, `...fbzY`, `...213v`, `...8ZK6`) for four
sequential calls with **zero errors**. Advance-on-call is proven, not inferred.

### Direct consequence

Pool capacity is measured in *total requests per process*, not in rate-limit
events. After N calls (N = configured keys) the tool raises permanently.

### Cascading consequences

- **C1 — Exhaustion is retried.** `ToolConnectionError` is the first entry in
  `retry_on_failure`'s retryable tuple ([decorators.py:115-118](../src/core/decorators.py#L115)),
  so an exhausted pool triggers 3 further attempts at `MIN_COOLTIME_RETRY` (3 s)
  each — ~9 s of guaranteed-futile waiting per agent. *(CONFIRMED)*
- **C2 — Retries multiply the burn.** Because rotation precedes the request, each
  retry consumes a **fresh** key. With `MAX_RETRIES = 3`, one failing agent can
  consume **4 keys**. Amplified by RC-4, which makes even deterministic failures
  retry. *(CONFIRMED mechanism; count NEEDS-VERIFICATION)*
- **C3 — Depletion is cumulative across queries.** Tools are module-level
  singletons, so rotation state persists for the process. In the interactive CLI,
  spend accumulates across every query in a session and does not reset per run.
  *(CONFIRMED)*
- **C4 — Tavily demand exceeds supply in one run.** *(see RC-1a)*

### User-visible consequence

Agents fail mid-run with `All configured API keys have been exhausted`. Later
queries in a session fail earlier than the first. Nothing in the message
indicates the key was never actually rate-limited.

### Intended direction

Replace permanent consumption with failure-triggered rotation: hold a key until
it fails, advance only on a rate-limit/quota signal, and wrap around with
per-key cooldown tracking rather than permanent retirement.

---

## RC-1a — Tavily pool capacity is below single-run demand

**Severity: CRITICAL (conditional)** · **Evidence: CONFIRMED capacity/demand; NEEDS-VERIFICATION manifestation** · Phase 5 (new)

The most acute manifestation of RC-1, recorded separately because it is a
**sizing** fact independent of the rotation algorithm.

Tavily calls in one `full_analysis`:

| Agent | Calls | Reference |
|---|---|---|
| MarketResearchAgent | 3 (parallel) | [market_research_agent.py:232,237,242](../src/agents/market_research_agent.py#L232) |
| WebSearchAgent | 3 (parallel) | [web_search_agent.py:287,292,297](../src/agents/web_search_agent.py#L287) |
| RecommendationAgent | 1 | [recommendation_agent.py:230](../src/agents/recommendation_agent.py#L230) |
| **Total** | **7** | vs. **≤6 keys** (`settings.py:48`, `range(1, 7)`) |

**Direct consequence:** the 7th call raises exhaustion, so `RecommendationAgent`
fails on the first `full_analysis`. **Cascading:** the first 6 calls are issued
from a single parallel batch, so they also race (RC-2). **User-visible:** every
`full_analysis` returns without recommendations.

> **Honest limit:** `range(1, 7)` caps capacity at 6, but the *actual* count
> depends on how many `TAVILY_API_KEY_n` are populated in `.env`, which was not
> read. Fewer configured keys makes this manifest **sooner**, not later. The
> arithmetic is confirmed; the exact failure point is not.

Gemini, for comparison: ~11 calls per `full_analysis` against ≤20 keys — the
**second** run in a process is the exposure point (per C3).

### Intended direction

Size pools against measured per-run demand, or remove the dependency by fixing
RC-1 so capacity is bounded by rate limits rather than request count.

---

## RC-2 — Rotator closure is not thread-safe

**Severity: HIGH** · **Evidence: CONFIRMED (code); NEEDS-VERIFICATION (manifestation)** · Phase 5 (new)

**Root cause:** the bounds-check → read → increment sequence in `get_next_key`
is a non-atomic read-modify-write with no `threading.Lock`. `current_index += 1`
compiles to load/add/store, which the interpreter may interleave.

**Direct consequence:** concurrent callers can read the same `current_index`,
receive the **same key**, and lose an increment.

**Cascading consequence:** two concurrent requests hit one key's rate limit —
precisely what rotation exists to prevent — and the pool depletes at an
unpredictable rate, compounding RC-1.

**User-visible consequence:** sporadic, non-reproducible batch-1 failures.

Exposure is real: the orchestrator runs batches through `ThreadPoolExecutor`
([orchestrator_agent.py:334-357](../src/agents/orchestrator_agent.py#L334)) and
batch 1 issues 6 concurrent Tavily calls against one rotator.

Races are probabilistic; no observed occurrence is claimed.

### Intended direction

Guard rotation state with a lock, or make the counter atomic.

---

## RC-3 — Groq's error-classification shape was copied to Gemini and Tavily unadapted

**Severity: HIGH** · **Evidence: CONFIRMED (duplication); NEEDS-VERIFICATION (ineffectiveness)** · Phase 5 (new)

**Root cause:** the rate-limit check written for Groq was copied verbatim into
both other tools ([gemini_tool.py:102-111, 187-196](../src/tools/gemini_tool.py#L102);
[tavily_tool.py:86-95](../src/tools/tavily_tool.py#L86)):

```python
status_code = getattr(error, "status_code", None)
error_code  = getattr(error, "code", None)
if status_code == 429 or error_code == "rate_limit_exceeded":
```

The duplication is confirmed. Its ineffectiveness rests on each SDK's error
model: `google.genai` raises `APIError`/`ClientError` exposing `.code` as an
**int** and `.status` as a string, with no `.status_code`; the Tavily SDK raises
`UsageLimitExceededError` / `InvalidAPIKeyError`. If so, `status_code` is `None`
and `error_code` is an int compared against a string — both operands false.

**This was not verified at runtime and must not be treated as proven.**

**Direct consequence (if confirmed):** Gemini 429s and Tavily usage-limit errors
never become `ToolConnectionError`; they fall to bare `raise`.

**Cascading consequence:** masked today, because RC-4 makes the generic branch
behave identically — so retry still happens and the misclassification is
invisible. Any future logic keyed on `ToolConnectionError` will silently not fire
for two of three providers. Tavily, the pool that exhausts first (RC-1a), is the
worst place for this to be wrong.

**User-visible consequence:** logs cannot distinguish rate limit from quota
exhaustion from a genuine bug.

### Intended direction

Classify per-provider against each SDK's real exception types and attribute
names, rather than reusing one provider's shape.

---

## RC-4 — No non-retryable error classification exists

**Severity: HIGH** · **Evidence: CONFIRMED** · Phase 5 (decorators rewritten, +177 lines)

**Root cause:** `retry_on_failure` has a typed branch for
`(ToolConnectionError, WorkflowStateError)` and a bare `except Exception` branch
whose bodies are **byte-identical** ([decorators.py:115-138](../src/core/decorators.py#L115)).
The typed branch has no behavioural effect, and there is no code path for
"do not retry this".

**Direct consequence:** every exception is treated as transient — 400s, 413
oversized-request, 401 invalid key, and local schema errors all retry 3×.

**Cascading consequences:**
- Combined with RC-1/C2, each deterministic failure burns up to 4 keys.
- ~9 s of latency per agent on failures that cannot succeed.
- This is the mechanism behind large-content failures in the report and judge
  paths: an oversized Groq request (`max_completion_tokens` fixed at 4096, no
  input-size check) is retried as though it were transient.

**User-visible consequence:** slow failures, and key exhaustion with no
rate-limit event to explain it.

### Intended direction

Introduce a non-retryable class (auth, malformed request, oversized payload,
schema invalid) that fails fast without consuming a key, and make the typed
branch meaningful.

---

## RC-5 — `pipeline_status` has two incompatible value conventions

**Severity: HIGH** · **Evidence: CONFIRMED (conflict); NEEDS-VERIFICATION (TypeError)** · Phase 5 (both sides)

**Root cause:** 16 agents write a **flat string**
(`pipeline_status["MVPAdvisorAgent"] = "success"`). `LLMJudgeAgent` alone writes
a **nested dict** ([llm_judge_agent.py:415-420, 653-658](../src/agents/llm_judge_agent.py#L415)):

```python
workflow_state["pipeline_status"].setdefault("LLMJudgeAgent", {})
workflow_state["pipeline_status"]["LLMJudgeAgent"]["run_final"] = ...
```

`orchestrator_agent.py:397` and the working-tree `decorators.py:166` both write
the flat form to the same key.

**Direct consequence:** the value type at `pipeline_status["LLMJudgeAgent"]`
depends on which path wrote last.

**Cascading consequence:** after a flat write, `setdefault` returns a `str` and
the `["run_final"] = ...` assignment raises
`TypeError: 'str' object does not support item assignment`. That `TypeError` is
itself caught by `handle_errors`, which re-writes the flat string — so the judge
fails permanently and silently.

**User-visible consequence:** `judge_feedback` never populates and no error
explains why.

Both sides are Phase 5 (`LLMJudgeAgent` is Phase 5; the decorator change is
Phase 5 in-flight). The working-tree change broadens exposure from one
orchestrator path to every decorated agent failure.

### Intended direction

Settle on one shape for `pipeline_status` values and make all writers conform.

---

## RC-6 — `run_mid()` was orphaned by a Phase 5 edit

**Severity: HIGH** · **Evidence: CONFIRMED (diff)** · Phase 5 regression

**Root cause:** Phase 5 replaced the mid-checkpoint call. From
`git diff bb5d96c..HEAD -- src/agents/orchestrator_agent.py`:

```diff
-                        .run_mid(workflow_state)
+                        .run_final(workflow_state)
```

This is the strongest single piece of evidence in the audit: the baseline called
`run_mid`, and Phase 5 changed it to `run_final`. The surrounding error handler
still labels the failure `"LLMJudgeAgent.run_mid"`
([orchestrator_agent.py:500](../src/agents/orchestrator_agent.py#L500)),
confirming the original intent.

`LLMJudgeAgent.run_mid` (line 256) remains fully implemented with its own
`MID_RESPONSE_FORMAT`, and is now called from **nowhere** except the module's own
`__main__` (line 752).

**Direct consequence:** the mid checkpoint evaluates *final-report* criteria
while `final_report` is still empty.

**Cascading consequence:** `judge_feedback["mid_pipeline"]` is never populated;
both checkpoints write `judge_feedback["final"]`, so the second overwrites the
first.

**User-visible consequence:** no mid-pipeline quality gate — a run proceeds to
report generation on upstream data that was never judged.

### Intended direction

Restore `run_mid()` at the mid checkpoint.

---

## RC-7 — Gemini structured-output contract is unenforced

**Severity: HIGH** · **Evidence: CONFIRMED (code paths); NEEDS-VERIFICATION (occurrence)** · Phase 5 (new)

**Root cause:** three gaps in one method:

1. `return response.text` ([gemini_tool.py:203](../src/tools/gemini_tool.py#L203))
   is annotated `-> str`, but `.text` is `None` when candidates are empty,
   safety filters block, or generation stops at `MAX_TOKENS`. *(CONFIRMED that
   it is unguarded; NEEDS-VERIFICATION that it occurs here.)*
2. No `max_output_tokens` is configured, so truncation is possible on the
   large-context agents, and truncated JSON does not parse. *(CONFIRMED)*
3. `types.GenerateContentConfig(...)` is built **inside** the `try`
   ([gemini_tool.py:166-169](../src/tools/gemini_tool.py#L166)), so a schema
   construction error is caught by the provider handler and printed as
   `❌ Gemini key ...XXXX failed`. *(CONFIRMED)*

**Direct consequence:** `None` or truncated text reaches the four structured
consumers (`llm_judge` ×2, `recommendation`, `startup_scorer`); local schema bugs
are attributed to the API key.

**Cascading consequence:** `json.loads(None)` raises `TypeError`, which RC-4
retries 3× while RC-1 burns a key per attempt.

**User-visible consequence:** "agent failed" with no indication the model
returned nothing, or a key blamed for a local bug.

### Related: Gemini schema keyword compatibility — NEEDS-VERIFICATION

`STARTUP_SCORE_RESPONSE_FORMAT` uses `minimum`/`maximum` integer constraints
([startup_scorer_agent.py:200-201](../src/agents/startup_scorer_agent.py#L200)).
Gemini's `response_schema` historically accepts only an OpenAPI subset excluding
those keywords. Whether the installed `google-genai` ignores or rejects them is
version-dependent and **was not verified**. If it rejects, gap 3 above makes it
present as a key failure.

### Also: embedding batch size — NEEDS-VERIFICATION

`generate_embedding` ([gemini_tool.py:46](../src/tools/gemini_tool.py#L46))
passes every chunk in one `embed_content` call with no batch cap. With
`CHUNK_SIZE = 250` words, a long pitch deck may exceed the per-request batch
limit. No limit was confirmed against the provider.

### Intended direction

Validate the response before returning, set an explicit output-token budget, and
build the config outside the provider `try` so local errors are not attributed
to the key.

---

## RC-8 — Groq debug instrumentation is unguarded and inside the request `try`

**Severity: MEDIUM** · **Evidence: CONFIRMED** · Phase 5 (new)

**Root cause:** [groq_tool.py:127-137](../src/tools/groq_tool.py#L127)
unconditionally indexes `messages[0]` **and** `messages[1]` and prints 500
characters of the prompt, all inside the `try` that wraps the API call.

**Direct consequences:**
- Any call with fewer than 2 messages raises `IndexError`. The tool's own
  `__main__` passes exactly one message
  ([groq_tool.py:174-186](../src/tools/groq_tool.py#L174)), so
  `python -m src.tools.groq_tool` fails.
- User prompt content is written to stdout with no debug gate, interleaving with
  the CLI spinner (visible in `tests_output.txt:74-83`).
- Header has no separators and two typos — `system_promtp`, `comined` — rendering
  as `messages=2system_promtp=348user_prompt=96comined=444`.

**Cascading consequence:** because the indexing sits inside the `try`, an
`IndexError` is caught at line 143 and printed as `❌ Groq key ...XXXX failed`,
then retried under RC-4 while RC-1 burns keys — a logging bug reported as a
provider outage.

**User-visible consequence:** prompt content in logs; a crash on any
single-message call.

Severity is MEDIUM, not HIGH: all current production agents send two messages,
so the crash is confined to `__main__` and any future single-message caller.

### Intended direction

Gate debug output behind a flag, index defensively, and move instrumentation
outside the provider `try`.

---

## RC-9 — Error and status records are shape-inconsistent

**Severity: MEDIUM** · **Evidence: CONFIRMED** · **Pre-existing, Phase 5 amplified**

**Root cause:** three writers use three shapes for `workflow_state["errors"]`:

| Writer | Keys | Error value |
|---|---|---|
| `orchestrator_agent.py` (~393, 452, 506, 553) | `agent_name`, `attempt`, `time_stamp` | raw exception **object** |
| `decorators.py` `handle_errors` | `agent`, `error_type`, `timestamp` | `str` |
| schema comment (`workflow_state.py:54`) | "see Error Log Format above" | — |

The orchestrator handlers are **unchanged** by Phase 5 — verified: a diff of
`bb5d96c..HEAD` filtered for `error"` returns no hits in those bodies. They are
genuinely pre-existing.

**Phase 5 amplification:** Phase 5 rewrote `decorators.py` (+177) and the working
tree adds `error_type`, so Phase 5 introduced a *second* divergent shape rather
than reconciling the first.

**Direct consequence:** consumers cannot rely on either key set.

**Cascading consequence:** the raw exception object is not JSON-serialisable, so
any attempt to serialise state for a report or PDF fails.

**User-visible consequence:** error counts are reportable but error *content* is
not renderable.

### Related, same root: observability gaps *(MEDIUM, CONFIRMED)*

- `log_execution` and `track_timing` both append to `execution_log`
  ([decorators.py:74, 96](../src/core/decorators.py#L74)) with different shapes —
  two entries per agent, neither carrying `status`, though
  `workflow_state.py:53` specifies "name + timing + status".
- `agent_retry_count` (schema line 52) is **never written**. `retry_on_failure`
  tracks a local `retries` counter and discards it — so the retry pressure that
  would expose RC-1's key burn is unobservable.

### Intended direction

Define one error record shape and one `execution_log` shape; populate
`agent_retry_count` from the existing counter.

---

# Part 3 — Working-tree status

Phase 5 changes present in the working tree but **not** in committed history.
Reported separately so fixed issues are not counted as current defects.

## WT-1 — `handle_errors` no longer returns `None`

- **Historical problem:** Phase 5 *added* `if result is None: raise
  WorkflowStateError(...)` guards to the orchestrator (confirmed: all `+` lines
  in the baseline diff). Combined with `handle_errors` returning `None`, every
  agent failure was logged **twice** — once by `handle_errors` with the real
  cause, once by the orchestrator as a generic *"returned None"* that buried it.
- **Current status:** working tree returns `workflow_state` and adds
  `error_type` plus a `pipeline_status` write ([decorators.py:143-176](../src/core/decorators.py#L143)).
- **Does it resolve the issue?** **Yes** for the double-logging. Safe because all
  21 agents already `return workflow_state` — the same dict they mutate — so
  `workflow_state.update(result)` at orchestrator line 379 is a no-op
  self-update. *(CONFIRMED)*
- **Additional verification required?** **Yes, two items:**
  1. It writes the flat `pipeline_status` form, broadening RC-5 exposure from one
     orchestrator path to every decorated agent failure. **This should be
     reconciled before the change is committed.**
  2. Nothing reads `pipeline_status` — grep returns only writes and docstrings.
     A failed agent still leaves its output key at the `STATE_SCHEMA` default,
     so `ReportWriterAgent` and `LLMJudgeAgent` will build prompts around empty
     strings. Returning `workflow_state` removes the crash but converts a loud
     failure into a silent one until a consumer exists. *(CONFIRMED — HIGH)*

## WT-2 — Test pass criteria already gates on errors

- **Historical problem:** the baseline harness passed on
  `actual_intent == expected` alone.
- **Current status:** both call sites require `and not errors`
  ([app.py:774-777, 994-997](../app.py#L774)) — added by Phase 5, present in
  committed HEAD, absent at `bb5d96c`.
- **Does it resolve the issue?** **Yes** for the error dimension.
- **Additional verification required?** Yes — `tests_output.txt` is a **stale
  artifact predating this gate**. Its `PARTIAL_IDEA ... ✅ PASS ... Errors : 10`
  line (`tests_output.txt:53-55`) would be reported as **FAIL** by the current
  harness. The file must be regenerated before it is used as evidence of
  anything. Remaining gap in Part 4.

## WT-3 — Debug print in the orchestrator return path

- **Historical problem:** none; new in the working tree.
- **Current status:** `print(workflow_state["errors"])` immediately before
  `return workflow_state` ([orchestrator_agent.py:600-602](../src/agents/orchestrator_agent.py#L600)).
- **Does it resolve anything?** No — it is debug scaffolding.
- **Additional verification required?** No. **LOW**; remove before commit.

---

# Part 4 — Phase 5 testing assessment

**Severity: MEDIUM** · **Evidence: CONFIRMED**

Phase 5 improved the harness (W8). A test now passes only when intent matches
**and** no errors were recorded. Measured against the four required conditions:

| Required condition | Status | Evidence |
|---|---|---|
| Routing/intent is correct | ✅ Checked | `app.py:775` |
| No unexpected errors exist | ✅ Checked — **added by Phase 5** | `app.py:776` |
| Workflow execution completes | ❌ Not asserted | no completion/`pipeline_status` check |
| Required workflow outputs are valid | ❌ Not asserted | see below |

**Output validity is not asserted.** An `INTENT_OUTPUT_MAP`
(`full_analysis → final_report`, etc.) exists at
[app.py:347-353](../app.py#L347), but it lives in the **renderer** class —
documented *"Converts workflow_state into a user-facing response. Does not
execute agents."* It selects what to display; it never asserts the value is
non-empty or well-formed. The only output-shaped assertion is a conditional
`pitch_deck_text` presence check (line 787), which is reported as `Doc State`
and **excluded from `passed`**.

**Consequence:** a run can still pass with `intent` correct, `errors` empty, and
`final_report` an empty string — for example when an agent fails in a way that is
swallowed rather than recorded (RC-5's silent judge failure, or the
`pipeline_status`-without-consumer gap in WT-1).

Two Phase 5-specific coverage gaps:

- **No test exercises key rotation or exhaustion** — the central Phase 5 feature
  has no test. `key_rotator.py`'s `__main__` asserts that exhaustion *is* the
  expected behaviour (lines 81-88), so it passes today and encodes RC-1 as
  intended design.
- **No test covers parallel-batch key contention** (RC-2).

**Artifact hygiene:** `tests_output.txt` is untracked, stale (WT-2), and contains
API key suffixes (`...BBNg`, `...T0rb`) from the tool debug prints. Last-4
fragments are not usable credentials, but they are key fingerprints and should
not be committed.

### Intended direction

Extend the pass predicate to cover completion and output validity; add rotation,
exhaustion, and contention tests; regenerate or delete the stale artifact.

---

# Part 5 — Informational observations

Not defects; recorded for completeness.

| # | Observation | Class |
|---|---|---|
| I1 | Groq and Gemini log key selection; **Tavily logs nothing** — the provider that exhausts first is the only silent one. | INFORMATIONAL |
| I2 | Groq and Tavily never close their clients; Gemini does. Per-call clients accumulate `httpx` sockets for the process lifetime. `groq_tool.py:99`, `tavily_tool.py:67`. | LOW |
| I3 | `tavily_tool.py:74` requests `include_answer="advanced"` but only `["results"]` is returned (line 99) — latency and quota spent on a discarded answer. `response["results"]` is also unguarded against `KeyError`. | LOW |
| I4 | `GROQ_MODEL` is hardcoded into `request_parameters` (`groq_tool.py:104`) with no per-call override, unlike Gemini's `gemini_model` parameter. `reasoning_effort` and `include_reasoning` are always sent and are specific to `openai/gpt-oss-120b`. | LOW |
| I5 | Provider migration left `Tools:` docstrings pointing at Groq in 5 agents now calling Gemini: `mvp_advisor:4`, `tech_advisor:4`, `startup_scorer:4`, `llm_judge:8`, `recommendation:4`. | LOW |
| I6 | Both structured-output dialects are live simultaneously: `idea_generation_agent.py:358` uses Groq `response_format`; four others use Gemini `response_schema`. Constants are named `*_RESPONSE_FORMAT` (Groq vocabulary) but consumed as Gemini schemas. | INFORMATIONAL |
| I7 | `GEMINI_MODEL = "gemini-3.6-flash"` and `GEMINI_LITE_MODEL = "gemini-3.5-flash-lite"` (`settings.py:8-9`) were **not** validated against the provider — no network call was made. `GEMINI_LITE_MODEL` is referenced nowhere. | NEEDS-VERIFICATION |
| I8 | `_get_workflow_state` prints a `[DECORATOR DEBUG]` block before raising (`decorators.py:42-47`) — debug scaffolding on an error path. | LOW |
| I9 | `log_execution` and `track_timing` call `_get_workflow_state` inside `finally`. If the agent raises *and* state resolution fails there, the `finally` exception replaces the original. | LOW |
| I10 | `API_COOLDOWN_SECONDS = 60` (`settings.py:15`) is defined but referenced nowhere — the intended cooldown mechanism is unimplemented. | INFORMATIONAL |

---

# Part 6 — Do not fix yet

This audit deliberately recommends **no code changes**. Directions only, in
dependency order — RC-1 and RC-4 are upstream of most other symptoms, so fixing
downstream items first will move failures rather than remove them.

| Order | Direction | Addresses |
|---|---|---|
| 1 | Replace permanent key consumption with failure-triggered rotation and wrap-around. | RC-1, RC-1a |
| 2 | Introduce a non-retryable error class that fails fast without consuming a key. | RC-4, and RC-1/C2 |
| 3 | Make rotation state concurrency-safe. | RC-2 |
| 4 | Reconcile `pipeline_status` to a single value shape **before committing WT-1**. | RC-5, WT-1 |
| 5 | Add a `pipeline_status` consumer so failures are surfaced, not silently defaulted. | WT-1 |
| 6 | Restore `run_mid()` at the mid checkpoint. | RC-6 |
| 7 | Classify provider errors against each SDK's real exception model. | RC-3 |
| 8 | Enforce the Gemini output contract; build config outside the provider `try`. | RC-7 |
| 9 | Gate debug output; move instrumentation outside the request `try`. | RC-8 |
| 10 | Unify error/log record shapes; populate `agent_retry_count`. | RC-9 |
| 11 | Extend test pass criteria; add rotation/exhaustion/contention tests. | Part 4 |

Sequencing note: several NEEDS-VERIFICATION items (RC-3, RC-7's schema question,
I7) should be resolved by the Part 7 checklist **before** design work, since the
answers change the shape of the fix.

---

# Part 7 — Verification checklist

Each item states what to test, expected behaviour now, expected behaviour after a
fix, and the finding it validates.

| # | What to test | Expected now | Expected after fix | Validates |
|---|---|---|---|---|
| V1 | Call `get_next_key()` `len(keys) + 1` times. | Raises `ToolConnectionError` on the final call. | Returns `keys[0]`; no raise. | RC-1 |
| V2 | Run one `full_analysis`; count `🔑` lines per provider. | Count rises monotonically with request count, not with failures. | Count rises only on rate-limit events. | RC-1 |
| V3 | Run `full_analysis`; watch `RecommendationAgent`. | Fails with `All configured API keys have been exhausted` (7 calls vs ≤6 keys). | Completes. | RC-1a |
| V4 | Issue two `full_analysis` queries in one CLI session. | Second fails earlier than the first (state persists in the singleton). | Both behave identically. | RC-1 / C3 |
| V5 | Point one `GROQ_API_KEY_n` at an invalid value; count `❌ Groq key ... failed` for one agent. | 4 lines (initial + 3 retries), each a different key. | 1 line; no retry, no extra key consumed. | RC-4, RC-1/C2 |
| V6 | Call `tavily_tool._get_next_key` from 6 threads; repeat ~100×; collect results. | At least one round yields duplicate keys. | All 6 distinct every round. | RC-2 |
| V7 | In a REPL, construct the `google.genai` and Tavily error types; assert `getattr(err, "status_code", None) is None`. | `None` — the 429 branch is unreachable. | Provider error maps to `ToolConnectionError`. | RC-3 |
| V8 | Force a judge failure at the mid checkpoint, then let the final checkpoint run. | `TypeError: 'str' object does not support item assignment`, swallowed. | Both checkpoints record status cleanly. | RC-5 |
| V9 | `grep -rn "run_mid" src/` and inspect `judge_feedback` after a full run. | Zero call sites outside `llm_judge_agent.__main__`; `mid_pipeline.judgment` stays `""`. | Mid checkpoint invoked; `mid_pipeline` populated. | RC-6 |
| V10 | Send an oversized prompt through a Gemini structured consumer. | Truncated/`None` text → `TypeError` from `json.loads`, retried 3×. | Typed error naming the real cause; no retry. | RC-7, RC-4 |
| V11 | Call `gemini_tool.generate_text(..., json_mode=True, response_schema=STARTUP_SCORE_RESPONSE_FORMAT)`. | Unknown — resolves whether `minimum`/`maximum` is rejected. If rejected, presents as `❌ Gemini key ... failed`. | Accepted, or rejected with a schema-specific error. | RC-7 (NEEDS-VERIFICATION) |
| V12 | `python -m src.tools.groq_tool`. | `IndexError`, printed as `❌ Groq key ... failed`. | Runs, or fails with a clear message. | RC-8 |
| V13 | After a failing run: `json.dumps(workflow_state["errors"])`. | `TypeError` — raw exception objects are not serialisable. | Serialises cleanly. | RC-9 |
| V14 | After a failing run, inspect `execution_log` and `agent_retry_count`. | Two entries per agent, no `status`; `agent_retry_count` empty. | One shaped entry per agent; retry counts populated. | RC-9 |
| V15 | Re-run all 5 focused intents; compare against `tests_output.txt`. | PARTIAL_IDEA now reports **FAIL** (10 errors) where the stale file says PASS. | All pass with `errors == []`. | WT-2, Part 4 |
| V16 | Force one agent to fail during `full_analysis`; inspect `final_report`. | Test may pass with an empty/degraded report — output validity unasserted. | Test fails, naming the missing output. | Part 4, WT-1 |
| V17 | Confirm `GEMINI_MODEL` / `GEMINI_LITE_MODEL` resolve at the provider. | Unknown — never validated. | Both resolve, or are corrected. | I7 |

---

# Part 8 — Phase 5 Release Assessment

### GO WITH CONDITIONS

Phase 5's structure is sound. The provider-instance migration is complete and
consistent (W1), the rotation utility is correctly encapsulated and
provider-agnostic (W2, W3), all three providers demonstrably serve live traffic
(W4–W6), intent routing passes on all 5 tested intents (W7), and Phase 5
measurably *strengthened* the test harness (W8). The working tree has already
resolved the most damaging error-handling defect (WT-1).

It is not a **GO** because one confirmed defect makes Phase 5's headline feature
behave opposite to its documented contract: rotation consumes a key per request
and never recovers (RC-1, RUNTIME-VERIFIED). For Tavily, confirmed arithmetic
puts single-run demand above pool capacity (RC-1a). Neither is a theoretical
risk.

It is not a **NO-GO** because both are localised to `key_rotator.py` and the
retry classification, behind a stable interface, with no architectural rework
required.

### Conditions required for GO

**Blocking — must be resolved:**

1. **RC-1** — rotation must advance on failure, not per call, and must wrap
   around. Validated by V1, V2, V4.
2. **RC-1a** — `full_analysis` must complete without exhausting Tavily.
   Validated by V3.
3. **RC-4** — non-retryable errors must fail fast without consuming a key.
   Validated by V5.
4. **RC-5 before committing WT-1** — `pipeline_status` must have one value shape.
   Validated by V8.
5. **RC-6** — `run_mid()` must be restored. Validated by V9.
6. **WT-3** — remove the debug print from the orchestrator return path.

**Blocking — must be *answered*, not necessarily fixed:**

7. **RC-3** via V7 and **RC-7 schema question** via V11 — both are
   NEEDS-VERIFICATION and change the shape of the fix. **No remediation should be
   designed before these run.**
8. **V15** — regenerate `tests_output.txt`. The current file is stale and cannot
   support a release decision.

**Non-blocking — should follow:**

9. RC-2 (V6) — concurrency correctness; probabilistic, no observed failure.
10. RC-7 output contract (V10), RC-8 (V12), RC-9 (V13, V14).
11. Part 4 coverage: completion and output-validity assertions (V16), plus
    rotation/exhaustion/contention tests.
12. WT-1 follow-up: add a `pipeline_status` consumer so failures surface.
13. I7 (V17) — validate model IDs.

### Assessment boundary

This assessment rests on code and diff evidence plus one existing test artifact
that is known stale. **No runtime verification was performed.** Items 7 and 8
above must be executed before this is treated as a final release decision.

---

# Out of scope

Excluded by the Phase 5 boundary and **not** reviewed: RAG fusion and reranking
internals (`src/rag/rag.py`), ChromaDB / BM25 / reranker / PDF tools, prompt
content quality (`src/prompts/prompts.py`, −4497 lines), the 15 domain agents'
JSON-parsing logic, `src/core/orchestrator.py` and `src/core/context_manager.py`
(untouched by Phase 5), and pre-Phase-5 documentation drift (`README.md` at
v3.6.0, `docs/ARCHITECTURE.md` at v4.5.0).

Pre-existing issues are included **only** where Phase 5 amplified them, and are
labelled *Pre-existing, Phase 5 amplified* (RC-9).
