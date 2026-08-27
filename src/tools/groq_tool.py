"""
File        : tools/groq_tool.py
Purpose     : Groq LLM wrapper for all agents.

Supported use cases:
    - Normal text generation
    - Structured JSON generation
    - Strict JSON Schema output
    - Reasoning tasks
    - Low/high temperature generation
    - Long-form report generation

Current Phase:
    - Uses the configured Groq API keys through key rotation.
    - Advances to the next key on every call (round-robin, never exhausts).
    - Raises ToolConnectionError when the selected key is rate limited.

Agents should interact with Groq through the shared groq_tool instance.
"""

# from groq import Groq
from openai import OpenAI

from src.config.settings import (
    OPEN_ROUTER_API_KEYS,
    GROQ_MODEL
)
from src.core.exceptions import ToolConnectionError
from src.core.key_rotator import create_key_rotator


class GroqTool:
    """
    Provide Groq text generation with API-key rotation.
    """

    def __init__(self):
        """
        Initialize the Groq tool and create its persistent key rotator.
        """
        self._get_next_key = create_key_rotator(
            OPEN_ROUTER_API_KEYS
        )

    def generate_text(
        self,
        messages: list,
        temperature: float = 0.3,
        max_completion_tokens: int = 4096,
        response_format: dict | None = None,
        reasoning_effort: str = "low",
        include_reasoning: bool = True,
        top_p: float | None = None
    ) -> str:
        """
        Execute a Groq chat completion.

        Parameters
        ----------
        messages : list
            Chat messages in Groq/OpenAI message format.

        temperature : float, default=0.3
            Controls response randomness.

        max_completion_tokens : int, default=4096
            Maximum number of completion tokens.

        response_format : dict | None, default=None
            Optional Groq response format.

        reasoning_effort : str, default="low"
            Reasoning effort requested from the model.

        include_reasoning : bool, default=True
            Controls whether model reasoning is included in the response.

        top_p : float | None, default=None
            Optional nucleus-sampling parameter.

            None means the parameter is not sent to Groq.

        Returns
        -------
        str
            The model's response content.

        Raises
        ------
        ToolConnectionError
            When the selected Groq API key is rate limited.
        """

        api_key = self._get_next_key()
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",   # <-- change from Groq to OpenRouter
            api_key=api_key,                   # your OpenRouter API key
        )


        request_parameters = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
            "reasoning_effort": reasoning_effort,
        }
            # "include_reasoning": include_reasoning

        # ----------------------------------------------------------
        # Optional parameters
        # ----------------------------------------------------------

        if response_format is not None:
            request_parameters["response_format"] = response_format

        if top_p is not None:
            request_parameters["top_p"] = top_p

        # ----------------------------------------------------------
        # Groq API call
        # ----------------------------------------------------------

        try:
            response = client.chat.completions.create(
                **request_parameters
            )

        except Exception as error:
            status_code = getattr(error, "status_code", None)
            error_code = getattr(error, "code", None)

            if (
                status_code == 429
                or error_code == "rate_limit_exceeded"
            ):
                raise ToolConnectionError(
                    "Groq API key rate limit reached."
                ) from error

            raise

        return response.choices[0].message.content


groq_tool = GroqTool()


if __name__ == "__main__":

    messages = [
        {
            "role": "user",
            "content": (
                "What is LangChain and LangGraph? "
                "Differentiate them based on use cases."
                "Explain in short and in table format"
            )
        }
    ]

    response = groq_tool.generate_text(
        messages=messages
    )

    print(response)