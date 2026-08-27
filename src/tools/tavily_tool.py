"""
File        : tools/tavily_tool.py
Purpose     : Tavily search wrapper for external market research.

Supported use cases:
    - Web search
    - Startup market research
    - Competitor research
    - Industry research

Current Phase:
    - Uses the configured Tavily API keys through key rotation.
    - Advances to the next key on every call (round-robin, never exhausts).
    - Raises ToolConnectionError when the selected key is rate limited.

Agents should interact with Tavily through the shared tavily_tool instance.
"""

from tavily import TavilyClient

from src.config.settings import (
    TAVILY_API_KEYS,
    TAVILY_MAX_RESULTS,
)
from src.core.exceptions import ToolConnectionError
from src.core.key_rotator import create_key_rotator


class TavilyTool:
    """
    Provide Tavily web search with API-key rotation.
    """

    def __init__(self):
        """
        Initialize the Tavily tool and create its persistent key rotator.
        """
        self._get_next_key = create_key_rotator(
            TAVILY_API_KEYS
        )

    def search(
        self,
        user_query: str
    ) -> list:
        """
        Search the web using Tavily.

        Parameters
        ----------
        user_query : str
            Search query submitted to Tavily.

        Returns
        -------
        list
            Tavily search results.

        Raises
        ------
        ToolConnectionError
            When the selected Tavily API key is rate limited.
        """

        api_key = self._get_next_key()

        client = TavilyClient(
            api_key=api_key
        )

        try:
            response = client.search(
                query=user_query,
                include_answer="advanced",
                search_depth="basic",
                exclude_domains=[
                    "facebook.com",
                    "instagram.com",
                    "x.com",
                    "youtube.com"
                ],
                max_results=TAVILY_MAX_RESULTS
            )

        except Exception as error:
            status_code = getattr(error, "status_code", None)
            error_code = getattr(error, "code", None)

            if (
                status_code == 429
                or error_code == "rate_limit_exceeded"
            ):
                raise ToolConnectionError(
                    "Tavily API key rate limit reached."
                ) from error

            raise

        return response["results"]


tavily_tool = TavilyTool()


if __name__ == "__main__":

    user_input = input(
        "Enter Your Query : "
    ).strip()

    results = tavily_tool.search(
        user_query=user_input
    )

    print(
        f"Results returned: {len(results)}"
    )

    for index, result in enumerate(
        results,
        start=1
    ):
        print(
            f"\nResult {index}:"
        )
        print(
            f"Title: {result.get('title', '')}"
        )
        print(
            f"URL: {result.get('url', '')}"
        )