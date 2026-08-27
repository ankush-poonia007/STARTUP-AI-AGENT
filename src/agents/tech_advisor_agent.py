"""
File        : agents/tech_advisor_agent.py
Triggered By: full_analysis, partial_idea
# Claude: prev -> Tools       : groq_tool.py
# Phase 5 migrated this agent to Gemini but left the docstring on Groq.
Tools       : gemini_tool.py
Input       : workflow_state["startup_idea"]
             + workflow_state["startup_type"]
             + workflow_state["market_data"]
Output      : workflow_state["tech_recommendations"]

Purpose:
    Recommend a practical technology stack using the normalized startup
    context and supporting market evidence.

Output Format:
    workflow_state["tech_recommendations"] → str
        Structured plain text:
            ## Frontend
            ## Backend
            ## Database
            ## Server
            ## Infrastructure
            ## Rationale

Responsibilities:
    - Align technology choices with startup idea and startup type.
    - Use market data as supporting evidence.
    - Prioritize speed to market and maintainability.
    - Prefer lean architecture for an early-stage startup.
    - Explain requirements, fit, and trade-offs for major choices.
    - Avoid unnecessary architectural complexity.
    - Preserve supplied source URLs for supported claims.

Important:
    Do not invent missing business, scale, compliance, or team-size
    information. Recommend only technologies that solve actual or
    reasonably inferred requirements.
"""

from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure
)

from src.prompts.prompts import TECH_ADVISOR_PROMPT
from src.tools.gemini_tool import gemini_tool


class TechAdvisorAgent:
    """
Technology stack recommendation agent for early-stage startup analysis.

The agent combines normalized startup context with market evidence to
produce a realistic, maintainable technology stack.

Input State:
    workflow_state["startup_idea"]:
        Normalized startup concept prepared upstream.

    workflow_state["startup_type"]:
        Startup category inferred from the normalized startup idea.

    workflow_state["market_data"]:
        Market and technology evidence produced by upstream agents.

Output State:
    workflow_state["tech_recommendations"]:
        Structured technology stack recommendation.

    workflow_state["pipeline_status"]["TechAdvisorAgent"]:
        Set to "success" after successful execution.

Responsibilities:
    - Translate startup requirements into technology requirements.
    - Recommend relevant frontend, backend, database, server, and
      infrastructure choices.
    - Justify major choices against startup context and evidence.
    - Prefer simple architecture over premature complexity.
    - Consider team size only when supplied in the workflow state.
    - Distinguish sourced facts from technical recommendations.

The agent recommends technology; it does not perform market research
or invent missing startup information.
"""

    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state: dict) -> dict:
        """
Generate technology stack recommendations from startup context and
market evidence.

Parameters
----------
workflow_state : dict
    Shared workflow state containing "startup_idea", "startup_type",
    "market_data", and "pipeline_status".

Returns
-------
dict
    Updated workflow state containing "tech_recommendations" and the
    successful TechAdvisorAgent pipeline status.

Processing Stages
-----------------
1. Read startup idea, startup type, and market data.
2. Load the technology-advisor system instructions.
3. Build the evidence-grounded user prompt.
4. Prepare the system/user message sequence.
5. Generate the recommendation through Groq.
6. Store the recommendation in workflow_state.
7. Mark TechAdvisorAgent as successful.
8. Return the updated workflow state.

Recommendation Rules
--------------------
Startup information is the primary product context. Market data is
supporting evidence. Recommendations should be realistic for the
startup's current stage, avoid premature infrastructure complexity,
and clearly distinguish evidence from technical inference.
"""

        # ----------------------------------------------------
        # 1. Read startup context and market evidence
        # ----------------------------------------------------
        startup_idea = workflow_state["startup_idea"]
        startup_type = workflow_state["startup_type"]
        
        market_data = workflow_state["market_data"]

        # ----------------------------------------------------
        # 2. Load technology-advisor instructions
        # ----------------------------------------------------

        system_prompt = TECH_ADVISOR_PROMPT

        # ----------------------------------------------------
        # 3. Build evidence-grounded user prompt
        # ----------------------------------------------------
        
        user_prompt = f"""
Analyze the startup context below and recommend the technology stack according to the system instructions.

### STARTUP INFORMATION

**Startup Idea:** {startup_idea}
**Startup Type:** {startup_type}

### MARKET DATA

{market_data}

Return the response using the exact output structure defined in the system prompt.
"""

        # ----------------------------------------------------
        # 4. Prepare LLM message sequence
        # ----------------------------------------------------

        messages = (
            system_prompt +
            "\n\n" +
            user_prompt
        )

        # ----------------------------------------------------
        # 5. Generate technology recommendations
        # ----------------------------------------------------

        tech_stack_response = gemini_tool.generate_text(
            user_prompt=messages
        )

        # ----------------------------------------------------
        # 6. Store recommendations in workflow state
        # ----------------------------------------------------

        workflow_state["tech_recommendations"] = (
            tech_stack_response
        )

        # ----------------------------------------------------
        # 7. Mark agent execution as successful
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
    # 1. Load full-workflow test state
    # ----------------------------------------------------

    from tests.mock_workflow_state import MOCK_STATE_FULL

    # ----------------------------------------------------
    # 2. Initialize Tech Advisor Agent
    # ----------------------------------------------------

    agent = TechAdvisorAgent()

    # ----------------------------------------------------
    # 3. Run technology recommendation stage
    # ----------------------------------------------------

    workflow_state = agent.run(
        MOCK_STATE_FULL.copy()
    )

    # ----------------------------------------------------
    # 4. Display generated recommendations
    # ----------------------------------------------------

    print(
        workflow_state["tech_recommendations"]
    )
    
    # ============================================================
    # 5. Display execution errors
    # ============================================================

    print(
        workflow_state["errors"]
    )