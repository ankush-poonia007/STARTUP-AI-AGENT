"""
File        : tools/gemini_tool.py
Purpose     : Gemini wrapper for text generation and embeddings.

Supported use cases:
    - Text generation
    - Text embeddings
    - Startup analysis
    - RAG retrieval
    - Semantic classification

Current Phase:
    - Uses the configured Gemini API keys through key rotation.
    - Rotates to the next key when a rate-limit error occurs.
    - Raises ToolConnectionError when all configured keys are exhausted.

Agents should interact with Gemini through the shared gemini_tool instance.
"""

from google import genai

from src.config.settings import (
    GEMINI_API_KEYS,
    EMBEDDING_MODEL,
    GEMINI_MODEL,
)
from src.core.exceptions import ToolConnectionError
from src.core.key_rotator import create_key_rotator


class GeminiTool:
    """
    Provide Gemini text generation and embedding operations
    with API-key rotation.
    """

    def __init__(self):
        """
        Initialize the Gemini tool and create its persistent key rotator.
        """
        self._get_next_key = create_key_rotator(
            GEMINI_API_KEYS
        )

    def generate_embedding(
        self,
        chunks: list[dict],
    ) -> list:
        """
        Generate embeddings for the supplied text chunks.

        Parameters
        ----------
        chunks : list[dict]
            Chunks containing a "text" field.

        Returns
        -------
        list
            Embedding vectors returned by Gemini.

        Raises
        ------
        ToolConnectionError
            When all configured Gemini API keys are exhausted.
        """
        
        api_key = self._get_next_key()

        print(
            f"🔑 Gemini key selected: ...{api_key[-4:]}"
        )


        text = [
            chunk["text"]
            for chunk in chunks
        ]


        client = genai.Client(
            api_key=api_key
        )

        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text
            )

        except Exception as error:
            
            print(
                f"❌ Gemini key ...{api_key[-4:]} failed"
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
                    "Gemini API key rate limit reached."
                ) from error

            raise

        finally:
            client.close()

        return [
            content.values
            for content in response.embeddings
        ]

    def generate_text(
        self,
        user_prompt,
        gemini_model=GEMINI_MODEL
    ) -> str:
        """
        Generate text using Gemini.

        Parameters
        ----------
        user_prompt : str
            Prompt supplied to the Gemini model.

        gemini_model : str, default=GEMINI_MODEL
            Gemini model used for generation.

        Returns
        -------
        str
            Generated response text.

        Raises
        ------
        ToolConnectionError
            When all configured Gemini API keys are exhausted.
        """

        api_key = self._get_next_key()
        
        print(
            f"🔑 Gemini key selected: ...{api_key[-4:]}"
        )

        client = genai.Client(
            api_key=api_key
        )

        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=user_prompt
            )

        except Exception as error:
            
            print(
                f"❌ Gemini key ...{api_key[-4:]} failed"
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
                    "Gemini API key rate limit reached."
                ) from error

            raise

        finally:
            client.close()

        return response.text


gemini_tool = GeminiTool()


if __name__ == "__main__":

    print("READY\n" + "=" * 20)

    # 1. Test Data for Embeddings
    mock_chunks = [
        {
            "id": 1,
            "text": "Artificial intelligence is transforming technology."
        },
        {
            "id": 2,
            "text": "Python is a versatile programming language."
        }
    ]

    # 2. Test Embedding Generation
    print("Testing generate_embedding()...")

    embed_response = gemini_tool.generate_embedding(
        mock_chunks
    )

    # Verify response structure
    for i, vector in enumerate(embed_response):

        print(
            f"-> Chunk {i + 1} vector length: "
            f"{len(vector)}"
        )

        print(
            f"-> Sample values: "
            f"{vector[:3]}..."
        )

    print("-" * 20)

    # 3. Test Text Generation
    print("Testing generate_text()...")

    test_prompt = (
        "Write a one-sentence greeting to a developer."
    )

    text_response = gemini_tool.generate_text(
        test_prompt
    )

    print(
        f"-> Prompt: '{test_prompt}'"
    )

    print(
        f"-> Response: {text_response.strip()}"
    )