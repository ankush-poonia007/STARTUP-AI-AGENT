"""
File        : agents/idea_generation_agent.py
Triggered By: idea_exploration
Tools       : tavily_tool.py + groq_tool.py

Purpose:
    Discover and rank startup opportunities using fresh market evidence
    together with the user-provided startup context.

Inputs:
    workflow_state["user_input"]   → original user request
    workflow_state["startup_idea"]  → normalized startup concept
    workflow_state["startup_type"]  → inferred startup category

Output:
    workflow_state["generated_ideas"] → list of ranked idea dictionaries

Each generated idea contains:
    rank          → demand-based ranking position
    idea          → one-line startup concept
    market_signal → evidence-based reason the opportunity is relevant
    source_url    → original Tavily evidence URL

Responsibilities:
    - Discover current market opportunities with Tavily.
    - Identify relevant customer problems and demand signals.
    - Generate 5–10 startup opportunities.
    - Rank opportunities using available market evidence.
    - Preserve source URLs exactly as returned by Tavily.
    - Return the required structured JSON output.

Pipeline:
    Startup Context → Tavily Research → Groq Idea Generation
                    → JSON Parsing → generated_ideas

Important:
    Tavily provides external evidence; Groq interprets that evidence.
    Market claims must remain grounded in the supplied search results.
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

class IdeaGenerationAgent:
    """
Discover and rank startup opportunities for the idea_exploration workflow.

The agent combines the normalized startup context with fresh Tavily
research, then asks Groq to generate a structured ranked opportunity list.

Input State:
    workflow_state["user_input"]:
        Original user request or area of interest.

    workflow_state["startup_idea"]:
        Normalized startup concept prepared upstream.

    workflow_state["startup_type"]:
        Startup category used to keep opportunity discovery relevant.

External Evidence:
    Tavily supplies current information about customer problems, market
    demand, emerging opportunities, technologies, and industry changes.

Output State:
    workflow_state["generated_ideas"]:
        Ranked startup opportunities with supporting market signals and URLs.

    workflow_state["pipeline_status"]["IdeaGenerationAgent"]:
        Set to "success" after successful execution.

Processing Flow:
    1. Read startup context.
    2. Build a focused market-search query.
    3. Retrieve fresh Tavily evidence.
    4. Build the idea-generation prompt.
    5. Generate structured opportunities with Groq.
    6. Parse the JSON response.
    7. Store the generated ideas in workflow_state.

The agent does not invent market evidence or modify supplied source URLs.
"""

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

    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state: dict) -> dict:
        """
Generate and rank startup opportunities using fresh market research.

Parameters
----------
workflow_state : dict
    Shared workflow state containing user input, normalized startup
    context, and pipeline status.

Returns
-------
dict
    Updated workflow state containing generated_ideas and the successful
    IdeaGenerationAgent pipeline status.

Processing Stages
-----------------
1. Read the original input and normalized startup context.
2. Build a focused Tavily research query.
3. Retrieve fresh market evidence.
4. Load the idea-generation system instructions.
5. Build the user prompt from startup context and search evidence.
6. Prepare the LLM message sequence.
7. Generate ranked startup opportunities through Groq.
8. Clean accidental Markdown formatting.
9. Parse the structured JSON response.
10. Store generated ideas in workflow_state.
11. Mark the agent as successful.
12. Return the updated workflow state.

Evidence Rules
--------------
Market signals should be supported by the supplied Tavily results.
Original source URLs must be preserved exactly.
"""


        # ----------------------------------------------------
        # 1. Read user input
        # ----------------------------------------------------

        user_input = workflow_state["user_input"]
        
        startup_idea = workflow_state["startup_idea"]
        startup_type = workflow_state["startup_type"]
        
        # ----------------------------------------------------
        # 2. Build market research search query
        # ----------------------------------------------------

        # TAVILY SEARCH PROMPT

        tavily_prompt = f"""
Find recent, credible, and directly relevant market evidence that can help identify
and evaluate startup opportunities related to the provided startup context.

USER INPUT:
{user_input}

STARTUP INFORMATION:

Startup Idea:
{startup_idea}

Startup Type:
{startup_type}

Search specifically for evidence related to the actual opportunity space described
above.

Prioritize evidence that can support a concrete market_signal, such as:

- Specific market-size figures
- Specific growth percentages or rates
- Revenue figures
- Customer or user adoption numbers
- Measured customer behavior
- Documented demand
- Specific customer pain points
- Documented unmet needs
- Product adoption trends
- Relevant industry events
- Regulatory or policy changes creating opportunities
- Relevant competitor or product developments
- Specific emerging market opportunities

The evidence must be directly relevant to the startup idea or a clearly related
customer problem.

Do NOT prioritize generic articles about:

- Broad technology growth
- Generic AI trends
- General startup trends
- Vague market optimism
- Technology popularity without business relevance

A growing industry or technology is useful only when the evidence can help support
a specific startup opportunity within that industry.

Prefer:

1. Recent sources
2. Credible sources
3. Primary or authoritative sources
4. Sources containing concrete statistics or measurable evidence
5. Sources directly related to the target customer, problem, or market

Search broadly enough to discover multiple meaningfully different opportunities,
but keep the evidence relevant to the startup context.

Return multiple relevant search results with their original URLs and useful content.

Preserve the original source URLs exactly.

Do not invent, modify, shorten, or combine URLs.
"""

        # ----------------------------------------------------
        # 3. Retrieve fresh market evidence
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

        # USER PROMPT FOR IDEA GENERATION

        user_prompt = f"""
STARTUP INFORMATION:

Startup Idea:
{startup_idea}

Startup Type:
{startup_type}

USER INPUT:
{user_input}

TAVILY SEARCH RESULTS:

{chr(10).join(
    f"- URL: {result['url']}\n"
    f"  Content: {result['content']}"
    for result in tavily_response
)}

Evaluate the opportunities in the supplied search results using the startup
information and the system instructions.

Return the required ranked JSON array only.
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
        # 7. Generate startup opportunities
        # ----------------------------------------------------
        groq_response = text_call(
            messages=messages,
            reasoning_effort="high",
            include_reasoning=False,
            response_format= self.IDEA_GENERATION_RESPONSE_FORMAT
        )

        
        # ----------------------------------------------------
        # 8. Parse LLM JSON response
        # ----------------------------------------------------

        data = json.loads(
            groq_response
        )

        # ----------------------------------------------------
        # 9. Store generated ideas in workflow state
        # ----------------------------------------------------
        
        workflow_state["generated_ideas"] = (
            data["ideas"]
        )
        
        # ----------------------------------------------------
        # 10. Update pipeline status
        # ----------------------------------------------------

        workflow_state["pipeline_status"]["IdeaGenerationAgent"] = (
            "success"
        )

        # ----------------------------------------------------
        # 11. Return updated workflow state
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
    import copy
    
    workflow_state = copy.deepcopy(MOCK_STATE_FULL)
    
    # ----------------------------------------------------
    # 2. Initialize Idea Generation Agent
    # ----------------------------------------------------

    agent = IdeaGenerationAgent()

    # ----------------------------------------------------
    # 3. Run idea generation pipeline
    # ----------------------------------------------------

    workflow_state = agent.run(
        copy.deepcopy(workflow_state)
    )

    # ----------------------------------------------------
    # 4. Print generated startup ideas
    # ----------------------------------------------------

    print(
        workflow_state["generated_ideas"]
    )