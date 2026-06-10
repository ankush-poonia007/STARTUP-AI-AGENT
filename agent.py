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
#  - main.py / cli.py → instantiates StartupAgent and calls run() with user input
#
#  Flow:
#  run(user_input) → load context once → append user message →
#  Groq API call → tool calls? → Fan-Out execute → append results →
#  loop back → no tool calls → return final answer
#
#  Imports from:
#  - prompts.py          → SYSTEM_PROMPT
#  - context_manager.py  → get_context()
#  - tools_description.py → tools (Groq tool schema list)
#  - tools.py            → all six tool functions
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
    summarize_text,
    search_knowledge_base,
    analyze_market,
    suggest_mvp,
    recommend_tech_stack,
    risk_analysis,
    search_documents,       # RAG vector store query for uploaded PDFs
)


# ── CLIENT SETUP ──────────────────────────────────────────────
# Groq client initialized once at module level — reused across all agent calls
# Avoids re-authenticating on every run() call

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


# ── AGENT ─────────────────────────────────────────────────────

class StartupAgent:
    """Orchestrates the BizRadar AI agentic loop using Groq + tool calling.

    Attributes:
        model_name        (str)  → Groq model ID to use for completions
        messages          (list) → full conversation history; grows each loop iteration
        context_loaded    (bool) → guards get_context() so history loads only once
        available_functions (dict) → maps tool name strings to callable functions;
                                     used to dispatch tool calls from the LLM

    Why one instance per session:
        messages accumulates the full conversation history across turns.
        A new instance resets history — intended for fresh sessions only.
    """

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        """Initialises agent state, injects system prompt, and registers tools.

        Parameters:
            model_name (str) → Groq model ID. Defaults to llama-3.3-70b-versatile.

        Flow:
            1. Store model name
            2. Initialise empty message history
            3. Set context_loaded guard to False
            4. Append system prompt as first message — injected once, never repeated
            5. Build available_functions dispatch map
        """

        # Step 1-3: Core state
        self.model_name     = model_name
        self.messages       = []
        self.context_loaded = False

        # Step 4: System prompt goes in first — Groq expects it as the first message
        self.messages.append({"role": "system", "content": SYSTEM_PROMPT})

        # Step 5: Dispatch map — LLM returns tool name as string; this resolves it to callable
        self.available_functions = {
            "analyze_market":        analyze_market,
            "summarize_text":        summarize_text,
            "search_knowledge_base": search_knowledge_base,
            "suggest_mvp":           suggest_mvp,
            "recommend_tech_stack":  recommend_tech_stack,
            "risk_analysis":         risk_analysis,
            "search_documents":      search_documents,      # queries local RAG store — separate from web search
        }


    # ── MAIN AGENT LOOP ───────────────────────────────────────

    def run(self, user_input: str) -> str:
        """Drives the full agentic loop — tool calls and all — until final answer.

        Parameters:
            user_input (str) → raw startup idea or question from the user

        Returns:
            str → final LLM answer after all tool calls are resolved,
                  or an error string if any exception is raised.

        Flow:
            1. Load conversation context once via get_context() — guarded by context_loaded
            2. Append user message to history
            3. Call Groq API with full message history and tool schemas
            4. If LLM returns tool calls — execute all in parallel via ThreadPoolExecutor
            5. Append each tool result back to messages as role=tool
            6. Loop back to Step 3 — LLM sees tool results and decides next action
            7. If LLM returns no tool calls — return the final answer string

        Concepts used:
            - Agentic loop  → LLM drives its own tool call sequence; loop runs until
                              LLM produces a response with no tool calls
            - Fan-Out       → all tool calls in a single LLM response are submitted
                              to ThreadPoolExecutor simultaneously, not sequentially
            - future dict   → maps Future → tool_call_id so results can be matched
                              back to the correct tool call when appending to messages
            - context_loaded guard → prevents get_context() from running on every
                                     turn in a multi-turn session; history loads once

        Why temperature=0.5:
            Low enough for consistent structured output and tool call decisions,
            high enough to avoid repetitive phrasing in the final report.
        """

        try:

            # Step 1: Load prior context into message history — once per session only
            if not self.context_loaded:
                context = get_context()
                self.context_loaded = True

                for item in context:
                    self.messages.append({"role": item["role"], "content": item["content"]})

            # Step 2: Append current user message to history
            self.messages.append({"role": "user", "content": user_input})

            # Step 3: Agentic loop — runs until LLM produces a final answer
            while True:

                # Groq API call — sends full history + tool schemas
                response = client.chat.completions.create(
                    messages=self.messages,
                    model=self.model_name,
                    tools=tools,
                    temperature=0.5,
                    max_completion_tokens=4096,
                )

                response_message = response.choices[0].message

                # Append raw assistant message — preserves tool_calls metadata for Groq
                self.messages.append(response_message)

                tool_calls = response_message.tool_calls or []

                if tool_calls:

                    # Step 4: Fan-Out — submit all tool calls to thread pool simultaneously
                    future = {}

                    with ThreadPoolExecutor() as executor:

                        for tool_call in tool_calls:

                            function_name = tool_call.function.name

                            # Guard against hallucinated tool names from the LLM
                            if function_name not in self.available_functions:
                                self.messages.append({
                                    "role": "tool",
                                    "content": f"Error: tool '{function_name}' does not exist.",
                                    "tool_call_id": tool_call.id,
                                })
                                continue

                            function_to_call = self.available_functions[function_name]
                            function_args   = json.loads(tool_call.function.arguments)

                            # Submit to thread pool — map future → tool_call_id for result matching
                            future[executor.submit(function_to_call, **function_args)] = tool_call.id
                            print(f"🔧 Calling tool: {function_name}")

                        # Step 5: Collect results as futures complete — Fan-In
                        for completed_future in as_completed(future):
                            tool_call_id    = future[completed_future]
                            function_response = completed_future.result(timeout=60)

                            # Append tool result — Groq requires role=tool with matching tool_call_id
                            self.messages.append({
                                "role":        "tool",
                                "content":     str(function_response),
                                "tool_call_id": tool_call_id,
                            })

                    # Step 6: Loop back — LLM sees tool results and decides next action

                else:

                    # Step 7: No tool calls — LLM has produced its final answer
                    return response_message.content

        # Handle bad API keys (401)
        except AuthenticationError as e:
            return f"Authentication failed. Check your GROQ_API_KEY in .env. Details: {e}"

        # Handle bad model name or endpoint (404)
        except NotFoundError as e:
            return f"Resource not found. Check the model ID string. Details: {e}"

        # Handle rate limiting (429)
        except RateLimitError as e:
            return f"Rate limit exceeded. Implement backoff retry. Details: {e}"

        # Handle invalid request payload or parameters (400)
        except BadRequestError as e:
            return f"Invalid request parameters. Details: {e}"

        # Catch-all for other non-2xx HTTP status codes (e.g., 403, 500)
        except APIStatusError as e:
            return f"Groq API returned an error status ({e.status_code}): {e.message}"

        # Network issues, DNS failures, or connection timeouts
        except APIConnectionError as e:
            return f"Failed to connect to Groq servers. Check internet connection. Details: {e}"

        # Unexpected errors — last resort catch
        except Exception as error:
            return f"❌ Agent Error\n\nDetails:\n{str(error)}"