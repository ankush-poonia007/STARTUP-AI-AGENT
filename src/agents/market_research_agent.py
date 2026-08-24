"""
File        : agents/market_research_agent.py
Triggered By:
    - full_analysis
    - partial_idea
    - nurturing

Tools:
    - tavily_tool.py

Input:
    workflow_state["user_input"]
        Original user-provided startup idea or request.

    workflow_state["startup_idea"]
        Normalized startup concept.

    workflow_state["startup_type"]
        Startup category.

Output:
    workflow_state["market_data"] → str
        Formatted market research containing:
            - Market size and growth
            - Customer demand
            - Competitive landscape
            - Supporting source URLs

Responsibilities:
    - Conduct targeted market research.
    - Research market size and growth.
    - Research customer demand and pain points.
    - Research competitors and market gaps.
    - Use all available startup context when building queries.
    - Execute independent Tavily searches concurrently.
    - Aggregate search results into workflow_state["market_data"].

Execution Flow:
    1. Read startup context from workflow state.
    2. Build three targeted research queries.
    3. Execute Tavily searches concurrently.
    4. Collect completed search results.
    5. Extract title, summary, and URL.
    6. Format the research results.
    7. Store the result in workflow_state["market_data"].
    8. Update pipeline status.
    9. Return the updated workflow state.

Failure Handling:
    Execution logging, timing, retry behavior, and exception handling
    are managed by the shared decorators in src/core/decorators.py.
"""

from src.core.decorators import (
    handle_errors,
    track_timing,
    log_execution,
    retry_on_failure
)

from concurrent.futures import ThreadPoolExecutor, as_completed

from src.tools.tavily_tool import tavily_tool

class MarketResearchAgent:
    """
    Conduct targeted market research for the startup opportunity.

    MarketResearchAgent uses the user's original input together with the
    normalized startup context to perform three focused Tavily searches:

        1. Market Size
        2. Customer Demand
        3. Competitive Landscape

    The three research operations are executed concurrently to reduce
    overall research latency.

    Input State
    -----------
    workflow_state["user_input"]:
        Original startup idea or user request.

    workflow_state["startup_idea"]:
        Normalized startup concept.

    workflow_state["startup_type"]:
        Startup category used to make research queries domain-specific.

    Processing Flow
    ---------------
    1. Read the original user input and normalized startup context.
    2. Build three targeted market research queries.
    3. Submit all three Tavily searches concurrently.
    4. Collect completed futures using as_completed().
    5. Extract title, content, and URL from each search result.
    6. Format the collected evidence into market_data.
    7. Store the final research output in workflow state.
    8. Update MarketResearchAgent execution status.
    9. Return the updated workflow state.

    Output State
    ------------
    workflow_state["market_data"]:
        Formatted market research evidence containing market size,
        customer demand, and competitive landscape findings.

    workflow_state["pipeline_status"]["MarketResearchAgent"]:
        Set to "success" after successful execution.

    Execution Model
    ---------------
    The three Tavily research queries run in parallel using
    ThreadPoolExecutor because they are independent external I/O
    operations.

    Failure Handling
    ----------------
    Execution logging, timing, retry behavior, and exception handling
    are managed centrally by the shared decorators.
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
        Execute targeted market research and update workflow state.

        Parameters
        ----------
        workflow_state : dict
            Shared workflow state containing the original user input,
            normalized startup context, and pipeline status.

        Returns
        -------
        dict
            Updated workflow state containing the formatted market
            research under "market_data".

        Processing Stages
        -----------------
        1. Read startup context from workflow state.
        2. Build market-size, customer-demand, and competition queries.
        3. Execute the three Tavily searches concurrently.
        4. Collect and format completed search results.
        5. Store the combined research in workflow_state["market_data"].
        6. Mark MarketResearchAgent as successful.
        7. Return the updated workflow state.
        """

        # ============================================================
        # 1. Read startup context from workflow state
        # ============================================================

        user_input = workflow_state["user_input"]
        startup_idea = workflow_state["startup_idea"]
        startup_type = workflow_state["startup_type"]

        # ============================================================
        # 2. Build targeted market research queries
        # ============================================================

        market_size_prompt = f"""
Startup: {startup_idea}
Type: {startup_type}
Context: {user_input}

Find actual competitors and alternatives relevant to this startup.

Search for:
- Direct, local, and regional competitors
- Established platforms serving the same customer
- Competitor pricing, positioning, and core offering
- Underserved customer segments and observable market gaps

Prioritize: real businesses, primary sources, geography and customer-relevant results.
Exclude: generic industry articles, unrelated companies.

"""

        demand_prompt = f"""
Startup: {startup_idea}
Type: {startup_type}
Context: {user_input}

Find funding activity relevant to this startup category.

Search for:
- Comparable startups that received funding
- Recent funding rounds, stages, and approximate amounts
- Investors and business models of funded companies
- Geographic relevance and recent investment trends

Prioritize: actual funding announcements, reputable financial publications, startup databases.
Exclude: generic fundraising advice.
"""

        competition_prompt = f"""
Startup: {startup_idea}
Type: {startup_type}
Context: {user_input}

Find existing solutions for this startup's specific problem.

Search for:
- Existing products, services, and how customers currently solve the problem
- Alternative solutions, core features, and service models
- Pricing when available, strengths and weaknesses
- Unserved or underserved needs

Prioritize: solutions relevant to the target customer and geography.
Exclude: generic technology or business articles.
"""

        # ============================================================
        # 3. Execute independent Tavily searches concurrently
        # ============================================================

        with ThreadPoolExecutor() as executor:

            futures = {
                executor.submit(
                    tavily_tool.search,
                    market_size_prompt
                ): "market_size",

                executor.submit(
                    tavily_tool.search,
                    demand_prompt
                ): "demand",

                executor.submit(
                    tavily_tool.search,
                    competition_prompt
                ): "competition",
            }

            # ========================================================
            # 4. Collect completed research results
            # ========================================================

            text = ""

            for completed_future in as_completed(futures):

                result = completed_future.result()
                label = futures[completed_future]

                text += f"\n=== {label} ===\n"

                for item in result:

                    text += f"""Title: {item["title"]}
Summary: {item["content"]}
URL: {item["url"]}

"""

        # ============================================================
        # 5. Store combined market research in workflow state
        # ============================================================

        workflow_state["market_data"] = text

        # ============================================================
        # 6. Update MarketResearchAgent pipeline status
        # ============================================================

        workflow_state["pipeline_status"]["MarketResearchAgent"] = (
            "success"
        )

        # ============================================================
        # 7. Return updated workflow state
        # ============================================================

        return workflow_state


# ================================================================
# STANDALONE TEST
# Allows MarketResearchAgent to be tested independently using
# the shared mock workflow state.
# ================================================================

if __name__ == "__main__":

    from tests.mock_workflow_state import MOCK_STATE_FULL
    
    # ============================================================
    # 1. Load mock workflow state
    # ============================================================

    workflow_state = MOCK_STATE_FULL

    # ============================================================
    # 2. Initialize MarketResearchAgent
    # ============================================================

    agent = MarketResearchAgent()

    # ============================================================
    # 3. Execute market research workflow
    # ============================================================

    workflow_state = agent.run(
        workflow_state
    )

    # ============================================================
    # 4. Display collected market research and errors
    # ============================================================

    print(
        workflow_state["market_data"]
    )
    
    print(
        workflow_state["errors"]
    )
    