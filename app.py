# ============================================================
#  app.py — CLI Entry Point for BizRadar AI
# ============================================================
#
#  What this file does:
#  Launches the BizRadar AI command-line interface.
#  Handles startup banner, optional PDF ingestion before the
#  conversation loop, user input collection, agent invocation,
#  response display, and all keyboard interrupt / forced stop events.
#
#  What this file does NOT handle:
#  Does not implement agent logic — that belongs to agent.py.
#  Does not implement RAG pipeline — that belongs to rag.py.
#  Does not manage tool definitions — that belongs to tools.py.
#
#  Flow:
#  Banner → PDF upload prompt (once) → ingestion (if yes) →
#  while True conversation loop → agent.run() → display response
#
#  Keyboard Interrupt Handling:
#  Ctrl+C during input prompt   → clean exit with message
#  Ctrl+C during agent thinking → spinner cleared, clean exit
#  Ctrl+C during PDF ingestion  → partial data warning + clean exit
#  Ctrl+D / EOFError            → funny message + clean exit
#  Normal 'exit' command        → standard goodbye
#
#  Used by:
#  - User → entry point, run with: python app.py
#
#  Imports from:
#  - agent.py           → StartupAgent
#  - context_manager.py → add_message
#  - rag.py             → ingest_pdf(), embed_and_store()
# ============================================================

import sys
import time
import threading

from agent import StartupAgent
from context_manager import add_message
from rag import ingest_pdf, embed_and_store


# ── VISUAL HELPERS ────────────────────────────────────────────

def print_slow(text: str, delay: float = 0.03) -> None:
    """Prints text character by character with a delay for dramatic effect.

    Parameters:
        text  (str)   → text to print
        delay (float) → seconds between each character. Default 0.03s.
    """
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def print_divider(label: str = "", char: str = "─", width: int = 60) -> None:
    """Prints a styled horizontal divider with an optional centered label.

    Parameters:
        label (str) → optional text to center in the divider
        char  (str) → character to use for the divider line
        width (int) → total width of the divider
    """
    if label:
        side = (width - len(label) - 2) // 2
        print(f"\n{char * side} {label} {char * side}\n")
    else:
        print(char * width)


def spinner(stop_event: threading.Event) -> None:
    """Animated spinner that runs in a background thread while agent is thinking.

    Cycles through spinner frames until stop_event is set by the main thread.
    Clears itself from the terminal when stopped.

    Parameters:
        stop_event (threading.Event) → signal to stop the spinner loop
    """
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    while not stop_event.is_set():
        print(f"\r🤖 Thinking... {frames[idx % len(frames)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    # Clear the spinner line after agent returns
    print("\r" + " " * 30 + "\r", end="", flush=True)


def handle_exit(message: str = None) -> None:
    """Prints a clean exit block and terminates the process.

    Single shared exit handler — called from all exit paths to ensure
    consistent formatting regardless of how the session ends.

    Parameters:
        message (str) → optional custom message to display before goodbye.
                        If None, prints the standard goodbye block.
    """
    time.sleep(0.1)
    print_divider(char="━")
    if message:
        print(f"  {message}")
    else:
        print("  Thanks for using BizRadar AI 👋")
        print("  Session ended.")
    print_divider(char="━")
    time.sleep(0.3)
    sys.exit(0)


# ── STARTUP BANNER ────────────────────────────────────────────

def print_banner() -> None:
    """Prints the BizRadar AI ASCII art banner with a slow character reveal."""

    banner_lines = [
        "",
        "  ██████╗ ██╗███████╗    ██████╗  █████╗ ██████╗  █████╗ ██████╗ ",
        "  ██╔══██╗██║╚══███╔╝    ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗",
        "  ██████╔╝██║  ███╔╝     ██████╔╝███████║██║  ██║███████║██████╔╝ ",
        "  ██╔══██╗██║ ███╔╝      ██╔══██╗██╔══██╗██║  ██║██╔══██╗██╔══██╗ ",
        "  ██████╔╝██║███████╗    ██║  ██║██║  ██║██████╔╝██║  ██║██║  ██║ ",
        "  ╚═════╝ ╚═╝╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝",
        "",
        "        AI-Powered Startup Intelligence & Business Analysis",
        "",
    ]

    for line in banner_lines:
        print_slow(line, delay=0.01)

    time.sleep(0.3)
    print("  Type your startup idea to begin. Type 'exit' to quit.\n")
    time.sleep(0.2)


# ── DOCUMENT UPLOAD SECTION ───────────────────────────────────

def handle_document_upload() -> None:
    """Prompts the user for an optional PDF upload and runs the RAG ingestion pipeline.

    Called once at startup — before the conversation loop begins.
    If the user selects YES — collects file path, calls ingest_pdf() to extract
    paragraph chunks, then embed_and_store() to vectorize and persist to ChromaDB.
    If NO — skips ingestion and proceeds directly to the conversation loop.

    Keyboard interrupt handling:
        Ctrl+C during YES/NO prompt → clean exit
        Ctrl+C during file path prompt → clean exit
        Ctrl+C during ingestion → partial data warning + clean exit
        Ctrl+D / EOFError → funny message + clean exit

    Why at startup and not mid-conversation:
        Ingestion is a one-time operation per session. Triggering it at startup
        ensures vectors are ready before the first query hits search_documents().
        Calling this inside the conversation loop would prompt for upload on every turn.
    """

    print_divider("📄 Document Upload", char="═")
    time.sleep(0.1)

    # ── YES/NO PROMPT ─────────────────────────────────────────
    try:
        file_choice = input("  Do you have a document to upload? (YES / NO) : ").lower().strip()

    except KeyboardInterrupt:
        print()
        handle_exit("⚡ Whoa, in a hurry? Session ended.")

    except EOFError:
        print()
        handle_exit("📭 You closed the input stream. Did your keyboard fall asleep? Shutting down.")

    # ── FILE PATH PROMPT ──────────────────────────────────────
    if file_choice == "yes":

        try:
            file_path = input("  Enter your file path : ").strip()

        except KeyboardInterrupt:
            print()
            handle_exit("⚡ Whoa, in a hurry? Session ended.")

        except EOFError:
            print()
            handle_exit("📭 You closed the input stream. Did your keyboard fall asleep? Shutting down.")

        # ── PDF INGESTION ─────────────────────────────────────
        # Ctrl+C during ingestion is caught separately — ChromaDB may have
        # partial data written. User needs to know before exiting.
        try:
            print("\n  📥 Ingesting document...", flush=True)
            time.sleep(0.2)

            # Phase 1 — extract paragraph chunks from PDF
            file_chunks = ingest_pdf(file_path=file_path)

            # Phase 2 — embed chunks and store in ChromaDB
            result = embed_and_store(file_chunks)

            print(f"\n  ✅ {result}")
            time.sleep(0.3)

        except KeyboardInterrupt:
            print()
            print_divider("⚠️  Ingestion Interrupted", char="═")
            print("  ChromaDB may contain partial data from this document.")
            print("  To start clean: delete ./database/chroma_db/ and re-ingest.")
            print_divider(char="═")
            time.sleep(0.5)
            handle_exit("Session ended after interrupted ingestion.")

    else:
        print("\n  ℹ️  No document selected. Web search tools are active.\n")
        time.sleep(0.2)

    print_divider(char="═")
    time.sleep(0.2)


# ── MAIN ENTRY POINT ──────────────────────────────────────────

def main() -> None:
    """Main conversation loop — collects user input, runs the agent, displays response.

    Flow:
        1. Print startup banner
        2. Handle optional PDF ingestion — once, before conversation loop
        3. Instantiate StartupAgent
        4. Enter while True conversation loop:
           a. Collect user input — handle Ctrl+C and Ctrl+D
           b. Start spinner in background thread
           c. Run agent.run() in try/finally — spinner always cleared
           d. Display response
           e. Print turn divider
        5. On 'exit' — print goodbye and break

    Keyboard interrupt handling:
        All interrupt paths lead to handle_exit() for consistent clean shutdown.
        Spinner stop_event is set in finally block — guarantees terminal is clean
        even if agent.run() raises an unexpected exception.
    """

    # ── BANNER ────────────────────────────────────────────────
    print_banner()

    # ── DOCUMENT UPLOAD ───────────────────────────────────────
    # Called once before the conversation loop — not inside the loop.
    # Ensures RAG vectors are ready before the first user query.
    handle_document_upload()

    # ── AGENT INIT ────────────────────────────────────────────
    # Instantiated after upload so RAG vectors are ready before first query
    agent = StartupAgent()
    turn  = 0

    # ── CONVERSATION LOOP ─────────────────────────────────────
    while True:

        # ── INPUT PROMPT ──────────────────────────────────────
        try:
            print("╭─ You")
            user_input = input("╰─▶  ").strip()

        except KeyboardInterrupt:
            print()
            handle_exit("⚡ Caught you trying to escape! Fine. Goodbye.")

        except EOFError:
            print()
            handle_exit("📭 Input stream closed. Even keyboards need a break. Shutting down.")

        # Skip empty input — re-prompt without processing
        if not user_input:
            continue

        # Exit command — clean standard shutdown
        if user_input.lower() == "exit":
            handle_exit()

        # Store user message in conversation history
        add_message("user", user_input)
        turn += 1

        # ── SPINNER + AGENT RUN ───────────────────────────────
        # Spinner runs in a daemon thread — non-blocking while agent thinks.
        # stop_event lives in finally block — guaranteed to stop spinner
        # regardless of whether agent.run() succeeds, errors, or is interrupted.
        stop_event  = threading.Event()
        spin_thread = threading.Thread(target=spinner, args=(stop_event,), daemon=True)

        try:
            time.sleep(0.3)
            spin_thread.start()

            # Blocking call — returns final answer string when all stages complete
            response = agent.run(user_input)

        except KeyboardInterrupt:
            # Ctrl+C while agent is running — stop spinner first, then clean exit
            stop_event.set()
            spin_thread.join()
            print()
            handle_exit("⚡ Analysis aborted mid-flight. Your startup will have to wait.")

        except Exception as e:
            # Styled error block — keeps session alive for next input
            print_divider("❌ Something Went Wrong", char="═")
            print(f"  {e}")
            print_divider(char="═")
            continue

        finally:
            # Always stop spinner — even if exception or interrupt occurred
            # Ensures terminal is never left with a dangling spinner line
            stop_event.set()
            spin_thread.join()

        # Store assistant response in conversation history
        add_message("assistant", response)

        # ── RESPONSE DISPLAY ──────────────────────────────────
        print("\n📊 BizRadar AI:\n")
        print(response)

        time.sleep(0.5)

        # Turn divider — shows turn count for multi-turn sessions
        print_divider(label=f"Turn {turn}", char="─")


# ── RUN ───────────────────────────────────────────────────────
# Standard Python entry point guard — ensures main() only runs
# when app.py is executed directly, not when imported as a module.
# Top-level KeyboardInterrupt catch — handles any Ctrl+C that slips
# past the inner handlers (e.g., during import or banner printing).

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        handle_exit("⚡ You really didn't want to be here, did you? Goodbye.")