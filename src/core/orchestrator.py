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

load_dotenv()

GROQ_API_KEY_1 = os.getenv("GROQ_API_KEY_1")
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2")
GROQ_API_KEY_3 = os.getenv("GROQ_API_KEY_3")
GROQ_API_KEY_4 = os.getenv("GROQ_API_KEY_4")
GROQ_API_KEY_5 = os.getenv("GROQ_API_KEY_5")

client = Groq(api_key=GROQ_API_KEY_3)


def validate_stage_tools( stage: int, tool_call_list: list, document_access_allowed: bool ) -> dict:
    STAGE_MAP = {
        1: ["analyze_market", "search_knowledge_base"],
        2: ["suggest_mvp", "recommend_tech_stack"],
        3: ["risk_analysis"],
        4: ["search_documents"]
    }
    
    TOOL_TO_STAGE = {tool: stg for stg, tools in STAGE_MAP.items() for tool in tools}
    current_stage_tools = STAGE_MAP.get(stage, [])
    messages = []
    valid = True
    called_current_stage_tools = set()

    # 1. Process tools that the LLM actually called
    for tool_call in tool_call_list:
        tool_id = tool_call.id
        tool_name = tool_call.function.name
        
        if ( tool_name == "search_documents" and not document_access_allowed ):
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
        
        # Scenario A: Tool belongs to the current stage (Appends confirmation)
        if tool_name in current_stage_tools:
            called_current_stage_tools.add(tool_name)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": f"Success: '{tool_name}' is correct for Stage {stage}."
            })
            
        # Scenario B: Tool belongs to a different stage
        elif tool_name in TOOL_TO_STAGE:
            valid = False
            correct_stage = TOOL_TO_STAGE[tool_name]
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": f"Error: The tool '{tool_name}' does not belong to Stage {stage}. It must only be called during Stage {correct_stage}."
            })
            
        # Scenario C: Completely unrecognized tool
        else:
            valid = False
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": f"Error: The tool '{tool_name}' is not recognized in this workflow."
            })

    # 2. Check for missing tools from the current stage
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

    def run(self, user_input: str, current_files:str) -> str:
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
            
            length = len(self.messages)
            temp_list = self.messages.copy()
            
            if current_files:
                
                print(
                    f"[DOC ACCESS] Allowed: {bool(current_files)}"
                )
                
                print(
                    f"[DOC ACCESS] Files: {current_files}"
                )
                
                file_prompt = FILE_PROMPT.format(current_available_files= current_files)
                temp_list[0] = {
                    "role":"system", 
                    "content": SYSTEM_PROMPT + "\n\n" + file_prompt,
                    }
                
            # Step 3: Agentic loop — LLM drives the sequence; exits when no tool calls remain
            stage = 1
            stage_print_flag  = True
            while True:

                # ── STAGE HEADER ──────────────────────────────
                # Stage 4 is on-demand (search_documents) — label it distinctly
                # so the terminal output clearly separates pipeline from RAG query.
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
                        
                else:
                    if stage_print_flag:
                        print("\r✍️  All stages complete — Generating final report...  ")
                        stage_print_flag = False
                    else:
                        print(f"\r🔁 Retying the Final Response...               ")

                # ── GROQ API CALL ─────────────────────────────
                # Sends full message history + tool schemas on every iteration.
                # The LLM reads tool results appended in the previous iteration
                # and decides whether to call more tools or produce a final answer.
                response = client.chat.completions.create(
                    messages=temp_list,
                    model=self.model_name,
                    tools=tools,
                    temperature=0.3,
                    max_completion_tokens=4096,
                )

                response_message = response.choices[0].message
                # print(type(response_message))
                # print(len(temp_list))
                # for i in range ( len (temp_list)):
                    # print(type(temp_list[i]))
                # Append raw assistant message — must preserve tool_calls metadata
                # for Groq to correctly match tool results to their call IDs.
                temp_list.append(response_message)
            
                tool_calls = response_message.tool_calls or []
             
                if tool_calls:
                    
                    valid_tool_call = validate_stage_tools( 
                                    stage=stage, 
                                    tool_call_list=tool_calls, 
                                    document_access_allowed=bool(current_files)
                            )
                    
                    # print(valid_tool_call)
                    if not valid_tool_call["valid"]:
                        temp_list.extend(valid_tool_call["message"]) 
                        continue 
                    
                    
                    # ── FAN-OUT ───────────────────────────────
                    # Submit all tool calls from this LLM response simultaneously.
                    # future dict maps each Future object → tool_call_id.
                    # Local variable — resets each iteration, no cross-call corruption.
                    future = {}

                    with ThreadPoolExecutor() as executor:

                        for tool_call in tool_calls:

                            function_name = tool_call.function.name

                            if function_name == "search_documents":
                                print(
                                    f"[DOC TOOL] search_documents requested"
                                )

                            # Guard: LLM occasionally hallucinates tool names not in the dispatch map.
                            # Appending a clean error message lets the LLM self-correct on next iteration
                            # instead of crashing with a KeyError swallowed by the outer except.
                            # if function_name not in self.available_functions:
                            #     temp_list.append({
                            #         "role":        "tool",
                            #         "content":     f"Error: tool '{function_name}' does not exist.",
                            #         "tool_call_id": tool_call.id,
                            #     })
                            #     continue
                            
                            # Above Step can be removed when we apply the valid stage function 
                            
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
                            temp_list.append({
                                "role":        "tool",
                                "content":     str(function_response),
                                "tool_call_id": tool_call_id,
                            })

                    print(f"   ✅ Stage {stage} complete.")
                    stage += 1
                    stage_print_flag = True
                    # Step 6: Loop back — LLM sees tool results and decides next action

                else:

                    # ── FINAL ANSWER ──────────────────────────
                    # No tool calls in this response — LLM has enough information.
                    # Return the content string as the final structured report.
                    print("   ✅ Report ready.\n")
                    
                    self.messages.extend(
                        temp_list[length:]
                    )
                    
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