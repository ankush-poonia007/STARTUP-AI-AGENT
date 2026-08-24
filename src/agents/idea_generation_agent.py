"""
File        : agents/idea_generation_agent.py
Triggered By:
    - idea_exploration

Tools:
    - tavily_tool.py
    - groq_tool.py

Purpose:
    Discover and rank startup opportunities using fresh market evidence
    together with the user's startup context.

Input:
    workflow_state["user_input"]
        Original user request.

    workflow_state["startup_idea"]
        Normalized startup concept.

    workflow_state["startup_type"]
        Inferred startup category.

Output:
    workflow_state["generated_ideas"] → list of dicts

    Each generated idea contains:
        rank:
            Demand-based ranking position.

        idea:
            One-line startup concept.

        market_signal:
            Evidence-based reason the opportunity is relevant.

        source_url:
            Original Tavily evidence URL.

Responsibilities:
    - Discover current market opportunities using Tavily.
    - Identify relevant customer problems and demand signals.
    - Generate 5–10 startup opportunities.
    - Rank opportunities using available market evidence.
    - Preserve source URLs exactly as returned by Tavily.
    - Return the required structured JSON output.

Pipeline:
    Startup Context
        ↓
    Tavily Research
        ↓
    Groq Idea Generation
        ↓
    JSON Parsing
        ↓
    workflow_state["generated_ideas"]

Evidence Principle:
    Tavily provides external evidence.
    Groq interprets the supplied evidence.

    Market claims must remain grounded in the provided search results.
    The agent must not invent market evidence or source URLs.
"""

from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure
)

from src.prompts.prompts import IDEA_GENERATION_PROMPT
from src.tools.tavily_tool import tavily_tool
from src.tools.groq_tool import groq_tool

import json


class IdeaGenerationAgent:
    """
    Discover and rank startup opportunities for the idea_exploration
    workflow using fresh external market evidence.

    Input State
    -----------
    workflow_state["user_input"]:
        Original user request or area of interest.

    workflow_state["startup_idea"]:
        Normalized startup concept prepared upstream.

    workflow_state["startup_type"]:
        Startup category used to keep opportunity discovery relevant.

    External Evidence
    -----------------
    Tavily supplies current information about customer problems,
    market demand, emerging opportunities, technologies, and
    industry changes.

    Output State
    ------------
    workflow_state["generated_ideas"]:
        Ranked startup opportunities with supporting market signals
        and source URLs.

    workflow_state["pipeline_status"]["IdeaGenerationAgent"]:
        Set to "success" after successful execution.

    Processing Flow
    ---------------
    1. Read startup context.
    2. Build a focused market-search query.
    3. Retrieve fresh Tavily evidence.
    4. Build the idea-generation prompt.
    5. Generate structured opportunities with Groq.
    6. Parse the JSON response.
    7. Store generated ideas in workflow state.
    8. Update pipeline status.
    9. Return the updated workflow state.

    Evidence Principle
    ------------------
    Market signals must be supported by the supplied Tavily results.

    Original source URLs must be preserved exactly.

    The agent interprets supplied evidence but does not independently
    create or verify market claims.
    """

    # ============================================================
    # RESPONSE FORMAT
    # Defines the strict JSON structure expected from the LLM.
    # The root object contains the generated idea list.
    # ============================================================

    IDEA_GENERATION_RESPONSE_FORMAT = {
        "type": "json_schema",
        "json_schema": {
            "name": "startup_idea_generation",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "ideas": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rank": {
                                    "type": "integer"
                                },
                                "idea": {
                                    "type": "string"
                                },
                                "market_signal": {
                                    "type": "string"
                                },
                                "source_url": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "rank",
                                "idea",
                                "market_signal",
                                "source_url"
                            ],
                            "additionalProperties": False
                        }
                    }
                },
                "required": [
                    "ideas"
                ],
                "additionalProperties": False
            }
        }
    }

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
        Generate and rank startup opportunities using fresh market
        research.

        Parameters
        ----------
        workflow_state : dict
            Shared workflow state containing user input, normalized
            startup context, and pipeline status.

        Returns
        -------
        dict
            Updated workflow state containing generated_ideas and
            the successful IdeaGenerationAgent pipeline status.

        Processing Stages
        -----------------
        1. Read the original input and normalized startup context.
        2. Build a focused Tavily research query.
        3. Retrieve fresh market evidence.
        4. Load the idea-generation system instructions.
        5. Build the user prompt from startup context and evidence.
        6. Prepare the LLM message sequence.
        7. Generate ranked startup opportunities through Groq.
        8. Parse the structured JSON response.
        9. Store generated ideas in workflow state.
        10. Update pipeline status.
        11. Return the updated workflow state.

        Evidence Rules
        --------------
        Market signals should be supported by the supplied Tavily
        results.

        Original source URLs must be preserved exactly.
        """

        # ============================================================
        # 1. Read startup context
        # ============================================================

        user_input = workflow_state["user_input"]

        startup_idea = workflow_state["startup_idea"]

        startup_type = workflow_state["startup_type"]

        # ============================================================
        # 2. Build focused market research query
        # ============================================================

        tavily_prompt = f"""
[ROLE]
You are a market-evidence search agent for a startup analysis system.

[OBJECTIVE]
Find recent, credible, directly relevant evidence that reveals or validates market opportunities related to the supplied startup context.

[INPUT]
- USER INPUT: {user_input}
- STARTUP IDEA: {startup_idea}
- STARTUP TYPE: {startup_type}

Use STARTUP IDEA as the primary opportunity definition and STARTUP TYPE as industry/category context. Search the actual opportunity/customer problem, not the generic industry.

[EVIDENCE TARGETS]
Prioritize concrete, measurable signals:
- Market size, growth, or revenue
- Customer/user adoption
- Measured customer behavior or demand
- Specific pain points or unmet needs
- Product/adoption trends
- Competitor/product developments
- Relevant industry events
- Regulatory/policy changes creating opportunities
- Emerging market opportunities

A signal is useful only when it supports a specific opportunity relevant to the startup or a clearly related customer problem.

[SEARCH QUALITY]
Prefer, in order:
1. Recent sources
2. Credible/authoritative sources
3. Primary sources
4. Sources containing measurable evidence
5. Sources directly relevant to the target customer/problem/market

Search broadly enough to identify meaningfully different opportunities, but reject irrelevant evidence.

[EXCLUDE]
Do not prioritize:
- Generic AI/technology growth
- Broad startup trends
- Vague market optimism
- Technology popularity without business relevance

Industry or technology growth is relevant only when it supports a specific startup opportunity.

[OUTPUT]
Return multiple relevant search results containing useful evidence and their original URLs.

Preserve source URLs exactly. Never invent, modify, shorten, combine, or guess URLs.
"""

        # ============================================================
        # 3. Retrieve fresh market evidence
        # ============================================================

        tavily_response = tavily_tool.search(
            user_query=tavily_prompt
        )

        # ============================================================
        # 4. Prepare idea-generation system prompt
        # ============================================================

        system_prompt = IDEA_GENERATION_PROMPT

        # ============================================================
        # 5. Build idea-generation user prompt
        # ============================================================

        user_prompt = f"""
STARTUP IDEA: {startup_idea}

STARTUP TYPE: {startup_type}

USER INPUT: {user_input}

TAVILY SEARCH RESULTS:
{chr(10).join(
    f"- URL: {result['url']}\n"
    f"  Content: {result['content']}"
    for result in tavily_response
)}

Evaluate opportunities in the supplied search results using the startup context and system instructions. Return the ranked JSON object only.
"""

        # ============================================================
        # 6. Prepare LLM messages
        # ============================================================

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

        # ============================================================
        # 7. Generate ranked startup opportunities
        # ============================================================

        groq_response = groq_tool.generate_text(
            messages=messages,
            reasoning_effort="high",
            include_reasoning=False,
            response_format=self.IDEA_GENERATION_RESPONSE_FORMAT
        )

        # ============================================================
        # 8. Parse structured JSON response
        # ============================================================

        data = json.loads(
            groq_response
        )
        # ============================================================
        # 9. Store generated ideas in workflow state
        # ============================================================

        workflow_state["generated_ideas"] = (
            data["ideas"]
        )

        # ============================================================
        # 10. Update IdeaGenerationAgent pipeline status
        # ============================================================

        workflow_state["pipeline_status"]["IdeaGenerationAgent"] = (
            "success"
        )

        # ============================================================
        # 11. Return updated workflow state
        # ============================================================

        return workflow_state


# ================================================================
# STANDALONE TEST
# Allows IdeaGenerationAgent to be tested independently using the
# shared mock workflow state.
# ================================================================

if __name__ == "__main__":

    # ============================================================
    # 1. Load mock workflow state
    # ============================================================

    from tests.mock_workflow_state import MOCK_STATE_FULL
    import copy

    workflow_state = MOCK_STATE_FULL.copy()

    # ============================================================
    # 2. Initialize IdeaGenerationAgent
    # ============================================================

    agent = IdeaGenerationAgent()

    # ============================================================
    # 3. Execute idea-generation workflow
    # ============================================================
    
    workflow_state = agent.run(
        workflow_state
    )

    # result = agent.run(
    #     copy.deepcopy(workflow_state)
    # )

    # print("RESULT:", result)

    # if result is not None:
    #     print(result["generated_ideas"])
    #     print(result["errors"])
    # else:
    #     print("Agent returned None")
    # ============================================================
    # 4. Display generated startup ideas
    # ============================================================

    print(
        workflow_state["generated_ideas"]
    )

    # ============================================================
    # 5. Display execution errors
    # ============================================================

    print(
        workflow_state["errors"]
    )