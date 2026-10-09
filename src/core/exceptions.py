class PipelineInitError(Exception):
    """Raised when IntentRouterAgent fails — stops entire pipeline"""


class AgentExecutionError(Exception):
    """Raised when an agent fails after MAX_RETRIES exhausted"""


class ToolConnectionError(Exception):
    """Raised when a tool (Tavily/Groq/Gemini/ChromaDB) is unreachable"""


class WorkflowStateError(Exception):
    """Raised when a required workflow_state key is missing or wrong type"""


class NonRetryableError(Exception):
    """Raised when a failure cannot succeed on retry — auth, malformed
    request, oversized payload, or invalid schema"""
   
    
class FileTooLargeError(Exception):
    """Raised when a file exceeds the configured maximum size."""


class UnsupportedFileTypeError(Exception):
    """Raised when a file extension is not supported."""
