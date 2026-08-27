# ============================================================
# app.py — CLI Entry Point for BizRadar AI
# ============================================================
#
# Phase 5 modular CLI architecture
#
# SessionController
#     ├── SessionState
#     ├── CLIInput
#     ├── CLIPresentation
#     ├── PipelineExecutor
#     ├── ResponseRenderer
#     └── PipelineReporter
#
# OrchestratorAgent remains responsible for the actual
# Phase 5 workflow and workflow_state.
# ============================================================

import sys
import time
import threading
import argparse
import traceback
from dataclasses import dataclass, field
from typing import Any, Iterator

from src.agents.orchestrator_agent import OrchestratorAgent


# ============================================================
# SESSION STATE
# ============================================================

@dataclass
class SessionState:
    """
    Runtime state belonging only to the CLI session.

    This class must not contain workflow/business logic.
    """

    pitch_deck_path: str = ""
    turn: int = 0
    running: bool = True
    current_workflow_state: dict[str, Any] = field(default_factory=dict)

    def increment_turn(self) -> None:
        """Increment the current conversation turn."""
        self.turn += 1

    def set_document(self, path: str) -> None:
        """Set the active document context."""
        self.pitch_deck_path = path.strip()

    def clear_document(self) -> None:
        """Clear the active document context."""
        self.pitch_deck_path = ""

    def set_workflow_state(self, state: dict[str, Any]) -> None:
        """Store the latest workflow state."""
        self.current_workflow_state = state

    def stop(self) -> None:
        """Mark the CLI session as stopped."""
        self.running = False


# ============================================================
# CLI PRESENTATION
# ============================================================

class CLIPresentation:
    """
    Owns terminal presentation only.

    Does not collect input.
    Does not execute the pipeline.
    Does not inspect workflow business logic.
    """

    SPINNER_FRAMES = (
        "⠋", "⠙", "⠹", "⠸", "⠼",
        "⠴", "⠦", "⠧", "⠇", "⠏",
    )

    def print_slow(self, text: str, delay: float = 0.01) -> None:
        """Print text character by character."""
        for char in text:
            print(char, end="", flush=True)
            time.sleep(delay)
        print()

    def print_divider(
        self,
        label: str = "",
        char: str = "─",
        width: int = 70,
    ) -> None:
        """Print a terminal divider."""
        if label:
            side = max(1, (width - len(label) - 2) // 2)
            print(f"\n{char * side} {label} {char * side}\n")
        else:
            print(char * width)

    def print_banner(self) -> None:
        """Display the BizRadar AI startup banner."""

        banner_lines = [
            "",
            "  ██████╗ ██╗███████╗    ██████╗  █████╗ ██████╗  █████╗ ██████╗ ",
            "  ██╔══██╗██║╚══███╔╝    ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗",
            "  ██████╔╝██║  ███╔╝     ██████╔╝███████║██║  ██║███████║██████╔╝",
            "  ██╔══██╗██║ ███╔╝      ██╔══██╗██╔══██╗██║  ██║██╔══██╗██╔══██╗",
            "  ██████╔╝██║███████╗    ██║  ██║██║  ██║██████╔╝██║  ██║██║  ██║",
            "  ╚═════╝ ╚═╝╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝",
            "",
            "        AI-Powered Startup Intelligence & Business Analysis",
            "",
        ]

        for line in banner_lines:
            self.print_slow(line)

        time.sleep(0.2)

        print("  Type your request to begin.")
        print("  Type 'exit' to quit.\n")

    def spinner(self, stop_event: threading.Event) -> None:
        """Display an execution spinner until stopped."""

        index = 0

        while not stop_event.is_set():
            frame = self.SPINNER_FRAMES[index % len(self.SPINNER_FRAMES)]

            print(
                f"\r🤖 Orchestrating... {frame}",
                end="",
                flush=True,
            )

            index += 1
            time.sleep(0.1)

        print(
            "\r" + " " * 40 + "\r",
            end="",
            flush=True,
        )

    def start_spinner(self) -> tuple[threading.Event, threading.Thread]:
        """Start and return the terminal spinner thread."""

        stop_event = threading.Event()

        thread = threading.Thread(
            target=self.spinner,
            args=(stop_event,),
            daemon=True,
        )

        thread.start()

        return stop_event, thread

    @staticmethod
    def stop_spinner(
        stop_event: threading.Event,
        thread: threading.Thread,
    ) -> None:
        """Stop the terminal spinner safely."""
        stop_event.set()
        thread.join()

    def display_response(self, response: str) -> None:
        """Display the final user-facing response."""
        print("\n📊 BizRadar AI:\n")
        print(response)
        print()

    def display_error(self, error: Exception) -> None:
        """Display a recoverable pipeline error."""
        self.print_divider("❌ Pipeline Error", char="═")

        print(
            f"  {type(error).__name__}: {error}"
        )

        self.print_divider(char="═")
        print()

    def display_message(self, message: str) -> None:
        """Display a simple CLI message."""
        print(message)

    def exit(self, message: str | None = None) -> None:
        """Terminate the CLI with consistent formatting."""

        time.sleep(0.1)

        self.print_divider(char="━")

        if message:
            print(f"  {message}")
        else:
            print("  Thanks for using BizRadar AI 👋")
            print("  Session ended.")

        self.print_divider(char="━")

        time.sleep(0.2)

        sys.exit(0)


# ============================================================
# CLI INPUT
# ============================================================

class CLIInput:
    """
    Owns user input collection and command interpretation.

    Does not execute agents.
    Does not modify workflow_state.
    """

    EXIT_COMMANDS = {"exit", "quit"}

    DOCUMENT_COMMANDS = {
        "document",
        "upload",
        "add document",
    }

    CLEAR_DOCUMENT_COMMANDS = {
        "none",
        "clear document",
        "remove document",
    }

    def get_user_input(self) -> str:
        """Collect one user request."""

        try:
            print("╭─ You")
            return input("╰─▶  ").strip()

        except KeyboardInterrupt:
            raise

        except EOFError:
            raise

    def get_document_path(self) -> str:
        """Collect an optional document path."""

        print("\n📄 Optional Document")
        print("  Enter a PDF/pitch-deck path.")
        print("  Press Enter to continue without a document.\n")

        try:
            return input("  Document path: ").strip()

        except KeyboardInterrupt:
            raise

        except EOFError:
            raise

    def is_exit_command(self, user_input: str) -> bool:
        """Check whether input requests session termination."""
        return user_input.lower() in self.EXIT_COMMANDS

    def is_document_command(self, user_input: str) -> bool:
        """Check whether input changes document context."""
        return user_input.lower() in self.DOCUMENT_COMMANDS

    def is_clear_document_command(self, user_input: str) -> bool:
        """Check whether input clears document context."""
        return user_input.lower() in self.CLEAR_DOCUMENT_COMMANDS


# ============================================================
# PIPELINE EXECUTOR
# ============================================================

class PipelineExecutor:
    """
    Executes the Phase 5 orchestrator.

    This class adapts the CLI to OrchestratorAgent.
    It does not format or interpret the returned state.
    """

    def __init__(self, agent: OrchestratorAgent) -> None:
        self.agent = agent

    def execute(
        self,
        user_input: str,
        pitch_deck_path: str,
        presentation: CLIPresentation,
    ) -> dict[str, Any]:
        """
        Execute one request through OrchestratorAgent.

        Presentation is used only for the execution indicator.
        """

        stop_event, spinner_thread = presentation.start_spinner()

        try:
            workflow_state = self.agent.run(
                user_input=user_input,
                pitch_deck_path=pitch_deck_path,
            )

            if not isinstance(workflow_state, dict):
                raise TypeError(
                    "OrchestratorAgent.run() must return a workflow_state dict."
                )

            return workflow_state

        finally:
            presentation.stop_spinner(
                stop_event,
                spinner_thread,
            )


# ============================================================
# RESPONSE RENDERER
# ============================================================

class ResponseRenderer:
    """
    Converts workflow_state into a user-facing response.

    Does not execute agents.
    Does not mutate workflow_state.
    """

    INTENT_OUTPUT_MAP = {
        "full_analysis": "final_report",
        "partial_idea": "final_report",
        "nurturing": "nurtured_idea",
        "advancement": "advancement_plan",
        "general_chat": "chat_response",
    }

    FALLBACK_KEYS = (
        "final_report",
        "chat_response",
        "nurtured_idea",
        "advancement_plan",
    )

    def render(self, workflow_state: dict[str, Any]) -> str:
        """Select the correct user-facing response."""

        intent = workflow_state.get("intent", "")

        if intent == "idea_exploration":
            ideas = workflow_state.get("generated_ideas", [])

            if ideas:
                return self.format_generated_ideas(ideas)

        output_key = self.INTENT_OUTPUT_MAP.get(intent)

        if output_key:
            response = workflow_state.get(output_key, "")

            if isinstance(response, str) and response.strip():
                return response

        return self._fallback(workflow_state)

    def _fallback(self, workflow_state: dict[str, Any]) -> str:
        """Find a usable response when intent-specific output is unavailable."""

        for key in self.FALLBACK_KEYS:
            response = workflow_state.get(key)

            if isinstance(response, str) and response.strip():
                return response

        return (
            "The workflow completed, but no user-facing response "
            "was produced."
        )

    @staticmethod
    def format_generated_ideas(ideas: list) -> str:
        """Format IdeaGenerationAgent output."""

        lines = [
            "# Generated Startup Ideas",
            "",
        ]

        for item in ideas:

            if not isinstance(item, dict):
                lines.append(str(item))
                continue

            rank = item.get("rank", "?")
            idea = item.get("idea", "")
            market_signal = item.get("market_signal", "")
            source_url = item.get("source_url", "")

            lines.append(
                f"## {rank}. {idea}"
            )

            if market_signal:
                lines.append(
                    f"**Market Signal:** {market_signal}"
                )

            if source_url:
                lines.append(
                    f"**Source:** {source_url}"
                )

            lines.append("")

        return "\n".join(lines).strip()


# ============================================================
# PIPELINE REPORTER
# ============================================================

class PipelineReporter:
    """
    Reports execution information from workflow_state.

    This class is presentation-oriented.
    It does not execute or modify the pipeline.
    """

    def __init__(self, presentation: CLIPresentation) -> None:
        self.presentation = presentation

    def display_summary(
        self,
        workflow_state: dict[str, Any],
        turn: int,
    ) -> None:
        """Display a compact pipeline summary."""

        intent = workflow_state.get(
            "intent",
            "unknown",
        )

        status = workflow_state.get(
            "pipeline_status",
            {},
        )

        errors = workflow_state.get(
            "errors",
            [],
        )

        self.presentation.print_divider(
            "⚙️ Pipeline Summary",
            char="─",
        )

        print(f"  Intent : {intent}")

        self._display_agent_status(status)
        self._display_errors(errors)
        self._display_pdf_path(workflow_state)

        self.presentation.print_divider(
            label=f"Turn {turn}",
            char="─",
        )

        print()

    def _display_agent_status(
        self,
        status: dict[str, Any],
    ) -> None:
        """Display agent success/failure counts."""

        if not status:
            return

        successful = sum(
            1
            for value in status.values()
            if value == "success"
        )

        failed = sum(
            1
            for value in status.values()
            if value == "failed"
        )

        skipped = sum(
            1
            for value in status.values()
            if value == "skipped"
        )

        print(
            f"  Agents : "
            f"{successful} successful | "
            f"{failed} failed | "
            f"{skipped} skipped"
        )

    @staticmethod
    def _display_errors(
        errors: list,
    ) -> None:
        """Display pipeline error count."""

        if errors:
            print(
                f"  Errors : {len(errors)} recorded"
            )

    @staticmethod
    def _display_pdf_path(
        workflow_state: dict[str, Any],
    ) -> None:
        """Display generated PDF path when available."""

        pdf_path = workflow_state.get(
            "pdf_path",
            "",
        )

        if pdf_path:
            print(
                f"  PDF    : {pdf_path}"
            )


# ============================================================
# SESSION CONTROLLER
# ============================================================

class SessionController:
    """
    Coordinates the complete CLI session.

    This is the application-level coordinator.

    It does NOT:
        - implement agent logic
        - implement RAG
        - implement intent classification
        - implement business analysis
    """

    def __init__(
        self,
        state: SessionState,
        cli_input: CLIInput,
        presentation: CLIPresentation,
        executor: PipelineExecutor,
        renderer: ResponseRenderer,
        reporter: PipelineReporter,
    ) -> None:

        self.state = state
        self.cli_input = cli_input
        self.presentation = presentation
        self.executor = executor
        self.renderer = renderer
        self.reporter = reporter

    def run(self) -> None:
        """Run the complete interactive CLI session."""

        self.presentation.print_banner()

        while self.state.running:

            try:
                user_input = self.cli_input.get_user_input()

            except KeyboardInterrupt:
                self.presentation.exit(
                    "⚡ Session interrupted. Goodbye."
                )

            except EOFError:
                self.presentation.exit(
                    "📭 Input stream closed. Shutting down."
                )

            if not user_input:
                continue

            if self.cli_input.is_exit_command(user_input):
                self.presentation.exit()

            if self.cli_input.is_document_command(user_input):
                self._set_document_context()
                continue

            if self.cli_input.is_clear_document_command(user_input):
                self._clear_document_context()
                continue

            self._process_request(user_input)

    def _set_document_context(self) -> None:
        """Set the session's active document path."""

        self.presentation.print_divider(
            "📄 Document Context",
            char="═",
        )

        path = self.cli_input.get_document_path()

        if path:
            self.state.set_document(path)

            self.presentation.display_message(
                f"\n  ✅ Document context set: {path}\n"
            )
        else:
            self.state.clear_document()

            self.presentation.display_message(
                "\n  ℹ️ No document selected.\n"
            )

    def _clear_document_context(self) -> None:
        """Clear the active document."""

        self.state.clear_document()

        self.presentation.display_message(
            "\n  ℹ️ Document context cleared.\n"
        )

    def _ensure_document_context(self) -> None:
        """
        Ask for document context when none is active.

        This preserves the behavior of the previous app.py.
        """

        if self.state.pitch_deck_path:
            return

        path = self.cli_input.get_document_path()

        if path:
            self.state.set_document(path)

    def _process_request(self, user_input: str) -> None:
        """Execute one normal user request."""

        self.state.increment_turn()

        self._ensure_document_context()

        try:
            workflow_state = self.executor.execute(
                user_input=user_input,
                pitch_deck_path=self.state.pitch_deck_path,
                presentation=self.presentation,
            )

            self.state.set_workflow_state(
                workflow_state
            )

        except KeyboardInterrupt:
            self.presentation.exit(
                "⚡ Analysis aborted mid-flight. Goodbye."
            )

        except Exception as error:
            self.presentation.display_error(error)
            return

        response = self.renderer.render(
            self.state.current_workflow_state
        )

        self.presentation.display_response(
            response
        )

        self.reporter.display_summary(
            workflow_state=self.state.current_workflow_state,
            turn=self.state.turn,
        )


# ============================================================
# INTEGRATION TEST CASES
# ============================================================

@dataclass(frozen=True)
class IntentTestCase:
    """
    One integration scenario for the Phase 5 intent router.

    expected_intent is validated against the workflow_state returned
    by OrchestratorAgent.
    """

    name: str
    message: str
    expected_intent: str
    document_path: str = ""
    requires_document: bool = False


class StreamTestReporter:
    """
    Streams test progress to the terminal.

    This uses a generator rather than buffering all test results.
    """

    def __init__(self, presentation: CLIPresentation) -> None:
        self.presentation = presentation

    def emit(self, message: str) -> Iterator[str]:
        """Yield a message and print it immediately."""
        print(message, flush=True)
        yield message

    def case_started(self, case: IntentTestCase) -> Iterator[str]:
        yield from self.emit(
            f"\n🧪 [{case.name}]"
        )
        yield from self.emit(
            f"   Input    : {case.message}"
        )
        yield from self.emit(
            f"   Expected : {case.expected_intent}"
        )

        if case.document_path:
            yield from self.emit(
                f"   Document : {case.document_path}"
            )

    def case_result(
        self,
        case: IntentTestCase,
        workflow_state: dict[str, Any],
    ) -> Iterator[str]:
        actual_intent = workflow_state.get(
            "intent",
            "",
        )

        errors = workflow_state.get("errors", [])

        passed = (
            actual_intent == case.expected_intent
            and not errors
        )

        yield from self.emit(
            f"   Actual   : {actual_intent or '<empty>'}"
        )

        yield from self.emit(
            f"   Result   : {'✅ PASS' if passed else '❌ FAIL'}"
        )

        if case.requires_document:
            document_context = workflow_state.get(
                "pitch_deck_text",
                "",
            )

            yield from self.emit(
                "   Doc State: "
                + (
                    "✅ PRESENT"
                    if document_context
                    else "⚠️ EMPTY"
                )
            )

        yield from self.emit(
            "   Errors   : "
            + str(len(workflow_state.get("errors", [])))
        )

        yield from self.emit(
            "   ----------------------------------------"
        )

    def case_error(
        self,
        case: IntentTestCase,
        error: Exception,
    ) -> Iterator[str]:
        yield from self.emit(
            f"   Result   : ❌ ERROR"
        )
        yield from self.emit(
            f"   Error    : {type(error).__name__}: {error}"
        )
        yield from self.emit(
            "   ----------------------------------------"
        )


class IntegrationTestRunner:
    """
    Runs end-to-end Phase 5 intent scenarios through the real
    SessionController dependencies.

    These are integration tests, not unit tests.

    They intentionally exercise:
        user message
            ↓
        OrchestratorAgent
            ↓
        IntentRouterAgent
            ↓
        execution plan
            ↓
        agents
            ↓
        workflow_state
            ↓
        assertions
    """

    TEST_CASES = (
        # User has a concrete idea and requests complete analysis.
        IntentTestCase(
            name="FULL_ANALYSIS",
            message=(
                "I have a startup idea for an AI-powered tiffin "
                "delivery service for college students. "
                "Analyze the market, MVP, technology stack, "
                "competition, and major risks."
            ),
            expected_intent="full_analysis",
        ),

        # User has an incomplete idea and wants help developing it.
        IntentTestCase(
            name="PARTIAL_IDEA",
            message=(
                "I have a rough idea for an AI platform "
                "that helps students find internships, "
                "but I haven't figured out the details yet."
            ),
            expected_intent="partial_idea",
        ),

        # User explicitly lacks an idea and requests new ideas.
        IntentTestCase(
            name="IDEA_EXPLORATION",
            message=(
                "I don't have a startup idea yet. "
                "Suggest promising AI startup ideas "
                "I could realistically build."
            ),
            expected_intent="idea_exploration",
        ),

        # User already has a startup and wants to improve it.
        IntentTestCase(
            name="NURTURING",
            message=(
                "I already run a startup that helps small "
                "businesses automate customer support. "
                "Help me improve the existing business."
            ),
            expected_intent="nurturing",
        ),

        # User has traction and asks about scaling an existing startup.
        IntentTestCase(
            name="ADVANCEMENT",
            message=(
                "My SaaS startup already has paying customers. "
                "How should I scale it into a larger business?"
            ),
            expected_intent="advancement",
        ),

        # User asks a general AI question unrelated to startup analysis.
        IntentTestCase(
            name="GENERAL_CHAT",
            message=(
                "What is the difference between an AI agent "
                "and a traditional chatbot?"
            ),
            expected_intent="general_chat",
        ),

        # User explicitly requests PDF generation.
        IntentTestCase(
            name="PDF_REQUEST",
            message=(
                "Create a PDF report containing my startup "
                "analysis and recommendations."
            ),
            expected_intent="pdf_request",
        ),
    )

    def __init__(
        self,
        executor: PipelineExecutor,
        reporter: StreamTestReporter,
        presentation: CLIPresentation,
    ) -> None:
        self.executor = executor
        self.reporter = reporter
        self.presentation = presentation

    def run_focused(
        self,
        intent: str,
        document_path: str = "",
    ) -> dict[str, Any]:
        """
        Run exactly one intent integration test.

        The selected test is executed through the real
        PipelineExecutor and OrchestratorAgent.
        """

        case = next(
            (
                test_case
                for test_case in self.TEST_CASES
                if test_case.expected_intent == intent
            ),
            None,
        )

        if case is None:
            raise ValueError(
                f"No focused test exists for intent: {intent}"
            )

        if document_path and not case.document_path:
            case = IntentTestCase(
                name=case.name,
                message=case.message,
                expected_intent=case.expected_intent,
                document_path=document_path,
                requires_document=case.requires_document,
            )

        self.presentation.print_divider(
            f"🧪 FOCUSED TEST: {case.name}",
            char="═",
        )

        for _ in self.reporter.case_started(case):
            pass

        try:
            workflow_state = self.executor.execute(
                user_input=case.message,
                pitch_deck_path=case.document_path,
                presentation=self.presentation,
            )

            actual_intent = workflow_state.get(
                "intent",
                "",
            )

            errors = workflow_state.get("errors", [])

            passed = (
                actual_intent == case.expected_intent
                and not errors
            )

            for _ in self.reporter.case_result(
                case,
                workflow_state,
            ):
                pass

            result = {
                "name": case.name,
                "expected": case.expected_intent,
                "actual": actual_intent,
                "passed": passed,
                "error_count": len(
                    workflow_state.get("errors", [])
                ),
                "workflow_state": workflow_state,
            }

        except Exception as error:
            
            traceback.print_exc()
            
            for _ in self.reporter.case_error(
                case,
                error,
            ):
                pass

            result = {
                "name": case.name,
                "expected": case.expected_intent,
                "actual": "",
                "passed": False,
                "error": (
                    f"{type(error).__name__}: {error}"
                ),
            }

        self.presentation.print_divider(
            "📊 FOCUSED TEST RESULT",
            char="═",
        )

        print(
            f"  Test     : {case.name}"
        )
        print(
            f"  Expected : {case.expected_intent}"
        )
        print(
            f"  Actual   : {result.get('actual', '<error>')}"
        )
        print(
            f"  Result   : "
            f"{'✅ PASS' if result['passed'] else '❌ FAIL'}"
        )

        if result.get("error"):
            print(
                f"  Error    : {result['error']}"
            )

        self.presentation.print_divider(
            char="═",
        )

        return result

    def run_all(
        self,
        document_path: str = "",
    ) -> dict[str, Any]:
        """
        Execute every intent scenario.

        Tests continue after failures.
        Errors are printed immediately.
        """

        results: list[dict[str, Any]] = []

        self.presentation.print_divider(
            "🧪 PHASE 5 INTEGRATION TESTS",
            char="═",
        )

        for case in self.TEST_CASES:

            active_case = case

            if (
                document_path
                and not case.document_path
            ):
                active_case = IntentTestCase(
                    name=case.name,
                    message=case.message,
                    expected_intent=case.expected_intent,
                    document_path=document_path,
                    requires_document=case.requires_document,
                )

            yield_from_start = self.reporter.case_started(
                active_case
            )

            for message in yield_from_start:
                _ = message

            try:
                workflow_state = self.executor.execute(
                    user_input=active_case.message,
                    pitch_deck_path=active_case.document_path,
                    presentation=self.presentation,
                )

                actual_intent = workflow_state.get(
                    "intent",
                    "",
                )

                # Claude: added the errors read. run_all was the only pass
                # predicate missing the error gate that run_focused (line
                # ~994) and case_result (line ~769) both apply.
                errors = workflow_state.get("errors", [])

                # Claude: prev -> intent match was the ONLY criterion here:
                #
                #     passed = (
                #         actual_intent
                #         == active_case.expected_intent
                #     )
                #
                # A run could therefore be counted as passed while carrying
                # a full error list. The suite reported "Passed : 4" on a
                # run where all 7 cases had in fact failed, because the
                # per-case renderer applied the gate and this tally did not.
                passed = (
                    actual_intent
                    == active_case.expected_intent
                    and not errors
                )

                for message in self.reporter.case_result(
                    active_case,
                    workflow_state,
                ):
                    _ = message

                results.append(
                    {
                        "name": active_case.name,
                        "expected": active_case.expected_intent,
                        "actual": actual_intent,
                        "passed": passed,
                        "error_count": len(
                            workflow_state.get("errors", [])
                        ),
                    }
                )

            except Exception as error:

                for message in self.reporter.case_error(
                    active_case,
                    error,
                ):
                    _ = message

                results.append(
                    {
                        "name": active_case.name,
                        "expected": active_case.expected_intent,
                        "actual": "",
                        "passed": False,
                        "error": (
                            f"{type(error).__name__}: {error}"
                        ),
                    }
                )

        return self._print_summary(results)

    def _print_summary(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Print and return the aggregate test result."""

        passed = sum(
            1
            for result in results
            if result["passed"]
        )

        failed = len(results) - passed

        self.presentation.print_divider(
            "📊 TEST SUMMARY",
            char="═",
        )

        print(
            f"  Total  : {len(results)}"
        )
        print(
            f"  Passed : {passed}"
        )
        print(
            f"  Failed : {failed}"
        )

        if failed:
            print("\n  Failed cases:")

            for result in results:
                if not result["passed"]:
                    print(
                        f"  ❌ {result['name']}"
                    )

                    if result.get("error"):
                        print(
                            f"     {result['error']}"
                        )
                    else:
                        print(
                            f"     Expected: "
                            f"{result['expected']}"
                        )
                        print(
                            f"     Actual  : "
                            f"{result['actual']}"
                        )
        else:
            print(
                "\n  🎉 All intent tests passed."
            )

        self.presentation.print_divider(
            char="═",
        )

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "results": results,
        }


# ============================================================
# DOCUMENT PASSING TEST
# ============================================================

class DocumentPassingTest:
    """
    Verifies that document context travels from the CLI layer
    into OrchestratorAgent.

    This test requires a real document path.
    """

    def __init__(
        self,
        executor: PipelineExecutor,
        presentation: CLIPresentation,
    ) -> None:
        self.executor = executor
        self.presentation = presentation

    def run(self, document_path: str) -> dict[str, Any]:
        """Execute the document-passing integration test."""

        if not document_path:
            raise ValueError(
                "A document path is required for the document test."
            )

        self.presentation.print_divider(
            "📄 DOCUMENT PASSING TEST",
            char="═",
        )

        message = (
            "Analyze my startup based on the uploaded document."
        )

        print(f"  Message  : {message}")
        print(f"  Document : {document_path}")
        print()

        try:
            workflow_state = self.executor.execute(
                user_input=message,
                pitch_deck_path=document_path,
                presentation=self.presentation,
            )

            pitch_deck_text = workflow_state.get(
                "pitch_deck_text",
                "",
            )

            rag_context = workflow_state.get(
                "rag_context",
                [],
            )

            print(
                "  Pitch deck text : "
                + (
                    "✅ PRESENT"
                    if pitch_deck_text
                    else "⚠️ EMPTY"
                )
            )

            print(
                "  RAG context     : "
                + (
                    f"✅ {len(rag_context)} chunks"
                    if rag_context
                    else "⚠️ EMPTY"
                )
            )

            errors = workflow_state.get(
                "errors",
                [],
            )

            print(
                f"  Errors          : {len(errors)}"
            )

            self.presentation.print_divider(
                char="═",
            )

            return {
                "passed": bool(
                    pitch_deck_text
                    or rag_context
                ),
                "workflow_state": workflow_state,
            }

        except Exception as error:

            self.presentation.print_divider(
                "❌ DOCUMENT TEST ERROR",
                char="═",
            )

            print(
                f"  {type(error).__name__}: {error}"
            )

            self.presentation.print_divider(
                char="═",
            )

            return {
                "passed": False,
                "error": (
                    f"{type(error).__name__}: {error}"
                ),
            }


# ============================================================
# ERROR HANDLING TEST
# ============================================================

class ErrorHandlingTest:
    """
    Verifies that pipeline exceptions reach the CLI layer
    without terminating the complete test suite.

    Uses a controlled executor rather than corrupting real
    agent infrastructure.
    """

    class FailingExecutor:
        """Controlled executor used only for error testing."""

        def execute(
            self,
            user_input: str,
            pitch_deck_path: str,
            presentation: CLIPresentation,
        ) -> dict[str, Any]:
            raise RuntimeError(
                "Controlled Phase 5 test failure."
            )

    def __init__(
        self,
        presentation: CLIPresentation,
    ) -> None:
        self.presentation = presentation

    def run(self) -> bool:
        """Verify controlled pipeline error propagation."""

        self.presentation.print_divider(
            "💥 ERROR HANDLING TEST",
            char="═",
        )

        executor = self.FailingExecutor()

        try:
            executor.execute(
                user_input="Controlled failure test",
                pitch_deck_path="",
                presentation=self.presentation,
            )

        except Exception as error:

            print(
                f"  Caught          : {type(error).__name__}"
            )

            print(
                f"  Error message   : {error}"
            )

            print(
                "  Result          : ✅ PASS"
            )

            self.presentation.print_divider(
                char="═",
            )

            return True

        print(
            "  Result          : ❌ FAIL"
        )

        self.presentation.print_divider(
            char="═",
        )

        return False


# ============================================================
# TEST APPLICATION
# ============================================================

class Phase5TestApplication:
    """
    Entry point for Phase 5 integration testing.

    Supports:
        --test all
        --test intents
        --test document --document <path>
        --test errors
    """

    def __init__(
        self,
        controller: SessionController,
    ) -> None:
        self.controller = controller

        self.presentation = (
            controller.presentation
        )

        self.executor = (
            controller.executor
        )

    def run(
        self,
        test_type: str,
        document_path: str = "",
    ) -> int:
        """Run the selected Phase 5 test mode."""

        focused_intents = {
            "general_chat",
            "full_analysis",
            "partial_idea",
            "idea_exploration",
            "nurturing",
            "advancement",
            "pdf_request",
        }

        # ----------------------------------------------------
        # Focused single-intent test
        # ----------------------------------------------------

        if test_type in focused_intents:

            runner = IntegrationTestRunner(
                executor=self.executor,
                reporter=StreamTestReporter(
                    self.presentation
                ),
                presentation=self.presentation,
            )

            result = runner.run_focused(
                intent=test_type,
                document_path=document_path,
            )

            return 0 if result["passed"] else 1

        # ----------------------------------------------------
        # Complete intent suite
        # ----------------------------------------------------

        if test_type in {"all", "intents"}:

            runner = IntegrationTestRunner(
                executor=self.executor,
                reporter=StreamTestReporter(
                    self.presentation
                ),
                presentation=self.presentation,
            )

            summary = runner.run_all(
                document_path=document_path,
            )

            if test_type == "intents":
                return (
                    0
                    if summary["failed"] == 0
                    else 1
                )

        # ----------------------------------------------------
        # Document test
        # ----------------------------------------------------

        if test_type in {"all", "document"}:

            if not document_path:
                print(
                    "\n❌ Document test requires "
                    "--document <path>.\n"
                )

                if test_type == "document":
                    return 1

            else:
                document_test = DocumentPassingTest(
                    executor=self.executor,
                    presentation=self.presentation,
                )

                result = document_test.run(
                    document_path
                )

                if (
                    test_type == "document"
                    and not result["passed"]
                ):
                    return 1

        # ----------------------------------------------------
        # Error test
        # ----------------------------------------------------

        if test_type in {"all", "errors"}:

            error_test = ErrorHandlingTest(
                presentation=self.presentation,
            )

            passed = error_test.run()

            if (
                test_type == "errors"
                and not passed
            ):
                return 1

        return 0

def create_session_controller() -> SessionController:
    """
    Build the complete CLI dependency graph.

    This function is the composition root.
    """

    state = SessionState()

    presentation = CLIPresentation()

    cli_input = CLIInput()

    agent = OrchestratorAgent()

    executor = PipelineExecutor(
        agent=agent,
    )

    renderer = ResponseRenderer()

    reporter = PipelineReporter(
        presentation=presentation,
    )

    return SessionController(
        state=state,
        cli_input=cli_input,
        presentation=presentation,
        executor=executor,
        renderer=renderer,
        reporter=reporter,
    )

# ============================================================
# CLI ARGUMENTS
# ============================================================

def parse_arguments() -> argparse.Namespace:
    """Parse normal CLI and Phase 5 test-mode arguments."""

    parser = argparse.ArgumentParser(
        description="BizRadar AI Phase 5 CLI"
    )

    parser.add_argument(
        "--test",
        choices={
            "all",
            "intents",
            "general_chat",
            "full_analysis",
            "partial_idea",
            "idea_exploration",
            "nurturing",
            "advancement",
            "pdf_request",
            "document",
            "errors",
        },
        help="Run a focused Phase 5 integration test.",
    )

    parser.add_argument(
        "--document",
        type=str,
        default="",
        help="Document path used by document tests.",
    )

    return parser.parse_args()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:
        controller = create_session_controller()

        args = parse_arguments()

        if args.test:

            test_app = Phase5TestApplication(
                controller=controller,
            )

            exit_code = test_app.run(
                test_type=args.test,
                document_path=args.document,
            )

            sys.exit(exit_code)

        controller.run()

    except KeyboardInterrupt:
        print("\n⚡ Session interrupted. Goodbye.")