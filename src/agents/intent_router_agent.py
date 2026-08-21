"""
File        : agents/intent_router_agent.py
Triggered By: Every request — called first by OrchestratorAgent
Tools       : groq_tool.py
Input       : workflow_state["user_input"] + workflow_state["pitch_deck_text"]
Output      : workflow_state["startup_idea"]
             + workflow_state["startup_type"]
             + workflow_state["intent"]
             + workflow_state["execution_plan"]

Purpose:
    Intent_Router_Agent is the workflow decision layer. It first converts
    the user's raw input into a normalized startup idea and startup type,
    then classifies the user's intent and builds the corresponding
    execution plan.

Processing Sequence:
    1. Receive the user's original input.
    2. Extract a normalized startup idea using STARTUP_IDEA_PROMPT.
    3. Classify the startup type using STARTUP_TYPE_PROMPT.
    4. Classify the user's workflow intent using INTENT_ROUTER_PROMPT.
    5. Normalize and validate the returned intent.
    6. Check whether pitch-deck context is available.
    7. Build the execution plan for the selected intent.
    8. Store the derived values in workflow_state.

Output State:
    workflow_state["startup_idea"] → str
        Clean startup concept derived from the user's original input.

    workflow_state["startup_type"] → str
        Startup category/type inferred from the normalized startup idea.

    workflow_state["intent"] → str
        One of:
            "full_analysis"
            "partial_idea"
            "idea_exploration"
            "nurturing"
            "advancement"
            "general_chat"
            "pdf_request"

    workflow_state["execution_plan"] → dict
        Contains execution_order and execution_plan for the selected
        workflow.

RAG Behaviour:
    RAGAgent is included only when workflow_state["pitch_deck_text"]
    contains content.

LLM Judge Behaviour:
    LLMJudgeAgent is not included as a normal execution-plan agent.
    OrchestratorAgent owns the mid-pipeline and final judge checkpoints.

Failure Handling:
    Invalid intent classification falls back to "general_chat".
    Decorators handle execution-level failures and retry behaviour.

Ownership:
    This agent decides what workflow should run and prepares the
    information required by downstream agents. It does not execute
    downstream agents itself.
"""

from src.prompts.prompts import (
    INTENT_ROUTER_PROMPT,
    STARTUP_IDEA_PROMPT,
    STARTUP_TYPE_PROMPT
)

from tests.mock_workflow_state import MOCK_STATE_EMPTY
from src.tools.groq_tool import text_call

from src.core.decorators import (
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure,
)


class Intent_Router_Agent:
    """
Intent Router responsible for preparing startup context, classifying
the user's requested workflow, and constructing the execution plan.

Responsibilities:
    - Convert raw user input into a normalized startup idea.
    - Identify the startup type from the normalized idea.
    - Classify the requested workflow intent.
    - Normalize and validate the LLM's intent response.
    - Apply the general_chat fallback for unsupported intents.
    - Detect whether pitch-deck context is available.
    - Conditionally include RAGAgent in applicable workflows.
    - Build the execution order and batch execution plan.
    - Store all routing outputs in workflow_state.

The class is a decision layer only. It does not execute the downstream
agents listed in the execution plan.

Judge Ownership:
    LLMJudgeAgent is deliberately excluded from execution plans.
    OrchestratorAgent is responsible for triggering run_mid() and
    run_final() at the appropriate workflow checkpoints.

Startup Context:
    startup_idea and startup_type are prepared before intent routing so
    downstream agents can work with a normalized representation of the
    startup instead of relying only on the original user wording.
"""
    
    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(
            self,
            workflow_state: dict
        ) -> dict:
        """
Prepare startup context, classify the user's workflow intent, and attach
the selected execution plan to workflow_state.

Parameters
----------
workflow_state : dict
    Shared workflow state containing the user's original input and
    pitch-deck text.

Returns
-------
dict
    Updated workflow state containing:
        - startup_idea
        - startup_type
        - intent
        - execution_plan
        - successful IntentRouterAgent pipeline status

Processing Stages
-----------------
1. Build the startup-idea extraction prompt.
2. Generate and store workflow_state["startup_idea"].
3. Build the startup-type classification prompt.
4. Generate and store workflow_state["startup_type"].
5. Build the intent-classification prompt.
6. Classify and normalize the workflow intent.
7. Apply the general_chat fallback when necessary.
8. Check pitch-deck availability for conditional RAG execution.
9. Mark the router as successful.
10. Build the workflow-specific execution plans.
11. Store the selected plan in workflow_state.
12. Return the updated workflow state.

Important:
    startup_idea and startup_type are derived context values used to
    improve downstream workflow consistency. They do not replace the
    original user_input.

RAG:
    RAGAgent is conditionally included when pitch_deck_text is non-empty.

LLM Judge:
    LLMJudgeAgent is intentionally absent from normal execution batches.
    OrchestratorAgent owns the judge checkpoints.
"""

        # ----------------------------------------------------
        # 1. Build intent-classification prompt
        # ----------------------------------------------------
        # Prepare the system instructions and user's request
        # that will be sent to the intent-classification model.

        intent_prompt = [
            {
                "role": "system",
                "content": INTENT_ROUTER_PROMPT
            },
            {
                "role": "user",
                "content": workflow_state["user_input"]
            }
        ]
        
        # ----------------------------------------------------
        # 2. Build normalized startup idea
        # ----------------------------------------------------
        # Convert the user's original wording into a cleaner startup
        # concept that can be reused consistently by downstream agents.

        startup_idea_prompt = [
            {
                "role":"system",
                "content":STARTUP_IDEA_PROMPT
            },
            {
                "role":"user",
                "content": f"User Input : {workflow_state['user_input']}"
            }
        ]

        startup_idea = text_call(
            messages=startup_idea_prompt
        )

        workflow_state["startup_idea"] = (
                    startup_idea
            )

        # ----------------------------------------------------
        # 3. Classify startup type
        # ----------------------------------------------------
        # Use the normalized startup idea to identify its broad
        # startup/domain category for downstream analysis.

        startup_type_prompt = [
            {
                "role":"system",
                "content":STARTUP_TYPE_PROMPT
            },
            {
                "role":"user",
                "content":f"Startup Idea: {startup_idea}"
            }
        ]

        startup_type = text_call(
            messages=startup_type_prompt
        )

        workflow_state["startup_type"] = (
            startup_type
        )

        # ----------------------------------------------------
        # 4. Classify user intent
        # ----------------------------------------------------
        # Send the prepared prompt to the LLM and receive the
        # raw workflow-intent classification.

        intent_response = text_call(
            messages=intent_prompt
        )

        # ----------------------------------------------------
        # 5. Validate supported intents
        # ----------------------------------------------------
        # Define the complete set of workflow names that the
        # router is allowed to produce.

        valid_intents = {
            "full_analysis",
            "partial_idea",
            "idea_exploration",
            "nurturing",
            "advancement",
            "general_chat",
            "pdf_request"
        }

        # ----------------------------------------------------
        # 6. Normalize LLM output
        # ----------------------------------------------------
        # Convert the model response into a predictable format
        # so minor formatting differences do not break routing.

        normalized_intent = (
            str(intent_response)
            .strip()
            .lower()
            .replace(" ", "_")
        )

        normalized_intent = (
            normalized_intent.replace("-", "_")
        )

        # ----------------------------------------------------
        # 6A. Apply safe fallback for unsupported intent
        # ----------------------------------------------------
        # If the model returns an unsupported value, route the
        # request to the general-chat workflow.

        if normalized_intent not in valid_intents:
            normalized_intent = "general_chat"

        workflow_state["intent"] = normalized_intent

        # ----------------------------------------------------
        # 7. Check whether pitch-deck context is available
        # ----------------------------------------------------
        # Determine whether the user supplied pitch-deck content.
        # This flag controls conditional RAGAgent inclusion.

        rag_response = bool(
            workflow_state["pitch_deck_text"]
        )

        # ----------------------------------------------------
        # 8. Mark IntentRouterAgent as successful
        # ----------------------------------------------------
        # The routing stage is complete once the intent has been
        # classified and the workflow can be constructed.

        workflow_state["pipeline_status"][
            "IntentRouterAgent"
        ] = "success"

        # ----------------------------------------------------
        # 9. Build intent-specific execution plans
        # ----------------------------------------------------
        # Construct the execution configuration for every supported
        # intent. The selected plan is stored in workflow_state below.
        # Startup idea/type preparation has already completed before
        # this stage and is now available to downstream agents.

        execution_pipeline = {

            # =================================================
            # FULL ANALYSIS
            # =================================================
            # Complete startup analysis including market research,
            # MVP planning, technology evaluation, risk analysis,
            # startup scoring, recommendation, and report writing.

            "full_analysis": {

                "execution_order": [
                    "IntentRouterAgent",
                    "MarketResearchAgent",
                    "WebSearchAgent"
                ]
                + (
                    ["RAGAgent"]
                    if rag_response
                    else []
                )
                + [
                    "MVPAdvisorAgent",
                    "TechAdvisorAgent",
                    "RiskAnalystAgent",
                    "StartupScorerAgent",
                    "RecommendationAgent",
                    "ReportWriterAgent",
                    "PDFGeneratorAgent (on request)"
                ],

                "execution_plan": [

                    {
                        "batch": 1,
                        "agents": [
                            "MarketResearchAgent",
                            "WebSearchAgent"
                        ]
                        + (
                            ["RAGAgent"]
                            if rag_response
                            else []
                        ),
                        "parallel": True,
                        "note": (
                            "RAGAgent conditional if "
                            "pitch_deck_text non-empty"
                            if rag_response
                            else None
                        )
                    },

                    {
                        "batch": 2,
                        "agents": [
                            "MVPAdvisorAgent",
                            "TechAdvisorAgent"
                        ],
                        "parallel": True
                    },

                    {
                        "batch": 3,
                        "agents": [
                            "RiskAnalystAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 4,
                        "agents": [
                            "StartupScorerAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 5,
                        "agents": [
                            "RecommendationAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 6,
                        "agents": [
                            "ReportWriterAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 7,
                        "agents": [
                            "PDFGeneratorAgent"
                        ],
                        "parallel": False,
                        "note": (
                            "Generate only if user "
                            "explicitly requests PDF"
                        )
                    }
                ]
            },

            # =================================================
            # PARTIAL IDEA
            # =================================================
            # Used when the user provides an incomplete startup
            # concept that needs refinement and development.

            "partial_idea": {

                "execution_order": [
                    "IntentRouterAgent",
                    "MarketResearchAgent",
                    "WebSearchAgent"
                ]
                + (
                    ["RAGAgent"]
                    if rag_response
                    else []
                )
                + [
                    "MVPAdvisorAgent",
                    "TechAdvisorAgent",
                    "RecommendationAgent",
                    "NurturingAgent",
                    "ReportWriterAgent",
                    "PDFGeneratorAgent (on request)"
                ],

                "execution_plan": [

                    {
                        "batch": 1,
                        "agents": [
                            "MarketResearchAgent",
                            "WebSearchAgent"
                        ]
                        + (
                            ["RAGAgent"]
                            if rag_response
                            else []
                        ),
                        "parallel": True,
                        "note": (
                            "RAGAgent conditional if "
                            "pitch_deck_text non-empty"
                            if rag_response
                            else None
                        )
                    },

                    {
                        "batch": 2,
                        "agents": [
                            "MVPAdvisorAgent",
                            "TechAdvisorAgent"
                        ],
                        "parallel": True
                    },

                    {
                        "batch": 3,
                        "agents": [
                            "RecommendationAgent",
                            "NurturingAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 4,
                        "agents": [
                            "ReportWriterAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 5,
                        "agents": [
                            "PDFGeneratorAgent"
                        ],
                        "parallel": False,
                        "note": (
                            "On-demand only; requires "
                            "final_report"
                        )
                    }
                ]
            },

            # =================================================
            # IDEA EXPLORATION
            # =================================================
            # Lightweight workflow for generating and exploring
            # startup ideas without running the full analysis stack.

            "idea_exploration": {

                "execution_order": [
                    "IntentRouterAgent",
                    "IdeaGenerationAgent"
                ],

                "execution_plan": [
                    {
                        "batch": 1,
                        "agents": [
                            "IdeaGenerationAgent"
                        ],
                        "parallel": False
                    }
                ]
            },

            # =================================================
            # NURTURING
            # =================================================
            # Used when an existing startup concept needs further
            # refinement and development.

            "nurturing": {

                "execution_order": [
                    "IntentRouterAgent"
                ]
                + (
                    ["RAGAgent"]
                    if rag_response
                    else []
                )
                + [
                    "RecommendationAgent",
                    "NurturingAgent",
                    "ReportWriterAgent",
                    "PDFGeneratorAgent (on request)"
                ],

                "execution_plan": [

                    {
                        "batch": 1,
                        "agents": [
                            "RecommendationAgent",
                            "NurturingAgent"
                        ]
                        + (
                            ["RAGAgent"]
                            if rag_response
                            else []
                        ),
                        "parallel": True,
                        "note": (
                            "RAGAgent conditional if "
                            "pitch_deck_text non-empty"
                            if rag_response
                            else None
                        )
                    },

                    {
                        "batch": 2,
                        "agents": [
                            "ReportWriterAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 3,
                        "agents": [
                            "PDFGeneratorAgent"
                        ],
                        "parallel": False,
                        "note": "On-demand only"
                    }
                ]
            },

            # =================================================
            # ADVANCEMENT
            # =================================================
            # Used when the user wants to continue or advance
            # an existing startup workflow.

            "advancement": {

                "execution_order": [
                    "IntentRouterAgent",
                    "AdvancementAgent",
                    "ReportWriterAgent",
                    "PDFGeneratorAgent (on request)"
                ],

                "execution_plan": [

                    {
                        "batch": 1,
                        "agents": [
                            "AdvancementAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 2,
                        "agents": [
                            "ReportWriterAgent"
                        ],
                        "parallel": False
                    },

                    {
                        "batch": 3,
                        "agents": [
                            "PDFGeneratorAgent"
                        ],
                        "parallel": False,
                        "note": "On-demand only"
                    }
                ]
            },

            # =================================================
            # GENERAL CHAT
            # =================================================
            # Lightweight fallback workflow for requests that do
            # not require specialized startup-analysis processing.

            "general_chat": {

                "execution_order": [
                    "IntentRouterAgent",
                    "GeneralChatAgent"
                ],

                "execution_plan": [
                    {
                        "batch": 1,
                        "agents": [
                            "GeneralChatAgent"
                        ],
                        "parallel": False
                    }
                ]
            },

            # =================================================
            # PDF REQUEST
            # =================================================
            # Dedicated workflow for explicitly requested PDF
            # generation when a final report is already available.

            "pdf_request": {

                "execution_order": [
                    "IntentRouterAgent",
                    "PDFGeneratorAgent (requires final_report)"
                ],

                "execution_plan": [
                    {
                        "batch": 1,
                        "agents": [
                            "PDFGeneratorAgent"
                        ],
                        "parallel": False,
                        "note": (
                            "PDF generation is on-demand and "
                            "requires workflow_state['final_report'] "
                            "to exist."
                        )
                    }
                ]
            }
        }

        # ----------------------------------------------------
        # 10. Store selected execution plan
        # ----------------------------------------------------
        # Select the workflow configuration corresponding to the
        # normalized user intent.

        workflow_state["execution_plan"] = (
            execution_pipeline[normalized_intent]
        )

        # ----------------------------------------------------
        # 11. Return updated workflow state
        # ----------------------------------------------------
        # Routing is complete. OrchestratorAgent will now consume
        # the selected execution plan and execute the workflow.

        return workflow_state


# ----------------------------------------------------
# LOCAL TEST
# ----------------------------------------------------
# Run this module directly to verify intent classification
# and execution-plan construction using mock workflow state.

if __name__ == "__main__":

    # ------------------------------------------------
    # 1. Load mock workflow state
    # ------------------------------------------------
    # Use the predefined empty state for a lightweight local test.

    workflow_state = MOCK_STATE_EMPTY

    # ------------------------------------------------
    # 2. Provide test user input
    # ------------------------------------------------
    # This sample input should be classified as a startup-analysis
    # request and routed to the appropriate execution workflow.

    workflow_state["user_input"] = (
        "AI-powered tiffin delivery for college students"
    )

    # ------------------------------------------------
    # 3. Initialize Intent Router Agent
    # ------------------------------------------------
    # Create the router that will classify the test request.

    agent = Intent_Router_Agent()

    # ------------------------------------------------
    # 4. Run intent classification
    # ------------------------------------------------
    # The router updates the workflow state with the detected
    # intent and its corresponding execution plan.

    workflow_state = agent.run(
        workflow_state
    )

    # ------------------------------------------------
    # 5. Display derived startup context
    # ------------------------------------------------
    # Verify the normalized startup idea and inferred startup type
    # produced before intent classification.

    print(
        workflow_state["intent"]
    )

    print(
        workflow_state["startup_idea"]
    )
    
    print(
        workflow_state["startup_type"]
    )
    # ------------------------------------------------
    # 6. Display detected intent and execution plan
    # ------------------------------------------------
    # Verify the selected workflow and the batches/agents that
    # Intent_Router_Agent assigned to it.

    print(
        workflow_state["execution_plan"]
    )

    # ============================================================
    # 5. Display execution errors
    # ============================================================

    print(
        workflow_state["errors"]
    )