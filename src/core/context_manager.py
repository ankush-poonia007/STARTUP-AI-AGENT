# ============================================================
#  context_manager.py — Conversation History Store for BizRadar AI
# ============================================================
#
#  What this file does:
#  Maintains a module-level conversation history list across turns.
#  Provides add_message() to append new messages and get_context()
#  to retrieve the last 6 messages for injection into the agent loop.
#
#  What this file does NOT handle:
#  Does not persist history to disk — resets on every process restart.
#  Validates role values are "user" or "assistant" — invalid roles rejected with stderr warning.
#  Does not manage the agent's internal messages list — that belongs to agent.py.
#  Does not summarize or compress old history — old messages are simply dropped.
#
#  Functions:
#  - add_message()  → appends a role/content dict to conversation_history
#  - get_context()  → returns the last 6 messages from conversation_history
#
#  Used by:
#  - agent.py → calls get_context() once per session to seed message history,
#               calls add_message() to log each user and assistant turn
#
#  Flow:
#  add_message(role, content) → appends to conversation_history →
#  get_context() → returns [-6:] slice → agent.py injects into messages list
#
#  Why 6 messages:
#  Balances two constraints — context window limits (sending full unbounded
#  history eventually breaks the Groq API token limit) and relevance
#  degradation (old turns distract the LLM from the current analysis).
#  6 covers ~3 full turns (user + assistant each), enough for follow-up
#  coherence without polluting the current pipeline run.
# ============================================================


import sys

# ── HISTORY STORE ─────────────────────────────────────────────
# Module-level list — shared across all calls within a process lifetime.
# Resets to [] on every process restart (no disk persistence).

conversation_history = []

# ── FUNCTIONS ─────────────────────────────────────────────────

def add_message(role: str, content: str) -> None:
    """Appends a single message to the conversation history.

    Parameters:
        role    (str) → message role; must be "user" or "assistant".
                        Invalid values are rejected with a warning — message
                        is not added to history.
                        
        content (str) → message text to store

    Returns:
        None — modifies conversation_history in place

    Flow:
        1. Build a role/content dict
        2. Append to module-level conversation_history list
    """

    # Step 1: Validate role — Groq only accepts "user" or "assistant"
    if role not in ("user", "assistant"):
        print(f"⚠️  Warning: invalid role '{role}' — message not added to history.", file=sys.stderr)        
        return

    # Step 2: Append message dict to shared history
    conversation_history.append({
        "role":    role,
        "content": content,
    })


def get_context() -> list:
    """Returns the last 6 messages from conversation history.

    Parameters:
        None

    Returns:
        list → up to 6 most recent role/content dicts from conversation_history.
               Returns fewer than 6 if history has less than 6 entries.
               Returns [] if history is empty.

    Flow:
        1. Slice conversation_history to last 6 entries
        2. Return the slice

    Concepts used:
        - [-6:] slice → returns last N items from a list; safe on short lists —
                        if len < 6, returns whatever exists without raising IndexError
    """

    # Step 1-2: Return last 6 messages — window size balances token limits vs coherence
    return conversation_history[-6:]
    # Debug: uncomment to verify context size during Phase 4 multi-turn testing
    # context = conversation_history[-6:]
    # print(f"  [context] {len(context)} message(s) loaded.", file=sys.stderr)
    # return context