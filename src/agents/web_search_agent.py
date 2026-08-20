"""
File        : agents/web_search_agent.py
Triggered By:
    - full_analysis
    - partial_idea

Tools:
    - tavily_tool.py

Input:
    workflow_state["user_input"]
        Original user-provided startup idea or request.

    workflow_state["startup_idea"]
        Normalized startup concept.

    workflow_state["startup_type"]
        Startup category used to make search queries domain-specific.

Output:
    workflow_state["web_search_results"] → str
        Formatted external research containing:

            === Competitors ===
            Title: <title>
            Summary: <summary>
            URL: <url>

            === Funding Landscape ===
            Title: <title>
            Summary: <summary>
            URL: <url>

            === Existing Solutions ===
            Title: <title>
            Summary: <summary>
            URL: <url>

Responsibilities:
    - Identify direct and indirect competitors.
    - Research local and regional competitors.
    - Research the funding landscape around the startup category.
    - Identify comparable funded startups and investment activity.
    - Research existing products and alternative solutions.
    - Identify observable market gaps and underserved needs.
    - Return structured search evidence with source URLs.

Why Separate from MarketResearchAgent:
    MarketResearchAgent answers:
        "What is the market?"

    WebSearchAgent answers:
        "Who exists in this market and what solutions already exist?"

    The agents use different research intents so that downstream
    agents receive complementary information rather than duplicated
    market research.

Execution Flow:
    1. Read startup context from workflow state.
    2. Build competitor research query.
    3. Build funding landscape research query.
    4. Build existing-solutions research query.
    5. Execute all three Tavily searches concurrently.
    6. Collect completed search results.
    7. Format titles, summaries, and source URLs.
    8. Store the combined research in workflow state.
    9. Update pipeline status.
    10. Return the updated workflow state.

Failure Handling:
    Execution logging, timing, retry behavior, and exception handling
    are managed centrally by the shared decorators.
"""

from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure
)

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from tests.mock_workflow_state import MOCK_STATE_FULL
from src.tools.tavily_tool import ask_tavily


class WebSearchAgent:
    """
    Conduct targeted external research into competitors, funding
    activity, and existing solutions relevant to the startup.

    WebSearchAgent complements MarketResearchAgent by focusing on
    identifiable businesses, existing solutions, funding activity,
    competitive positioning, and observable market gaps.

    Input State
    -----------
    workflow_state["user_input"]:
        Original startup idea or user request.

    workflow_state["startup_idea"]:
        Normalized startup concept.

    workflow_state["startup_type"]:
        Startup category used to maintain search relevance.

    Processing Model
    ----------------
    Three independent Tavily searches are executed concurrently:

        1. Competitor Research
        2. Funding Landscape Research
        3. Existing Solutions Research

    The searches are independent I/O operations, so they are submitted
    to ThreadPoolExecutor and collected using as_completed().

    Output State
    ------------
    workflow_state["web_search_results"]:
        Formatted external research containing titles, summaries,
        and source URLs.

    workflow_state["pipeline_status"]["WebSearchAgent"]:
        Set to "success" after successful execution.

    Design Principle
    ----------------
    Search results should remain specific to the startup's target
    customer, geography, problem, and category.

    The agent prioritizes actual businesses, real funding activity,
    existing products, and primary or reputable sources instead of
    generic industry content.
    """

    # ============================================================
    # DECORATOR STACK
    # Provides centralized error handling, execution logging,
    # timing measurement, and retry behavior.
    # ============================================================

    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state: dict) -> dict:
        """
        Execute targeted external research and update workflow state.

        Parameters
        ----------
        workflow_state : dict
            Shared workflow state containing the original user input,
            normalized startup context, and pipeline status.

        Returns
        -------
        dict
            Updated workflow state containing formatted competitor,
            funding, and existing-solution research under
            "web_search_results".

        Processing Stages
        -----------------
        1. Read startup context from workflow state.
        2. Build the competitor research prompt.
        3. Build the funding research prompt.
        4. Build the existing-solutions research prompt.
        5. Execute the three Tavily searches concurrently.
        6. Collect completed search results.
        7. Format the returned evidence.
        8. Store the combined research in workflow state.
        9. Mark WebSearchAgent as successful.
        10. Return the updated workflow state.
        """

        # ============================================================
        # 1. Read startup context from workflow state
        # ============================================================

        user_input = workflow_state["user_input"]
        startup_idea = workflow_state["startup_idea"]
        startup_type = workflow_state["startup_type"]

        # ============================================================
        # 2. Build competitor research query
        # ============================================================

        competitor_prompt = f"""
User Input:
{user_input}

Startup Idea:
{startup_idea}

Startup Type:
{startup_type}

Find actual competitors and alternatives relevant to this startup.

Research:
- Direct competitors
- Local and regional competitors
- Established platforms serving the same customer
- Competitor pricing or plans when available
- Their positioning and core offering
- Underserved customer segments
- Observable market gaps

Prioritize real businesses and primary sources.
Do not return generic industry articles or unrelated companies.
Focus on competitors relevant to the startup's geography and target customer.
"""

        # ============================================================
        # 3. Build funding landscape research query
        # ============================================================

        funding_prompt = f"""
User Input:
{user_input}

Startup Idea:
{startup_idea}

Startup Type:
{startup_type}

Research the funding landscape surrounding this startup category.

Find:
- Comparable startups that received funding
- Recent funding rounds
- Funding stage and approximate amount when available
- Investors
- Business models of funded companies
- Geographic relevance
- Recent investment trends

Prioritize actual funding announcements, company sources,
reputable financial publications, and startup databases.
Do not return generic startup fundraising advice.
"""

        # ============================================================
        # 4. Build existing-solutions research query
        # ============================================================

        solutions_prompt = f"""
User Input:
{user_input}

Startup Idea:
{startup_idea}

Startup Type:
{startup_type}

Research existing solutions for this specific startup problem.

Find:
- Existing products and services
- How customers currently solve the problem
- Alternative solutions
- Core features or service models
- Pricing or plans when available
- Strengths and weaknesses
- Unserved or underserved needs

Prioritize solutions directly relevant to the target customer and geography.
Do not return generic technology or business articles.
"""

        # ============================================================
        # 5. Execute independent Tavily searches concurrently
        # ============================================================

        with ThreadPoolExecutor() as executor:

            futures = {
                executor.submit(
                    ask_tavily,
                    competitor_prompt
                ): "Competitor",

                executor.submit(
                    ask_tavily,
                    funding_prompt
                ): "Funding",

                executor.submit(
                    ask_tavily,
                    solutions_prompt
                ): "Solutions",
            }

            # ========================================================
            # 6. Collect completed search results
            # ========================================================

            content = ""

            for completed_futures in as_completed(futures):

                result = completed_futures.result()
                label = futures[completed_futures]

                content += f"""
================================================================================
++++++++++++++++++++++++++++++++  {label}  ++++++++++++++++++++++++++++++++++
================================================================================

"""

                # ====================================================
                # 7. Format each Tavily result
                # ====================================================

                for item in result:

                    content += f"""Title:  {item["title"]}

Summary: {item["content"]}

URL: {item["url"]}
"""

                content += "\n\n"

        # ============================================================
        # 8. Store combined search research in workflow state
        # ============================================================

        workflow_state["web_search_results"] = content

        # ============================================================
        # 9. Update WebSearchAgent pipeline status
        # ============================================================

        workflow_state["pipeline_status"]["WebSearchAgent"] = (
            "success"
        )

        # ============================================================
        # 10. Return updated workflow state
        # ============================================================

        return workflow_state


# ================================================================
# STANDALONE TEST
# Allows WebSearchAgent to be tested independently using the
# shared mock workflow state.
# ================================================================

if __name__ == "__main__":

    # ============================================================
    # 1. Load mock workflow state
    # ============================================================

    workflow_state = MOCK_STATE_FULL

    # ============================================================
    # 2. Initialize WebSearchAgent
    # ============================================================

    agent = WebSearchAgent()

    # ============================================================
    # 3. Execute external research workflow
    # ============================================================

    workflow_state = agent.run(
        workflow_state
    )

    # ============================================================
    # 4. Display collected search research
    # ============================================================

    print(
        workflow_state["web_search_results"]
    )

    # ============================================================
    # 5. Display execution errors, if any
    # ============================================================

    print(
        workflow_state["errors"]
    )