"""
File        : agents/tech_advisor_agent.py
Triggered By: full_analysis, partial_idea
Tools       : groq_tool.py
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
from src.tools.groq_tool import groq_tool


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
Analyze the following startup information and market data.

Recommend the technology stack according to your system instructions.

### STARTUP INFORMATION

Startup Idea:
{startup_idea}

Startup Type:
{startup_type}

### MARKET DATA

{market_data}

Use STARTUP INFORMATION as the primary product context.

Use MARKET DATA as supporting market and technology evidence.

Determine the startup's actual product requirements, technical requirements, technology needs, and relevant ecosystem considerations.

Do not invent missing business, scale, traffic, compliance, or team-size information.

If team size is available in the supplied context, use it when evaluating every major technology choice.

For every major technology recommendation:

1. Identify the requirement it solves.
2. Explain why the technology fits this startup.
3. Explain why it is appropriate for the team's size and current stage.
4. Consider whether a simpler alternative would be sufficient.
5. Explain one important trade-off.

Prefer a modular monolith for an early-stage startup unless a concrete requirement justifies greater architectural complexity.

Do not recommend orchestration or workflow frameworks before 10,000 users.

This includes workflow and agent orchestration frameworks such as Temporal, Airflow, Celery, Prefect, Dagster, LangChain, CrewAI, AutoGen, and similar tools.

The 10,000-user threshold does not automatically justify orchestration.

Even after that threshold, recommend orchestration only when a concrete operational requirement justifies its complexity.

Do not recommend Kubernetes, microservices, distributed infrastructure, or other complex deployment architecture merely because the startup may eventually scale.

Use the source URLs provided in MARKET DATA when making externally supported claims.

Do not invent, modify, shorten, or guess URLs.

Clearly distinguish sourced facts from technical inferences and recommendations.

Recommend only technologies that solve actual or reasonably inferred requirements.

Do not fill unnecessary technology categories.

The final stack should be realistic for this startup to build and maintain TODAY.

Return the response using the exact output structure defined in the system instructions.

        """

        # ----------------------------------------------------
        # 4. Prepare LLM message sequence
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

        tech_stack_response = groq_tool.generate_text(
            messages=messages
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