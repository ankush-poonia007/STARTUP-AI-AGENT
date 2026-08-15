"""
File        : tools/groq_tool.py
Purpose     : Global Groq LLM wrapper for all agents.

Supported use cases:
    - Normal text generation
    - Structured JSON generation
    - Strict JSON Schema output
    - Reasoning tasks
    - Low/high temperature generation
    - Long-form report generation

Current Phase:
    - Uses the first configured Groq API key.
    - API-key rotation/cooldown handling is intentionally not implemented yet.
    - Can be added later without changing agent-level calls.

Agents should interact with Groq through this function instead of creating
Groq clients directly.
"""

from groq import Groq

from src.config.settings import (
    GROQ_API_KEYS,
    GROQ_MODEL
)


def text_call(
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
    prompt : list
        Chat messages in Groq/OpenAI message format.

    temperature : float, default=0.3
        Controls response randomness.

    max_completion_tokens : int, default=4096
        Maximum number of completion tokens.

    response_format : dict | None, default=None
        Optional Groq response format.

        Examples:
            Normal text:
                None

            JSON object:
                {
                    "type": "json_object"
                }

            Strict JSON Schema:
                {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "...",
                        "strict": True,
                        "schema": {...}
                    }
                }

    reasoning_effort : str, default="low"
        Reasoning effort requested from the model.

        Supported values depend on the configured Groq model.
        Typical values:
            "low"
            "medium"
            "high"

    include_reasoning : bool, default=False
        Controls whether model reasoning is included in the response.

    top_p : float | None, default=None
        Optional nucleus-sampling parameter.

        None means the parameter is not sent to Groq.

    Returns
    -------
    str
        The model's response content.
    """

    client = Groq(
        api_key=GROQ_API_KEYS[0]
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

    response = client.chat.completions.create(
        **request_parameters
    )

    return response.choices[0].message.content


if __name__ == "__main__":

    messages=[
        {
            "role": "user",
            "content": (
                "What is LangChain and LangGraph? "
                "Differentiate them based on use cases."
            )
        }
    ]
    response = text_call(
        messages=messages
    )

    print(response)