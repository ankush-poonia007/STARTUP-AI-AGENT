"""
File        : agents/recommendation_agent.py
Triggered By: full_analysis, nurturing
# Claude: prev -> Tools       : tavily_tool.py + groq_tool.py
# Phase 5 migrated the generation call to Gemini; Tavily is still used.
Tools       : tavily_tool.py + gemini_tool.py

Input:
    workflow_state["startup_idea"]
        Startup idea being evaluated and improved.

    workflow_state["startup_type"]
        Startup category used to construct the competitor-improvement
        search query.

    workflow_state["startup_score"]
        Startup viability assessment produced by StartupScorerAgent.
        Used to identify the highest-risk dimension.

    workflow_state["risk_analysis"]
        Feature-level and business risks identified by RiskAnalystAgent.

Output:
    workflow_state["recommendations"] → list of dicts
        [
            {
                "title"          : str,
                "description"    : str,
                "evidence"       : str,
                "linked_weakness": str
            },
            ...
        ]

    Maximum of 3–5 actionable recommendations.

Responsibilities:
- Run a fresh Tavily search focused on competitor improvement
- Identify actionable startup improvement opportunities
- Use startup context and upstream risk analysis
- Ground recommendations in fresh search evidence
- Link each recommendation to an identified weakness or risk
- Generate structured JSON output
- Parse the LLM-generated JSON response
- Store the final recommendations in workflow state

Design Notes:
- Tavily provides fresh external search evidence.
- Groq generates the recommendations using the supplied startup context.
- The response schema enforces a structured JSON object containing
  the recommendations list.
- Evidence URLs are supplied to the LLM through the Tavily search results.
"""

from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure
)

from src.prompts.prompts import RECOMMENDATION_PROMPT
from src.tools.tavily_tool import tavily_tool
from src.tools.gemini_tool import gemini_tool

import json


class RecommendationAgent:
    """
    Recommendation Agent responsible for converting identified startup
    weaknesses and risks into specific, actionable improvements.

    This agent operates in the full_analysis and nurturing workflows.

    The agent combines:
        - Startup idea
        - Startup type
        - Highest-risk dimension
        - Detailed risk analysis
        - Fresh competitor and improvement research from Tavily

    The generated recommendations are intended to address concrete
    weaknesses rather than provide generic startup advice.

    Input State:
        workflow_state["startup_idea"]:
            Startup idea being evaluated.

        workflow_state["startup_type"]:
            Startup category used for targeted competitor research.

        workflow_state["startup_score"]:
            Startup viability assessment containing the highest-risk flag.

        workflow_state["risk_analysis"]:
            Detailed feature-level and business risks identified upstream.

    External Evidence:
        Tavily performs a fresh competitor-improvement search.
        Its results are supplied to the LLM as supporting evidence.

    Output State:
        workflow_state["recommendations"]:
            List of structured recommendation dictionaries containing:
                - title
                - description
                - evidence
                - linked_weakness

        workflow_state["pipeline_status"]["RecommendationAgent"]:
            Updated to "success" after successful execution.

    Notes:
        Recommendations must be specific, practical, and connected to
        an identified weakness or risk.

        Evidence is supplied through fresh Tavily search results.
        The LLM must use the supplied search URLs rather than inventing
        external sources.
    """

    # ============================================================
    # Structured response schema
    # Defines the exact JSON structure expected from the LLM.
    # ============================================================

    RECOMMENDATION_RESPONSE_FORMAT = {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        },
                        "evidence": {
                            "type": "string"
                        },
                        "linked_weakness": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "title",
                        "description",
                        "evidence",
                        "linked_weakness"
                    ]
                }
            }
        },
        "required": [
            "recommendations"
        ]
    
    }

    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state: dict) -> dict:
        """
        Generate evidence-backed startup improvement recommendations.

        Parameters
        ----------
        workflow_state : dict
            Shared workflow state containing the startup context,
            startup score, risk analysis, and other upstream outputs.

        Returns
        -------
        dict
            Updated workflow state containing the generated
            recommendations and successful pipeline status.

        Processing:
            1. Read startup context and upstream risk information.
            2. Build a competitor-improvement search query.
            3. Retrieve fresh external evidence using Tavily.
            4. Prepare the recommendation system prompt.
            5. Build the user prompt with startup context and search results.
            6. Prepare the LLM message payload.
            7. Generate structured recommendations using Groq.
            8. Parse the returned JSON response.
            9. Store the recommendation list in workflow state.
            10. Mark RecommendationAgent execution as successful.
            11. Return the updated workflow state.

        Notes
        -----
        The LLM receives the startup context, highest-risk flag,
        risk analysis, and fresh Tavily results.

        The structured response is expected to contain a top-level
        "recommendations" field containing the recommendation list.
        """

        # ============================================================
        # 1. Read startup context and upstream analysis
        # ============================================================

        startup_idea = workflow_state["startup_idea"]

        startup_type = workflow_state["startup_type"]

        highest_risk_flag = (
            workflow_state["startup_score"]["highest_risk_flag"]
        )

        risk_analysis = workflow_state["risk_analysis"]

        # ============================================================
        # 2. Build fresh competitor-improvement search query
        # ============================================================

        tavily_prompt = (
            f"how can {startup_type} improve vs competitors"
        )

        # ============================================================
        # 3. Run fresh Tavily search
        # ============================================================

        tavily_response = tavily_tool.search(
            user_query=tavily_prompt
        )

        # ============================================================
        # 4. Prepare recommendation system prompt
        # ============================================================

        system_prompt = RECOMMENDATION_PROMPT

        # ============================================================
        # 5. Build recommendation generation prompt
        # ============================================================

        user_prompt = f"""
Startup Idea: {startup_idea}

Startup Type: {startup_type}

Highest Risk Flag: {highest_risk_flag}

Risk Analysis:
{risk_analysis}

Tavily Search Results:
{chr(10).join([f"- URL: {r['url']}{chr(10)}  Content: {r['content']}" for r in tavily_response])}

Generate the structured recommendation response now.
"""

        # ============================================================
        # 6. Prepare LLM messages
        # ============================================================

        messages = (
            system_prompt +
            "\n\n"+
            user_prompt
        )

        # ============================================================
        # 7. Generate structured recommendations
        # ============================================================

        response = gemini_tool.generate_text(
            user_prompt=messages,
            gemini_model="gemini-3.6-flash",
            json_mode=True,
            response_schema=self.RECOMMENDATION_RESPONSE_FORMAT,
            
        )

        # ============================================================
        # 8. Parse the structured LLM response
        # ============================================================

        data = json.loads(
            response
        )

        # ============================================================
        # 9. Store recommendations in workflow state
        # ============================================================

        workflow_state["recommendations"] = (
            data["recommendations"]
        )

        # ============================================================
        # 10. Update RecommendationAgent pipeline status
        # ============================================================

        workflow_state["pipeline_status"]["RecommendationAgent"] = (
            "success"
        )

        # ============================================================
        # 11. Return the updated workflow state
        # ============================================================

        return workflow_state


# ================================================================
# LOCAL TEST
# Allows RecommendationAgent to be tested independently without
# running the complete BizRadar workflow.
# ================================================================

if __name__ == "__main__":

    # ============================================================
    # 1. Load mock workflow state
    # ============================================================

    from tests.mock_workflow_state import MOCK_STATE_FULL
    import copy

    workflow_state = copy.deepcopy(
        MOCK_STATE_FULL
    )

    # ============================================================
    # 2. Initialize RecommendationAgent
    # ============================================================

    agent = RecommendationAgent()

    # ============================================================
    # 3. Execute recommendation generation
    # ============================================================

    result = agent.run(
        copy.deepcopy(workflow_state)
    )

    # ============================================================
    # 4. Inspect execution result
    # ============================================================

    print("RETURN TYPE:", type(result))
    print("RETURN VALUE:", result)
    print("ERRORS:", workflow_state["errors"])