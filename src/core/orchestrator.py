# ============================================================
#  orchestrator.py — StartupAgent Orchestrator for BizRadar AI
# ============================================================
#
#  What this file does:
#  Defines the StartupAgent class that drives the full analysis pipeline.
#  Manages the Groq LLM agentic loop — sending messages, receiving tool calls,
#  validating that each tool call belongs to its current stage, executing
#  valid tool calls in parallel, and feeding results back until a final
#  structured report is produced.
#
#  What this file does NOT handle:
#  Does not define tool logic — that belongs to tools.py.
#  Does not define tool schemas — that belongs to tools_description.py.
#  Does not define prompt strings — that belongs to prompts.py.
#  Does not manage RAG ingestion — that belongs to rag.py.
#
#  Classes:
#  - StartupAgent → wraps the full agentic loop; one instance per session
#
#  Functions:
#  - validate_stage_tools() → Phase 4 gatekeeper. Real enforcement, not just
#                             a print-label counter. Rejects tool calls that
#                             don't belong to the current stage, rejects
#                             search_documents() when no document context is
#                             allowed, and detects missing required tool calls.
#
#  Methods:
#  - __init__()  → sets up model, message history, and available tools map
#  - run()       → drives the LLM loop; handles tool calls and returns final answer
#
#  Used by:
#  - app.py → instantiates StartupAgent and calls run() with user input
#
#  Flow:
#  run(user_input, current_files) → load context once → append user message →
#  inject FILE_PROMPT into a temp_list copy if files exist →
#  Groq API call → tool calls? → validate_stage_tools() gate →
#  Fan-Out execute (if valid) → append results → loop back →
#  no tool calls → generate final structured report → return
#
#  Pipeline (3+1 stages):
#  Stage 1 → analyze_market() + search_knowledge_base() in parallel
#  Stage 2 → suggest_mvp() + recommend_tech_stack() in parallel
#  Stage 3 → risk_analysis() alone
#  Stage 4 → search_documents() alone, on-demand, only when current_files is non-empty
#  Final   → LLM generates structured report from workflow_state, no further tool calls
#
#  Why validate_stage_tools() exists (Phase 4):
#  Before Phase 4, `stage` was only a print-label counter — it had no actual
#  power to stop the LLM from calling the wrong tool, or batching tools from
#  multiple stages together. This silently allowed a staging violation that
#  was never reliably caught in Phase 3. validate_stage_tools() closes that
#  gap: every tool_call is checked against STAGE_MAP before execution, and
#  the whole batch is rejected (not executed) if anything is out of place.
#
#  Imports from:
#  - prompts.py           → SYSTEM_PROMPT, FILE_PROMPT
#  - context_manager.py   → get_context()
#  - tools_description.py → tools (Groq tool schema list)
#  - tools.py             → all tool functions
# ============================================================

import os
import json

from groq import Groq
from groq import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    BadRequestError,
    APIStatusError,
    APIConnectionError,
)
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from src.prompts.prompts import SYSTEM_PROMPT, FILE_PROMPT
from src.core.context_manager import get_context
from src.tools.tools_description import tools
from src.tools.tools import (
    search_knowledge_base,
    analyze_market,
    suggest_mvp,
    recommend_tech_stack,
    risk_analysis,
    search_documents,       # RAG vector store query for uploaded PDFs — Stage 4
)


# ── CLIENT SETUP ──────────────────────────────────────────────
# Groq client initialized once at module level — reused across all agent calls.
# load_dotenv() must run before os.getenv() to populate the environment.
# Avoids re-authenticating on every run() call.
#
# Multiple GROQ_API_KEY_N variables exist to allow manual key rotation across
# separate Groq accounts/projects if one key's daily quota is exhausted —
# only one is actually wired up to the client below at a time.

load_dotenv()

GROQ_API_KEY_1 = os.getenv("GROQ_API_KEY_1")
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2")
GROQ_API_KEY_3 = os.getenv("GROQ_API_KEY_3")
GROQ_API_KEY_4 = os.getenv("GROQ_API_KEY_4")
GROQ_API_KEY_5 = os.getenv("GROQ_API_KEY_5")

client = Groq(api_key=GROQ_API_KEY_2)


# ── STAGE GATING (Phase 4) ─────────────────────────────────────

def validate_stage_tools(stage: int, tool_call_list: list, document_access_allowed: bool) -> dict:
    """Validates that every tool the LLM called actually belongs to the current stage.

    The real enforcement mechanism behind the pipeline — replaces the old
    print-only stage counter that had no power to stop incorrect tool calls.
    Called once per loop iteration, immediately after the LLM returns tool_calls
    and before any tool is actually executed.

    Parameters:
        stage                    (int)  → the stage the orchestrator currently expects
        tool_call_list            (list) → raw tool_calls list from the Groq response
        document_access_allowed   (bool) → True only when current_files is non-empty;
                                            gates whether search_documents() may be called at all

    Returns:
        dict → {
            "valid"           : bool — True only if every tool call was correct
                                 AND every required tool for this stage was called,
            "message"         : list — role="tool"/role="user" correction messages,
                                 appended to temp_list so the LLM sees exactly what
                                 went wrong and can self-correct next iteration,
            "missing_tool_call": list — names of required tools the LLM failed to call
        }

    Why whole-batch rejection, not per-tool:
        If one tool call in a batch is wrong, the batch as a whole is not executed.
        Partially executing a batch (running the correct calls, rejecting only the
        wrong ones) would leave workflow_state inconsistently populated for that
        stage — safer to reject everything and let the LLM retry the full stage.

    Why TOOL_TO_STAGE reverse-lookup:
        When a tool is called in the wrong stage (Scenario B below), the rejection
        message needs to tell the LLM which stage it actually belongs to — not just
        that it's wrong. The reverse-lookup makes that message accurate without
        hardcoding stage numbers per tool name.

    Why missing-tool detection uses role="user", not role="system" or role="assistant":
        role="system" messages are meant for one-time identity/instruction setup, not
        per-turn corrections. role="assistant" would mean the LLM is talking to itself,
        which Groq's API does not interpret as a correction. role="user" is the only
        role that reliably reads as "new instruction the LLM must act on now."
    """

    STAGE_MAP = {
        1: ["analyze_market", "search_knowledge_base"],
        2: ["suggest_mvp", "recommend_tech_stack"],
        3: ["risk_analysis"],
        4: ["search_documents"],
    }

    TOOL_TO_STAGE = {tool: stg for stg, stage_tools in STAGE_MAP.items() for tool in stage_tools}
    current_stage_tools = STAGE_MAP.get(stage, [])
    messages = []
    valid = True
    called_current_stage_tools = set()

    # 1. Process every tool the LLM actually called this iteration
    for tool_call in tool_call_list:
        tool_id = tool_call.id
        tool_name = tool_call.function.name

        # Guard: search_documents() is only ever allowed when the user has
        # files available this session. Without this check, the LLM could
        # call it even when there's nothing to search against.
        if tool_name == "search_documents" and not document_access_allowed:
            valid = False
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": (
                    "Error: search_documents is not allowed. "
                    "The user did not request information from uploaded documents."
                )
            })
            continue

        # Scenario A — tool belongs to the current stage
        if tool_name in current_stage_tools:
            called_current_stage_tools.add(tool_name)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": f"Success: '{tool_name}' is correct for Stage {stage}."
            })

        # Scenario B — tool belongs to a different, known stage
        elif tool_name in TOOL_TO_STAGE:
            valid = False
            correct_stage = TOOL_TO_STAGE[tool_name]
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": f"Error: The tool '{tool_name}' does not belong to Stage {stage}. It must only be called during Stage {correct_stage}."
            })

        # Scenario C — tool name not recognized at all (hallucinated)
        else:
            valid = False
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": f"Error: The tool '{tool_name}' is not recognized in this workflow."
            })

    # 2. Check that every required tool for this stage was actually called.
    #    A stage is only complete once ALL its tools have been called —
    #    calling one of two parallel Stage 1 tools is not enough.
    missing_tools = []
    for tool in current_stage_tools:
        if tool not in called_current_stage_tools:
            missing_tools.append(tool)
            valid = False
            messages.append({
                "role": "user",
                "content": f"System Correction: You missed calling '{tool}'. It is required for Stage {stage} and must be executed now."
            })

    return {
        "valid": valid,
        "message": messages,
        "missing_tool_call": missing_tools
    }


# ── AGENT CLASS ───────────────────────────────────────────────

class StartupAgent:
    """Orchestrates the BizRadar AI agentic loop using Groq + tool calling.

    Manages the full ReAct-pattern loop — the LLM decides which tools to call,
    validate_stage_tools() confirms each call belongs to the current stage,
    the agent executes valid calls in parallel, appends results to message
    history, and loops until the LLM produces a final structured report.

    Attributes:
        model_name          (str)  → Groq model ID used for all completions
        messages            (list) → full conversation + tool result history;
                                     grows on every loop iteration
        context_loaded      (bool) → guards get_context() so prior history
                                     loads only once per session, not every turn
        available_functions (dict) → maps tool name strings to callable functions;
                                     used to dispatch LLM tool call requests

    Why one instance per session:
        self.messages accumulates the full conversation history across turns.
        Creating a new instance resets history — intended for fresh sessions only.
    """

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        """Initialises agent state, injects system prompt, and registers tools.

        Parameters:
            model_name (str) → Groq model ID. Defaults to llama-3.3-70b-versatile.

        Flow:
            1. Store model name
            2. Initialise empty message history list
            3. Set context_loaded guard to False
            4. Append system prompt as first message — injected once, never repeated
            5. Build available_functions dispatch map — maps name strings to callables

        Why system prompt in __init__ and not run():
            run() is called on every conversation turn. Appending the system prompt
            inside run() would duplicate it in history on every follow-up question.
            __init__() runs once per session — correct placement for one-time setup.
        """

        # Core session state
        self.model_name     = model_name
        self.messages       = []
        self.context_loaded = False

        # System prompt injected once — Groq expects it as the first message in history
        self.messages.append({"role": "system", "content": SYSTEM_PROMPT})

        # Dispatch map — LLM returns tool name as a string; this resolves it to a callable.
        # summarize_text excluded — it is internal to tools.py, not LLM-callable.
        self.available_functions = {
            "analyze_market":        analyze_market,
            "search_knowledge_base": search_knowledge_base,
            "suggest_mvp":           suggest_mvp,
            "recommend_tech_stack":  recommend_tech_stack,
            "risk_analysis":         risk_analysis,
            "search_documents":      search_documents,
        }


    # ── MAIN AGENT LOOP ───────────────────────────────────────

    def run(self, user_input: str, current_files: str) -> str:
        """Drives the full agentic loop — stage-gated tool calls — until final report.

        Parameters:
            user_input    (str) → raw startup idea or question from the user
            current_files (str) → space/comma-separated list of available uploaded
                                  filenames for this session, or "" if none / not
                                  relevant to this query. Built upstream by
                                  get_available_files(user_input) in rag.py, which
                                  already runs the document-relevance classifier —
                                  by the time this string reaches run(), Stage 4
                                  is either fully unlocked or fully locked for this turn.

        Returns:
            str → final structured report after all stages complete,
                  or an error string if any Groq exception is raised.

        Flow:
            1. Load conversation context once via get_context() — guarded by context_loaded
            2. Append user message to self.messages (permanent history)
            3. Build temp_list — a disposable copy of self.messages for this turn only
            4. If current_files is non-empty, replace temp_list[0] with a fresh
               SYSTEM_PROMPT + FILE_PROMPT combined system message (self.messages[0]
               is never touched — it stays the static SYSTEM_PROMPT permanently)
            5. Stage loop: Groq call → validate_stage_tools() gate → Fan-Out execute
               (if valid) → append results to workflow_state and temp_list →
               advance stage → repeat
            6. Once Stage 3 (or Stage 4, if files exist) completes, generate the
               final report from workflow_state in a single separate Groq call
            7. Extend self.messages with only the NEW turns from temp_list —
               temp_list itself is discarded; only the meaningful conversation
               turns persist into the next call

        Why temp_list instead of operating on self.messages directly:
            current_files can change between turns (the relevance classifier may
            decide differently depending on what the user asks). If FILE_PROMPT
            were injected directly into self.messages[0], that mutation would
            persist into every future turn even when files are no longer relevant.
            temp_list is a throwaway working copy — self.messages[0] stays the
            static SYSTEM_PROMPT across the entire session, and the dynamic
            FILE_PROMPT injection happens fresh, only when needed, every turn.

        Why temp_list[0] = {...} (a new dict) and not temp_list[0]["content"] = X:
            self.messages and temp_list share the same dict objects after .copy()
            — .copy() is shallow. Mutating temp_list[0]["content"] in place would
            silently mutate self.messages[0]["content"] too, permanently corrupting
            the static system prompt. Assigning a brand new dict to temp_list[0]
            replaces the reference in temp_list only — self.messages[0] is untouched.

        Why while True:
            The number of loop iterations is unknown in advance — the LLM decides
            when it has enough information per stage, and validate_stage_tools()
            may force retries. A fixed iteration count would either cut off early
            or fail to allow legitimate retries.

        Why ThreadPoolExecutor (Fan-Out/Fan-In):
            The LLM often requests multiple tools in one response (e.g., Stage 1:
            analyze_market + search_knowledge_base). Running them sequentially
            multiplies latency. Parallel execution cuts wait time to the slowest
            single tool call. future dict maps each Future → {tool_call_id, function_name}
            so results can be appended to the correct role=tool message and stored
            under the correct key in workflow_state.

        Why future is a local variable (not self.future):
            self.future would persist across concurrent run() calls — two rapid
            calls would share and corrupt each other's future dict. A local variable
            resets on every loop iteration, eliminating the concurrency bug.

        Why context_loaded guard:
            get_context() loads prior conversation history from context_manager.py.
            Without the guard, it would reload and re-append history on every
            follow-up question in a multi-turn session, duplicating old messages.

        Why temperature=0.3:
            Low enough to enforce strict tool call ordering. Higher temperatures
            increase the chance of the LLM taking shortcuts, skipping stages,
            batching tools from multiple stages, or hallucinating tool arguments —
            all of which validate_stage_tools() now catches, but a lower temperature
            reduces how often that gate needs to fire at all.

        Why MAX_STAGE_RETRIES = 3:
            Without a retry ceiling, a persistently confused LLM response could
            loop indefinitely on the same stage, burning API quota with no progress.
            3 retries gives the LLM real room to self-correct after a rejection
            message, while still guaranteeing the loop terminates with a clear
            failure message if something is structurally wrong with the prompt
            or the model's behavior that turn.

        Why context is forcibly overwritten in function_args (not LLM-supplied):
            Earlier versions let the LLM construct market_context/mvp_context/
            startup_idea itself when calling Stage 2/3/4 tools. This produced
            hallucinated context — the LLM would sometimes invent plausible-looking
            context instead of using the real Stage 1/2 outputs. Forcibly
            overwriting these three keys in function_args, immediately before
            execution, removes that failure mode entirely: the LLM still decides
            WHEN to call a tool, but never decides WHAT context that tool receives
            for these three specific keys.
        """

        try:

            # Step 1: Load prior conversation history — once per session only
            if not self.context_loaded:
                context = get_context()
                self.context_loaded = True
                for item in context:
                    self.messages.append({"role": item["role"], "content": item["content"]})

            # Step 2: Append current user turn to permanent history
            self.messages.append({"role": "user", "content": user_input})

            # Step 3: Build a disposable working copy for this turn only.
            # length marks where "new" turns begin — used at the end to extend
            # self.messages with only what's actually new from this call.
            length = len(self.messages)
            temp_list = self.messages.copy()

            # workflow_state is the single source of truth for everything each
            # tool returns this turn. The final report is generated entirely
            # from this dict — never from raw LLM tool-call arguments.
            workflow_state = {
                "user_query": user_input,

                "stage_1": {
                    "analyze_market": None,
                    "search_knowledge_base": None
                },

                "stage_2": {
                    "suggest_mvp": None,
                    "recommend_tech_stack": None
                },

                "stage_3": {
                    "risk_analysis": None
                },

                "stage_4": {
                    "search_documents": None
                }
            }

            # Step 4: Conditional file-list injection — only into temp_list[0],
            # never into self.messages[0]. New dict assignment, not in-place
            # mutation — see "Why temp_list[0] = {...}" in the docstring above.
            if current_files:
                file_prompt = FILE_PROMPT.format(current_available_files=current_files)
                temp_list[0] = {
                    "role": "system",
                    "content": SYSTEM_PROMPT + "\n\n" + file_prompt,
                }

            # Step 5: Agentic loop — LLM drives the sequence; validate_stage_tools()
            # gates every tool call against the current stage before execution.
            stage             = 1
            stage_print_flag  = True
            stage_retry_count = 0
            MAX_STAGE_RETRIES = 3

            while True:

                # ── STAGE HEADER ──────────────────────────────
                # stage_print_flag distinguishes a fresh stage print from a
                # gating-retry print, so the terminal never shows a misleading
                # repeated "Stage N — Executing tools..." line during a
                # rejection/retry cycle — retries get their own distinct label.
                if stage in [1, 2, 3]:
                    if stage_print_flag:
                        print(f"\r⚙️  Stage {stage} of 3 — Executing tools...          ")
                        stage_print_flag = False
                    else:
                        print(f"\r🔁 Stage {stage} Retry...               ")

                elif stage == 4 and current_files:
                    if stage_print_flag:
                        print("\r🔍 Stage 4 — Querying your document...               ")
                        stage_print_flag = False
                    else:
                        print("\r🔁 Stage 4 Retry..")

                elif stage == 4 and not current_files:
                    # No files this turn — Stage 4 does not exist for this query.
                    # Skip straight to final report generation.
                    stage = 5
                    continue

                else:
                    # ── FINAL REPORT GENERATION ───────────────
                    # All required stages are complete. Build the final prompt
                    # entirely from workflow_state — never from raw tool-call
                    # arguments — and make one last Groq call with no tools
                    # attached, so the LLM cannot call anything else here.
                    print("\r✍️  All stages complete — Generating final report...  ")

                    final_prompt = f"""USER REQUEST:
{workflow_state['user_query']}

MARKET ANALYSIS:
{workflow_state['stage_1']['analyze_market']}

KNOWLEDGE BASE:
{workflow_state['stage_1']['search_knowledge_base']}

MVP:
{workflow_state['stage_2']['suggest_mvp']}

TECH STACK
{workflow_state['stage_2']['recommend_tech_stack']}

RISK ANALYSIS
{workflow_state['stage_3']['risk_analysis']}

DOCUMENT SEARCH:
{workflow_state['stage_4']['search_documents'] if current_files else "No document referenced"}

Now generate the final Response in structured Format
"""
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": final_prompt},
                        ],
                        model=self.model_name,
                        temperature=0.3,
                        max_completion_tokens=4096,
                    )
                    response_message = response.choices[0].message.content

                    temp_list.append({
                        "role": "assistant",
                        "content": response_message
                    })

                    # ── FINAL ANSWER ──────────────────────────
                    print("   ✅ Report ready.\n")

                    # Step 7: Persist only the NEW turns from this call —
                    # temp_list itself (and its conditional FILE_PROMPT injection)
                    # is discarded once this function returns.
                    self.messages.extend(temp_list[length:])

                    return response_message

                # ── GROQ API CALL ─────────────────────────────
                # Sends temp_list (not self.messages) + tool schemas on every
                # iteration. The LLM reads tool results appended in the previous
                # iteration and decides whether to call more tools or stop.
                response = client.chat.completions.create(
                    messages=temp_list,
                    model=self.model_name,
                    tools=tools,
                    temperature=0.3,
                    max_completion_tokens=4096,
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls or []

                if tool_calls:

                    # ── STAGE GATE ─────────────────────────────
                    # Every tool call must pass validate_stage_tools() before
                    # anything is actually executed. An invalid batch is
                    # rejected entirely — no partial execution.
                    valid_tool_call = validate_stage_tools(
                        stage=stage,
                        tool_call_list=tool_calls,
                        document_access_allowed=bool(current_files)
                    )

                    if not valid_tool_call["valid"]:
                        stage_retry_count += 1

                        if stage_retry_count > MAX_STAGE_RETRIES:
                            return (
                                f"Stage {stage} failed after "
                                f"{MAX_STAGE_RETRIES} retries."
                            )

                        temp_list.extend(valid_tool_call["message"])
                        continue

                    # Valid batch — append the raw assistant message. This must
                    # be preserved as-is (with its tool_calls metadata intact)
                    # so Groq can correctly match the upcoming tool results
                    # back to their originating tool_call_id.
                    temp_list.append(response_message)

                    # ── FAN-OUT ───────────────────────────────
                    # Submit all tool calls from this LLM response simultaneously.
                    # future dict maps each Future object → {tool_call_id, function_name}.
                    # Local variable — resets each iteration, no cross-call corruption.
                    future = {}

                    with ThreadPoolExecutor() as executor:

                        for tool_call in tool_calls:

                            function_name = tool_call.function.name
                            function_to_call = self.available_functions[function_name]
                            function_args = json.loads(tool_call.function.arguments)

                            # =====================================================
                            # Forcibly overwrite shared workflow context.
                            # The LLM decides WHEN to call these tools — it never
                            # decides WHAT context they receive for these specific
                            # keys. This is the fix for the hallucinated-context bug:
                            # earlier versions let the LLM construct this context
                            # itself, which it sometimes did inaccurately.
                            # =====================================================

                            # Stage 2 tools need Stage 1 outputs
                            if function_name in ["suggest_mvp", "recommend_tech_stack"]:
                                function_args["startup_idea"] = workflow_state["user_query"]
                                function_args["market_context"] = (
                                    workflow_state["stage_1"]["analyze_market"][:1000]
                                    + "\n\n"
                                    + workflow_state["stage_1"]["search_knowledge_base"][:1000]
                                )

                            # Stage 3 tool needs Stage 1 + Stage 2 outputs
                            elif function_name == "risk_analysis":
                                function_args["startup_idea"] = workflow_state["user_query"]
                                function_args["market_context"] = (
                                    workflow_state["stage_1"]["analyze_market"]
                                    + "\n\n"
                                    + workflow_state["stage_1"]["search_knowledge_base"]
                                )
                                function_args["mvp_context"] = (
                                    workflow_state["stage_2"]["suggest_mvp"][:1000]
                                )

                            # Stage 4 document search — file_name is currently
                            # LLM-trusted (deliberate, accepted-risk scope decision —
                            # see LEARNING_LOG.md Phase 4 section for rationale;
                            # to be hardened once get_available_files() supports
                            # multi-document summary-based selection).
                            elif function_name == "search_documents":
                                function_args["user_input"] = workflow_state["user_query"]

                            # Submit to thread pool — non-blocking, returns Future immediately.
                            # Gemini RPM throttling handled inside tools.py summarize_text(),
                            # not here — sleep here would delay submission without reducing
                            # actual Gemini API call rate.
                            future[
                                executor.submit(function_to_call, **function_args)
                            ] = {
                                "tool_call_id": tool_call.id,
                                "function_name": function_name
                            }

                            print(f"\r   🔧 {function_name}()                                  ")

                        # ── FAN-IN ────────────────────────────
                        # Collect results as each future completes — not in submission order.
                        # as_completed() yields faster tools first; no tool waits for a slower one.
                        for completed_future in as_completed(future):

                            tool           = future[completed_future]
                            tool_call_id   = tool["tool_call_id"]
                            tool_call_name = tool["function_name"]
                            function_response = completed_future.result(timeout=120)

                            # Store the real result in workflow_state, truncated to
                            # 2000 chars — this is what the final report is built from.
                            workflow_state[f"stage_{stage}"][tool_call_name] = str(function_response)[:2000]

                            # role=tool with matching tool_call_id — required by Groq
                            # message format. Content is intentionally just "completed":
                            # the LLM does not need to re-read the raw tool output here —
                            # it only needs to know the call succeeded so it can proceed
                            # to the next stage. The actual content lives in workflow_state
                            # and is injected once, cleanly, in the final report prompt.
                            temp_list.append({
                                "role": "tool",
                                "content": "completed",
                                "tool_call_id": tool_call_id
                            })

                    print(f"   ✅ Stage {stage} complete.")
                    stage_retry_count = 0
                    stage += 1
                    stage_print_flag = True
                    # Step 6: Loop back — LLM sees tool results and decides next action

                else:
                    # LLM returned no tool calls when tools were still required
                    # for this stage — treat as a retry-worthy failure, not a
                    # silent skip.
                    stage_retry_count += 1

                    if stage_retry_count > MAX_STAGE_RETRIES:
                        return (
                            f"Stage {stage} failed. "
                            f"Model stopped calling tools."
                        )

                    temp_list.append({
                        "role": "user",
                        "content": f"System Correction:\nYou must call all required Stage {stage} tools"
                    })

                    continue

        # ── EXCEPTION HANDLING ────────────────────────────────
        # Each Groq exception maps to a specific failure mode.
        # Returning error strings (not raising) keeps the CLI loop running.

        except AuthenticationError as e:
            return f"Authentication failed. Check your GROQ_API_KEY in .env. Details: {e}"

        except NotFoundError as e:
            return f"Resource not found. Check the model ID string. Details: {e}"

        except RateLimitError as e:
            return f"Rate limit exceeded. Implement backoff retry. Details: {e}"

        except BadRequestError as e:
            return f"Invalid request parameters. Details: {e}"

        except APIStatusError as e:
            return f"Groq API returned an error status ({e.status_code}): {e.message}"

        except APIConnectionError as e:
            return f"Failed to connect to Groq servers. Check internet connection. Details: {e}"

        except Exception as error:
            return f"❌ Agent Error\n\nDetails:\n{str(error)}"