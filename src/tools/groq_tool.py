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
    - Rotates to the next key when a rate-limit error occurs.
    - Raises ToolConnectionError when all configured keys are exhausted.

Agents should interact with Groq through the shared groq_tool instance.
"""

from groq import Groq

from src.config.settings import (
    GROQ_API_KEYS,
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
            GROQ_API_KEYS
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
            When all configured Groq API keys are exhausted.
        """

        api_key = self._get_next_key()

        print(
            f"🔑 Groq key selected: ...{api_key[-4:]}"
        )
        
        client = Groq(
            api_key=api_key
        )

        request_parameters = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
            "reasoning_effort": reasoning_effort,
            "include_reasoning": include_reasoning
        }

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
            len_system = len(messages[0]["content"])
            len_user = len(messages[1]["content"])
            print(
                f"📦 Groq request: "
                f"messages={len(messages)}"
                f"system_promtp={len_system}"
                f"user_prompt={len_user}"
                f"comined={len_system+len_user}"
            )
            
            print(messages[1]["content"][:500])
            
            response = client.chat.completions.create(
                **request_parameters
            )

        except Exception as error:
            
            print(
                f"❌ Groq key ...{api_key[-4:]} failed"
            )

            print(
                f"   Error: {type(error).__name__}: {error}"
            )
            
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
            )
        }
    ]

    response = groq_tool.generate_text(
        messages=messages
    )

    print(response)