"""
Every agent run() method wrapped with 4 decorators:

@log_execution    → logs agent name + start time + end time
@track_timing     → records duration to workflow_state["execution_log"]
@retry_on_failure → retries up to MAX_RETRIES on any failure
@handle_errors    → catches ALL exceptions, logs to workflow_state["errors"]

Decorator import chain:
    core/decorators.py imports MAX_RETRIES from config/settings.py
    Agents import decorators from core/decorators.py
    Agents NEVER define retry or error logic themselves

Rules:
- ALL decorator logic lives in core/decorators.py ONLY
- NO retry logic written inside any agent file
- NO try/except blocks inside any agent file
- NO logging code inside any agent file
- Agents stay clean — zero boilerplate
- MAX_RETRIES defined once in settings.py — imported by decorators.py
"""
import time
from functools import wraps
from datetime import datetime, timezone
from src.config.settings import MAX_RETRIES, MIN_COOLTIME_RETRY
from src.core.exceptions import (
    AgentExecutionError,
    ToolConnectionError,
    WorkflowStateError,
    # Claude: added import for the new fail-fast branch in retry_on_failure.
    NonRetryableError
)

def _get_workflow_state(args, kwargs):
    """Resolve workflow_state from keyword or positional arguments."""
    workflow_state = kwargs.get("workflow_state")

    if workflow_state is not None:
        return workflow_state

    if len(args) > 1:
        return args[1]

    print(
        "\n[DECORATOR DEBUG]"
        f"\n  args_count: {len(args)}"
        f"\n  args_types: {[type(arg).__name__ for arg in args]}"
        f"\n  kwargs: {list(kwargs.keys())}"
    )


    raise WorkflowStateError(
        "workflow_state was not provided to the decorated agent."
    )


def _get_agent_name(args, func):
    """Resolve the decorated agent class name safely."""
    if args:
        return args[0].__class__.__name__

    return func.__qualname__.split(".")[0]


def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            return func(*args, **kwargs)

        finally:
            workflow_state = _get_workflow_state(args, kwargs)

            workflow_state["execution_log"].append(
                {
                    "agent_name": _get_agent_name(args, func),
                    "start_time": start_time,
                    "end_time": time.time(),
                }
            )

    return wrapper


def track_timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            return func(*args, **kwargs)

        finally:
            workflow_state = _get_workflow_state(args, kwargs)

            workflow_state["execution_log"].append(
                {
                    "agent_name": _get_agent_name(args, func),
                    "execution_time": time.time() - start_time,
                }
            )

    return wrapper


def retry_on_failure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0

        while True:
            try:
                return func(*args, **kwargs)

            # Claude: added this branch ABOVE the two existing ones.
            # Previously the typed branch and the generic `except Exception`
            # branch had byte-identical bodies, so nothing could opt out of
            # retrying. A deterministic HTTP 400 and a local ValueError both
            # cost 4 attempts, 4 API keys, and 9 seconds before failing.
            # NonRetryableError now fails on the first attempt.
            except NonRetryableError as error:
                raise AgentExecutionError(
                    f"Agent failed with a non-retryable error. "
                    f"Original error: {str(error)}"
                ) from error

            except (
                ToolConnectionError,
                WorkflowStateError,
            ) as error:
                retries += 1

                if retries > MAX_RETRIES:
                    raise AgentExecutionError(
                        f"Agent failed after {MAX_RETRIES} retries. "
                        f"Original error: {str(error)}"
                    ) from error

                time.sleep(MIN_COOLTIME_RETRY)

            except Exception as error:
                retries += 1

                if retries > MAX_RETRIES:
                    raise AgentExecutionError(
                        f"Agent failed after {MAX_RETRIES} retries. "
                        f"Original error: {str(error)}"
                    ) from error

                time.sleep(MIN_COOLTIME_RETRY)

    return wrapper


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        workflow_state = _get_workflow_state(args, kwargs)
        agent_name = _get_agent_name(args, func)

        try:
            return func(*args, **kwargs)

        except Exception as error:
            
            print(
                f"❌ {agent_name} failed: "
                f"{type(error).__name__}: "
                f"{str(error) or repr(error)}"
            )

            workflow_state.setdefault("errors", []).append(
                {
                    "agent": agent_name,
                    "error_type": type(error).__name__,
                    "error": str(error) or repr(error),
                    "timestamp": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )


            # Mark the agent failed so downstream consumers and the
            # report layer can see the gap instead of silently reading
            # the STATE_SCHEMA default.
            workflow_state.setdefault(
                "pipeline_status", {}
            )[agent_name] = "failed"

            # Agents mutate workflow_state in place and return it on
            # success. Returning it here preserves that contract, so
            # the orchestrator's `workflow_state.update(result)` stays
            # a harmless no-op instead of a WorkflowStateError.
            return workflow_state

    return wrapper


# ==========================================
# __main__ Block Simulation
# ==========================================
if __name__ == "__main__":
    # Create an empty shared workflow state object
    state = {
        "execution_log": [],
        "errors": []
    }

    # Set up a sample Agent class utilizing your decorators
    class OperationalAgent:
        def __init__(self):
            self.attempts = 0

        @handle_errors
        @log_execution
        @track_timing
        @retry_on_failure
        def run(self, workflow_state):
            self.attempts += 1
            print(
                f"[{datetime.now(timezone.utc).isoformat()}] "
                f"OperationalAgent: Call attempt #{self.attempts}"
            )
            
            # Simulate a transient Tool connection failure on the first attempt
            if self.attempts < 2:
                raise ToolConnectionError(
                    "Database connection dropped."
                )
                
            return "Task completed successfully!"

    print("--- Positional invocation test ---")
    agent = OperationalAgent()
    print(f"Return payload: {agent.run(state)}")
    print(f"State Logs: {state['execution_log']}")
    print(f"State Errors: {state['errors']}")

    keyword_state = {
        "execution_log": [],
        "errors": [],
    }

    print("\n--- Keyword invocation test ---")
    keyword_agent = OperationalAgent()
    print(
        "Return payload: "
        + str(keyword_agent.run(workflow_state=keyword_state))
    )
    print(f"State Logs: {keyword_state['execution_log']}")
    print(f"State Errors: {keyword_state['errors']}")