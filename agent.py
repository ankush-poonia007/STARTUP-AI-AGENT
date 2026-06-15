# ============================================================
#  agent.py — StartupAgent Orchestrator for BizRadar AI
# ============================================================
#
#  What this file does:
#  Defines the StartupAgent class that drives the full analysis pipeline.
#  Manages the Groq LLM agentic loop — sending messages, receiving tool calls,
#  executing tools in parallel, and feeding results back until a final answer
#  is produced.
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
#  Methods:
#  - __init__()  → sets up model, message history, and available tools map
#  - run()       → drives the LLM loop; handles tool calls and returns final answer
#
#  Used by:
#  - app.py → instantiates StartupAgent and calls run() with user input
#
#  Flow:
#  run(user_input) → load context once → append user message →
#  Groq API call → tool calls? → Fan-Out execute → append results →
#  loop back → no tool calls → return final answer
#
#  Pipeline (3+1 stages):
#  Stage 1 → analyze_market() + search_knowledge_base() in parallel
#  Stage 2 → suggest_mvp() + recommend_tech_stack() in parallel
#  Stage 3 → risk_analysis() alone
#  Stage 4 → search_documents() alone, on-demand, only when user references a document
#  Final   → LLM generates structured report with no further tool calls
#
#  Imports from:
#  - prompts.py           → SYSTEM_PROMPT
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

from prompts import SYSTEM_PROMPT
from context_manager import get_context
from tools_description import tools
from tools import (
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

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


# ── AGENT CLASS ───────────────────────────────────────────────

class StartupAgent:
    """Orchestrates the BizRadar AI agentic loop using Groq + tool calling.

    Manages the full ReAct-pattern loop — the LLM decides which tools to call,
    the agent executes them in parallel, appends results to message history,
    and loops until the LLM produces a final answer with no tool calls.

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

    def run(self, user_input: str) -> str:
        """Drives the full agentic loop — tool calls and all — until final answer.

        Parameters:
            user_input (str) → raw startup idea or question from the user

        Returns:
            str → final LLM answer after all tool calls are resolved,
                  or an error string if any Groq exception is raised.

        Flow:
            1. Load conversation context once via get_context() — guarded by context_loaded
            2. Append user message to history
            3. Call Groq API with full message history and tool schemas
            4. If LLM returns tool calls — Fan-Out: execute all in parallel via ThreadPoolExecutor
            5. Fan-In: append each tool result back to messages as role=tool
            6. Increment stage counter, loop back to Step 3
            7. If LLM returns no tool calls — return the final answer string

        Why while True:
            The number of loop iterations is unknown in advance — the LLM decides
            when it has enough information to stop calling tools. A fixed iteration
            count would either cut off early or waste API calls.

        Why ThreadPoolExecutor (Fan-Out/Fan-In):
            The LLM often requests multiple tools in one response (e.g., Stage 1:
            analyze_market + search_knowledge_base). Running them sequentially
            multiplies latency. Parallel execution cuts wait time to the slowest
            single tool call. future dict maps each Future → tool_call_id so results
            can be appended to the correct role=tool message.

        Why future is a local variable (not self.future):
            self.future would persist across concurrent run() calls — two rapid
            calls would share and corrupt each other's future dict. A local variable
            resets on every loop iteration, eliminating the concurrency bug.

        Why context_loaded guard:
            get_context() loads prior conversation history from context_manager.py.
            Without the guard, it would reload and re-append history on every
            follow-up question in a multi-turn session, duplicating old messages.

        Why temperature=0.3:
            Low enough to enforce strict tool call ordering per TOOL CALL ORDER rules.
            Higher temperatures increase the chance of the LLM taking shortcuts,
            skipping stages, or hallucinating tool arguments.

        Why no time.sleep() between Fan-Out submissions here:
            Gemini RPM throttling is handled inside summarize_text() in tools.py
            via sleep(25) between per-URL Gemini submissions. Adding sleep here
            would delay tool submission without reducing actual Gemini call rate —
            tools run in parallel threads regardless of submission timing.
        """

        try:

            # Step 1: Load prior conversation history — once per session only
            if not self.context_loaded:
                context = get_context()
                self.context_loaded = True
                for item in context:
                    self.messages.append({"role": item["role"], "content": item["content"]})

            # Step 2: Append current user turn to history
            self.messages.append({"role": "user", "content": user_input})

            # Step 3: Agentic loop — LLM drives the sequence; exits when no tool calls remain
            stage = 1
            while True:

                # ── STAGE HEADER ──────────────────────────────
                # Stage 4 is on-demand (search_documents) — label it distinctly
                # so the terminal output clearly separates pipeline from RAG query.
                if stage == 1 or stage == 2 or stage == 3:
                    print(f"\r⚙️  Stage {stage} of 3 — Executing tools...          ")
                elif stage == 4:
                    print("\r🔍 Stage 4 — Querying your document...               ")
                else:
                    print("\r✍️  All stages complete — Generating final report...  ")

                # ── GROQ API CALL ─────────────────────────────
                # Sends full message history + tool schemas on every iteration.
                # The LLM reads tool results appended in the previous iteration
                # and decides whether to call more tools or produce a final answer.
                response = client.chat.completions.create(
                    messages=self.messages,
                    model=self.model_name,
                    tools=tools,
                    temperature=0.3,
                    max_completion_tokens=4096,
                )

                response_message = response.choices[0].message

                # Append raw assistant message — must preserve tool_calls metadata
                # for Groq to correctly match tool results to their call IDs.
                self.messages.append(response_message)

                tool_calls = response_message.tool_calls or []

                if tool_calls:

                    # ── FAN-OUT ───────────────────────────────
                    # Submit all tool calls from this LLM response simultaneously.
                    # future dict maps each Future object → tool_call_id.
                    # Local variable — resets each iteration, no cross-call corruption.
                    future = {}

                    with ThreadPoolExecutor() as executor:

                        for tool_call in tool_calls:

                            function_name = tool_call.function.name

                            # Guard: LLM occasionally hallucinates tool names not in the dispatch map.
                            # Appending a clean error message lets the LLM self-correct on next iteration
                            # instead of crashing with a KeyError swallowed by the outer except.
                            if function_name not in self.available_functions:
                                self.messages.append({
                                    "role":        "tool",
                                    "content":     f"Error: tool '{function_name}' does not exist.",
                                    "tool_call_id": tool_call.id,
                                })
                                continue

                            function_to_call = self.available_functions[function_name]
                            function_args    = json.loads(tool_call.function.arguments)

                            # Submit to thread pool — non-blocking, returns Future immediately.
                            # Gemini RPM throttling handled inside tools.py summarize_text(),
                            # not here — sleep here would delay submission without reducing
                            # actual Gemini API call rate.
                            future[executor.submit(function_to_call, **function_args)] = tool_call.id
                            print(f"\r   🔧 {function_name}()                                  ")

                        # ── FAN-IN ────────────────────────────
                        # Collect results as each future completes — not in submission order.
                        # as_completed() yields faster tools first; no tool waits for a slower one.
                        for completed_future in as_completed(future):
                            tool_call_id      = future[completed_future]
                            function_response = completed_future.result(timeout=120)

                            # role=tool with matching tool_call_id — required by Groq message format.
                            # The LLM reads these on the next iteration to reason about results.
                            self.messages.append({
                                "role":        "tool",
                                "content":     str(function_response),
                                "tool_call_id": tool_call_id,
                            })

                    print(f"   ✅ Stage {stage} complete.")
                    stage += 1
                    # Step 6: Loop back — LLM sees tool results and decides next action

                else:

                    # ── FINAL ANSWER ──────────────────────────
                    # No tool calls in this response — LLM has enough information.
                    # Return the content string as the final structured report.
                    print("   ✅ Report ready.\n")
                    return response_message.content

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