"""
File        : agents/tech_advisor_agent.py
Triggered By: full_analysis, partial_idea
Tools       : groq_tool.py
Input       : workflow_state["market_data"]
Output      : workflow_state["tech_recommendations"]

Output Format:
    workflow_state["tech_recommendations"] → str
        Structured plain text with sections:
            ## Frontend
            ## Backend
            ## Database
            ## Server
            ## Infrastructure
            ## Rationale

        Each choice justified against startup type + market context.

Responsibilities:
- Recommend tech stack aligned to startup type
- Justify each choice against market context
- Prioritize speed to market over complexity
- Suggest lean architecture for small team
"""

from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure
)

from src.prompts.prompts import TECH_ADVISOR_PROMPT
from src.tools.groq_tool import text_call


class TechAdvisorAgent:
    """
    Tech Advisor Agent responsible for recommending a suitable
    technology stack for the startup based on available market data.

    This agent operates as part of the multi-agent workflow and uses
    market_data to understand the startup's product requirements,
    market expectations, technology needs, and relevant ecosystem trends.

    The agent focuses on:
        - Recommending a technology stack aligned with the startup type.
        - Justifying technology choices against the available evidence.
        - Prioritizing speed to market over unnecessary complexity.
        - Suggesting a lean architecture suitable for a small team.

    Input State:
        workflow_state["market_data"]:
            Market research and evidence produced by upstream agents.

    Output State:
        workflow_state["tech_recommendations"]:
            Structured plain-text technology stack recommendation.

        workflow_state["pipeline_status"]["TechAdvisorAgent"]:
            Updated to "success" when the agent completes successfully.

    Notes:
        Market data is used as the evidence source for technology
        recommendations. Source URLs provided in the market data are
        preserved when making externally supported claims.
    """

    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state: dict) -> dict:
        """
        Generate technology stack recommendations from market data.

        Parameters
        ----------
        workflow_state : dict
            Shared state passed between agents in the multi-agent workflow.
            The state must contain "market_data" and "pipeline_status".

        Returns
        -------
        dict
            Updated workflow state containing the generated technology
            recommendations under "tech_recommendations" and the updated
            TechAdvisorAgent execution status.

        Notes
        -----
        The recommendation is based on the startup's actual requirements
        and the technology ecosystem represented by the available market
        evidence.

        Sourced facts are distinguished from technical recommendations,
        and source URLs provided in the market data are not invented,
        modified, or guessed.
        """

        # ----------------------------------------------------
        # 1. Read market research data
        # ----------------------------------------------------

        market_data = workflow_state["market_data"]

        # ----------------------------------------------------
        # 2. Prepare system prompt
        # ----------------------------------------------------

        system_prompt = TECH_ADVISOR_PROMPT

        # ----------------------------------------------------
        # 3. Build user prompt
        # ----------------------------------------------------
        
        user_prompt = f"""
Analyze the following startup market data and recommend the technology stack according to your system instructions.

### MARKET DATA

{market_data}

Use the supplied market evidence to determine the startup's product requirements, current market expectations, technology needs, and relevant ecosystem trends.

Use the source URLs provided in `MARKET DATA` when making externally supported claims. Do not invent, modify, or guess URLs.

Base technology recommendations on the startup's actual requirements and the current technology ecosystem represented by the available evidence. Clearly distinguish sourced facts from your own technical recommendations.

        """

        # ----------------------------------------------------
        # 4. Prepare LLM messages
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
        # 5. Generate technology recommendations
        # ----------------------------------------------------

        tech_stack_response = text_call(
            prompt=messages
        )

        # ----------------------------------------------------
        # 6. Store recommendations in workflow state
        # ----------------------------------------------------

        workflow_state["tech_recommendations"] = (
            tech_stack_response
        )

        # ----------------------------------------------------
        # 7. Update pipeline status
        # ----------------------------------------------------

        workflow_state["pipeline_status"]["TechAdvisorAgent"] = (
            "success"
        )

        # ----------------------------------------------------
        # 8. Return updated workflow state
        # ----------------------------------------------------

        return workflow_state


# ----------------------------------------------------
# LOCAL TEST
# ----------------------------------------------------

if __name__ == "__main__":

    print("=" * 50)

    # ----------------------------------------------------
    # 1. Import the MOCK_STATE_FULL
    # ----------------------------------------------------

    from tests.mock_workflow_state import MOCK_STATE_FULL

    # ----------------------------------------------------
    # 2. Initialize Tech Advisor Agent
    # ----------------------------------------------------

    agent = TechAdvisorAgent()

    # ----------------------------------------------------
    # 3. Run technology recommendation pipeline
    # ----------------------------------------------------

    workflow_state = agent.run(
        MOCK_STATE_FULL.copy()
    )

    # ----------------------------------------------------
    # 4. Print generated recommendations
    # ----------------------------------------------------

    print(
        workflow_state["tech_recommendations"]
    )