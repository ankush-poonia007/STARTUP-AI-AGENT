"""
File        : agents/recommendation_agent.py
Triggered By: full_analysis, nurturing
Tools       : tavily_tool.py + groq_tool.py

Input:
    workflow_state["user_input"]
        Original startup idea or user request used to construct
        the competitor-improvement search query.

    workflow_state["startup_score"]
        Startup viability assessment produced by StartupScorerAgent,
        including the overall score, dimension breakdown, and
        highest-risk flag.

    workflow_state["risk_analysis"]
        Feature-level and business risks identified by
        RiskAnalystAgent.

Output:
    workflow_state["recommendations"] → list of dicts
        [
            {
                "title"         : str,  # short improvement title
                "description"   : str,  # what to improve + why
                "evidence"      : str,  # URL or search evidence
                "linked_weakness": str  # weakness identified upstream
            },
            ...
        ]

        Maximum of 3-5 actionable recommendations.

Responsibilities:
- Run a fresh Tavily search focused on competitor comparison
  and startup improvement opportunities
- Query: "how can [startup type] improve vs competitors"
- Identify actionable improvement opportunities
- Ground recommendations in fresh search evidence
- Tie each recommendation to a specific weakness identified
  by upstream analysis
- Return recommendations in the required JSON structure
- Validate and parse the LLM-generated JSON response
"""

from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure
)

from src.prompts.prompts import RECOMMENDATION_PROMPT
from src.tools.tavily_tool import ask_tavily
from src.tools.groq_tool import text_call

import json
import re


class RecommendationAgent:
    """
    Recommendation Agent responsible for generating actionable startup
    improvements using fresh external research and weaknesses identified
    by upstream agents.

    This agent operates in the full_analysis and nurturing workflows.

    The agent combines:
        - The original startup idea
        - The highest-risk area identified by StartupScorerAgent
        - Detailed risks identified by RiskAnalystAgent
        - Fresh competitor and improvement research from Tavily

    The purpose of the agent is to convert identified weaknesses into
    concrete, evidence-backed recommendations rather than generating
    generic startup advice.

    Input State:
        workflow_state["user_input"]:
            Original startup idea or user request.

        workflow_state["startup_score"]:
            Quantitative startup assessment containing the overall score,
            dimension breakdown, and highest-risk flag.

        workflow_state["risk_analysis"]:
            Detailed feature-level and business risk analysis.

    External Evidence:
        Tavily is queried with a competitor-focused improvement question.
        The returned search results are provided to the LLM as supporting
        evidence for recommendation generation.

    Output State:
        workflow_state["recommendations"]:
            List of structured recommendation dictionaries containing
            a title, description, evidence, and linked weakness.

        workflow_state["pipeline_status"]["RecommendationAgent"]:
            Updated to "success" when the agent completes successfully.

    Notes:
        Recommendations should be specific and actionable.

        Each recommendation should be grounded in fresh search evidence
        and connected to a weakness identified by the upstream analysis.
        The agent should not invent evidence or unsupported URLs.
    """

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
            Shared state passed between agents in the multi-agent workflow.

            Required fields:
                "user_input":
                    Original startup idea or user request.

                "startup_score":
                    Startup viability assessment and highest-risk flag.

                "risk_analysis":
                    Detailed risks identified by RiskAnalystAgent.

        Returns
        -------
        dict
            Updated workflow state containing the generated
            recommendations under "recommendations" and the updated
            RecommendationAgent execution status.

        Notes
        -----
        The agent first performs a fresh Tavily search focused on how
        the startup can improve relative to competitors.

        The search results, highest-risk flag, and risk analysis are then
        supplied to the Groq model to generate structured recommendations.

        The LLM response is cleaned of accidental Markdown code fences,
        parsed as JSON, and stored in the workflow state.
        """

        # ----------------------------------------------------
        # 1. Read startup context and upstream analysis
        # ----------------------------------------------------

        user_input = workflow_state["user_input"]

        highest_risk_flag = (
            workflow_state["startup_score"]["highest_risk_flag"]
        )

        risk_analysis = workflow_state["risk_analysis"]

        # ----------------------------------------------------
        # 2. Build fresh competitor-improvement search query
        # ----------------------------------------------------

        tavily_prompt = (
            f"how can {user_input} improve vs competitors"
        )

        # ----------------------------------------------------
        # 3. Run fresh Tavily search
        # ----------------------------------------------------

        tavily_response = ask_tavily(
            user_query=tavily_prompt
        )

        # ----------------------------------------------------
        # 4. Prepare system prompt
        # ----------------------------------------------------

        system_prompt = RECOMMENDATION_PROMPT

        # ----------------------------------------------------
        # 5. Build recommendation generation prompt
        # ----------------------------------------------------

        user_prompt = f"""
Startup:
{user_input}

Highest Risk Flag:
{highest_risk_flag}

Risk Analysis:
{risk_analysis}

Search Results:
{chr(10).join([f"- URL: {r['url']}{chr(10)}  Content: {r['content']}" for r in tavily_response])}

Generate the JSON recommendation array now.
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
        # 7. Generate recommendations
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
        # 10. Store recommendations in workflow state
        # ----------------------------------------------------

        workflow_state["recommendations"] = (
            data
        )

        # ----------------------------------------------------
        # 11. Update pipeline status
        # ----------------------------------------------------

        workflow_state["pipeline_status"]["RecommendationAgent"] = (
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
    # 1. Prepare mock workflow state
    # ----------------------------------------------------

    MOCK_STATE_RECOMMENDATION = {

        # ── INPUTS ──────────────────────────────────────────

        "user_input": "AI-powered tiffin delivery platform for college students",

        "pitch_deck_text": [],

        # ── LLM AS JUDGE ────────────────────────────────────

        "judge_feedback": {
            "mid_pipeline": "",
            "final": ""
        },

        # ── INTENT & PLAN ───────────────────────────────────

        "intent": "",

        "execution_plan": [],

        # ── AGENT OUTPUTS ───────────────────────────────────

        "market_data": "",

        "web_search_results": "",

        "rag_context": [],

        "mvp_suggestions": "",

        "tech_recommendations": "",

        "risk_analysis": """
## Feature Risks

### Feature: Weekly Tiffin Subscription
Risk: Customer churn if meal quality or menu variety is inconsistent.
Why: Students may switch providers when meals become repetitive or unreliable.
Impact: High
Mitigation: Introduce menu rotation, quality monitoring, and subscription feedback loops.

### Feature: Scheduled Meal Delivery
Risk: Late or missed deliveries can reduce customer trust.
Why: Students depend on predictable meal timing around classes and schedules.
Impact: High
Mitigation: Start with limited delivery zones, defined delivery windows, and operational tracking.

### Feature: Digital Payments
Risk: Payment failures may interrupt subscription purchases.
Why: Failed transactions can create friction during onboarding and renewal.
Impact: Medium
Mitigation: Support reliable payment flows and provide clear retry/failure handling.

## Highest Business Risk

Risk: Customer retention and delivery reliability.

Reason:
The business depends on recurring subscriptions, so poor food consistency or unreliable delivery could increase churn and weaken unit economics.

Mitigation:
Validate retention through a small geographic pilot, monitor repeat orders and cancellations, and improve delivery operations before expanding.
""",

        "startup_score": {
            "score": 68,
            "reasoning": (
                "The startup addresses a recurring student food-delivery need "
                "with a focused target segment, but customer retention and "
                "operational execution remain important concerns."
            ),
            "breakdown": {
                "market": 72,
                "mvp": 70,
                "tech": 68,
                "risk": 58
            },
            "highest_risk_flag": "risk"
        },

        "recommendations": [],

        "generated_ideas": [],

        "nurtured_idea": "",

        "advancement_plan": "",

        "chat_response": "",

        "final_report": "",

        "pdf_path": "",

        # ── PIPELINE TRACKING ───────────────────────────────

        "pipeline_status": {},

        "agent_retry_count": {},

        "execution_log": [],

        "errors": []
    }

    # ----------------------------------------------------
    # 2. Initialize Recommendation Agent
    # ----------------------------------------------------

    agent = RecommendationAgent()

    # ----------------------------------------------------
    # 3. Run recommendation pipeline
    # ----------------------------------------------------

    workflow_state = agent.run(
        MOCK_STATE_RECOMMENDATION.copy()
    )

    # ----------------------------------------------------
    # 4. Print generated recommendations
    # ----------------------------------------------------

    print(
        workflow_state["recommendations"]
    )