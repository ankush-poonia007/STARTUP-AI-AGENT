class PipelineInitError(Exception):
    """Raised when IntentRouterAgent fails — stops entire pipeline"""

class AgentExecutionError(Exception):
    """Raised when an agent fails after MAX_RETRIES exhausted"""

class ToolConnectionError(Exception):
    """Raised when a tool (Tavily/Groq/Gemini/ChromaDB) is unreachable"""

class WorkflowStateError(Exception):
    """Raised when a required workflow_state key is missing or wrong type"""

# Claude: added NonRetryableError. Previously every exception was
# treated as transient by retry_on_failure, so deterministic failures
# (HTTP 400/401/413, malformed request, invalid schema) were retried
# 3 times and burned a fresh API key on every attempt.
class NonRetryableError(Exception):
    """Raised when a failure cannot succeed on retry — auth, malformed
    request, oversized payload, or invalid schema"""