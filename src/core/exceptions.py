class PipelineInitError(Exception):
    """Raised when IntentRouterAgent fails — stops entire pipeline"""

class AgentExecutionError(Exception):
    """Raised when an agent fails after MAX_RETRIES exhausted"""

class ToolConnectionError(Exception):
    """Raised when a tool (Tavily/Groq/Gemini/ChromaDB) is unreachable"""

class WorkflowStateError(Exception):
    """Raised when a required workflow_state key is missing or wrong type"""