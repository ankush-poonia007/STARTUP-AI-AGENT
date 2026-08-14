"""
File        : agents/idea_generation_agent.py
Triggered By: idea_exploration
Tools       : tavily_tool.py + groq_tool.py

Input:
    workflow_state["user_input"]
        Original user request, startup interest, problem area,
        or other context used to identify relevant market
        opportunities.

Output:
    workflow_state["generated_ideas"] → list of dicts
        [
            {
                "rank"          : int,  # 1 = highest demand
                "idea"          : str,  # one-line startup concept
                "market_signal" : str,  # why this market is trending
                "source_url"    : str   # Tavily evidence URL
            },
            ...
        ]

        Expected output: 5-10 ranked startup ideas.

Responsibilities:
- Search current market trends and emerging opportunities via Tavily
- Identify customer problems, market demand, and technology trends
- Generate 5-10 startup ideas relevant to the user's input
- Match generated ideas to the user's interests or context
- Rank ideas using available market demand signals
- Ground market signals in fresh Tavily search evidence
- Preserve source URLs returned by Tavily
- Return the generated ideas in the required JSON structure
"""


from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure
)

from src.prompts.prompts import IDEA_GENERATION_PROMPT
from src.tools.tavily_tool import ask_tavily
from src.tools.groq_tool import text_call

import json
import re


class IdeaGenerationAgent:
    """
    Idea Generation Agent responsible for discovering and ranking
    startup opportunities based on current market trends and the
    user's provided input.

    This agent operates in the idea_exploration workflow.

    The agent combines:
        - The user's original input
        - Current market trends
        - Emerging customer needs and pain points
        - Relevant industries and niches
        - New or growing technologies
        - Competitive and business opportunities
        - Market adoption and momentum signals

    Input State:
        workflow_state["user_input"]:
            User-provided startup interest, problem area, or context
            used to guide opportunity discovery.

    External Evidence:
        Tavily is used to retrieve fresh market research covering
        current trends, emerging opportunities, customer problems,
        technologies, and market demand signals.

    Output State:
        workflow_state["generated_ideas"]:
            Ranked list of startup ideas containing the idea itself,
            supporting market signal, rank, and source URL.

        workflow_state["pipeline_status"]["IdeaGenerationAgent"]:
            Updated to "success" when the agent completes successfully.

    Process:
        1. Read the user's input from workflow_state.
        2. Build a market-trend and opportunity search query.
        3. Retrieve fresh evidence using Tavily.
        4. Provide the user's input and search results to Groq.
        5. Generate a ranked JSON list of startup opportunities.
        6. Clean and parse the LLM response.
        7. Store the generated ideas in workflow_state.

    Notes:
        Tavily provides the external market evidence used to identify
        current opportunities.

        The LLM is responsible for interpreting the search evidence,
        generating startup concepts, and ranking them according to
        the available market demand signals.

        Source URLs should come from the Tavily search results and
        should not be invented or modified.
    """

    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state: dict) -> dict:
        """
        Generate and rank startup ideas using fresh market research.

        Parameters
        ----------
        workflow_state : dict
            Shared state passed between agents in the multi-agent workflow.

            Required fields:
                "user_input":
                    User's startup interest, problem area, or context
                    used to guide opportunity discovery.

        Returns
        -------
        dict
            Updated workflow state containing the generated startup
            ideas under "generated_ideas" and the updated
            IdeaGenerationAgent execution status.

        Notes
        -----
        A fresh Tavily search is performed to identify current market
        trends, emerging opportunities, customer problems, relevant
        industries, technologies, and business opportunities.

        The Tavily results are then provided to the Groq model together
        with the user's input.

        The LLM response is expected to contain a ranked JSON array.
        Markdown code fences are removed before parsing the response.

        The resulting parsed data is stored directly under
        workflow_state["generated_ideas"].
        """

        # ----------------------------------------------------
        # 1. Read user input
        # ----------------------------------------------------

        user_input = workflow_state["user_input"]

        # ----------------------------------------------------
        # 2. Build market research search query
        # ----------------------------------------------------

        tavily_prompt = f"""
Find current market trends, emerging opportunities, customer problems,
startup opportunities, and technology trends relevant to:

USER INPUT:
{user_input}

Focus on information that can help evaluate potential startup ideas
related to the user's input.

Prioritize:
- Current market demand and growth signals
- Emerging customer needs or pain points
- Relevant industries and niches
- New or growing technologies
- Competitive or business opportunities
- Evidence of market adoption or momentum

Return multiple relevant search results with their original URLs.
Prefer recent, credible, and directly relevant sources.
"""

        # ----------------------------------------------------
        # 3. Run fresh Tavily search
        # ----------------------------------------------------

        tavily_response = ask_tavily(
            user_query=tavily_prompt
        )

        # ----------------------------------------------------
        # 4. Prepare system prompt
        # ----------------------------------------------------

        system_prompt = IDEA_GENERATION_PROMPT

        # ----------------------------------------------------
        # 5. Build idea generation prompt
        # ----------------------------------------------------

        user_prompt = f"""
USER INPUT:
{user_input}

TAVILY SEARCH RESULTS:
{chr(10).join(
    f"- URL: {result['url']}\n"
    f"  Content: {result['content']}"
    for result in tavily_response
)}

Evaluate the startup opportunities in the search results against the user's input and return the ranked JSON array.
"""

        # ----------------------------------------------------
        # 6. Prepare LLM messages
        # ----------------------------------------------------

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        # ----------------------------------------------------
        # 7. Generate startup ideas
        # ----------------------------------------------------

        groq_response = text_call(
            prompt=messages
        )

        # ----------------------------------------------------
        # 8. Clean accidental Markdown code fences
        # ----------------------------------------------------

        clean_response = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            groq_response.strip(),
            flags=re.IGNORECASE
        )

        # ----------------------------------------------------
        # 9. Parse LLM JSON response
        # ----------------------------------------------------

        data = json.loads(
            clean_response
        )

        # ----------------------------------------------------
        # 10. Store generated ideas in workflow state
        # ----------------------------------------------------

        workflow_state["generated_ideas"] = (
            data
        )

        # ----------------------------------------------------
        # 11. Update pipeline status
        # ----------------------------------------------------

        workflow_state["pipeline_status"]["IdeaGenerationAgent"] = (
            "success"
        )

        # ----------------------------------------------------
        # 12. Return updated workflow state
        # ----------------------------------------------------

        return workflow_state


# ----------------------------------------------------
# LOCAL TEST
# ----------------------------------------------------

if __name__ == "__main__":

    # ----------------------------------------------------
    # 1. Load mock workflow state
    # ----------------------------------------------------

    from tests.mock_workflow_state import MOCK_STATE_FULL

    workflow_state = MOCK_STATE_FULL.copy()

    # ----------------------------------------------------
    # 2. Initialize Idea Generation Agent
    # ----------------------------------------------------

    agent = IdeaGenerationAgent()

    # ----------------------------------------------------
    # 3. Run idea generation pipeline
    # ----------------------------------------------------

    workflow_state = agent.run(
        workflow_state
    )

    # ----------------------------------------------------
    # 4. Print generated startup ideas
    # ----------------------------------------------------

    print(
        workflow_state["generated_ideas"]
    )