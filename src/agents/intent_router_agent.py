"""
File        : agents/intent_router_agent.py
Triggered By: Every request — called first by OrchestratorAgent
Tools       : groq_tool.py
Input       : workflow_state["user_input"] + workflow_state["pitch_deck_text"]
Output      : workflow_state["intent"] + workflow_state["execution_plan"]

Purpose:
    Intent_Router_Agent is responsible for identifying what the user
    is asking for and converting that intent into a concrete execution
    plan for the multi-agent workflow.

    It does not execute downstream agents.

    Its job ends after:
        1. Classifying the user's request.
        2. Normalizing the classification result.
        3. Determining whether pitch-deck context is available.
        4. Selecting the corresponding workflow.
        5. Storing that workflow in workflow_state.

Supported Intents:
    - full_analysis
    - partial_idea
    - idea_exploration
    - nurturing
    - advancement
    - general_chat
    - pdf_request

Execution Plan:
    The selected execution plan contains:
        - execution_order:
            Ordered representation of the agents involved in the workflow.

        - execution_plan:
            Batch-level instructions describing:
                - batch number
                - agents in that batch
                - whether they can execute in parallel
                - optional execution notes

RAG Behaviour:
    RAGAgent is included only when pitch_deck_text contains data.

    This allows workflows to operate normally when no pitch deck is
    supplied while enabling document-grounded analysis when a pitch deck
    is available.

LLM Judge Behaviour:
    LLMJudgeAgent is not included as a normal execution-plan agent.

    The orchestrator owns judge execution and triggers:
        - run_mid() after the MVPAdvisorAgent stage for full_analysis.
        - run_final() after ReportWriterAgent for supported workflows.

Failure Handling:
    Invalid LLM classification → fall back to "general_chat".

    Decorators handle execution-level failures and retry behaviour.

    The resulting workflow state is returned to OrchestratorAgent,
    which is responsible for executing the selected plan.
"""

from src.prompts.prompts import INTENT_ROUTER_PROMPT
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
    Classifies the user's request and constructs the execution plan
    required by the multi-agent startup-analysis workflow.

    Intent_Router_Agent acts as the decision layer between the user's
    request and the workflow execution layer.

    Responsibilities:
        - Read the user's input from workflow_state.
        - Classify the request using INTENT_ROUTER_PROMPT.
        - Normalize the LLM classification.
        - Validate the classification against supported intents.
        - Fall back to general_chat when the classification is invalid.
        - Detect whether pitch-deck context is available.
        - Conditionally include RAGAgent when pitch-deck text exists.
        - Construct the execution plan for the selected workflow.
        - Store the selected intent and plan in workflow_state.
        - Mark IntentRouterAgent as successful.

    Supported Intents:
        full_analysis:
            Run the complete startup-analysis workflow.

        partial_idea:
            Expand and evaluate an incomplete startup idea.

        idea_exploration:
            Generate and explore startup ideas.

        nurturing:
            Improve and develop an existing startup concept.

        advancement:
            Continue or advance an existing startup workflow.

        general_chat:
            Handle requests that do not require a specialized
            startup-analysis workflow.

        pdf_request:
            Handle requests specifically related to PDF generation.

    Important:
        This class only decides what should execute.
        It does not execute the selected agents itself.

        OrchestratorAgent consumes the execution plan and performs
        the actual workflow execution.

        LLMJudgeAgent checkpoints are intentionally handled by
        OrchestratorAgent rather than being represented as normal
        execution-plan agents.
    """

    @log_execution
    @track_timing
    @retry_on_failure
    @handle_errors
    def run(
            self,
            workflow_state: dict
        ) -> dict:
        """
        Detect the user's intent and attach the corresponding
        execution plan to workflow_state.

        Parameters
        ----------
        workflow_state : dict
            Shared workflow state containing the user's original
            input and pitch-deck text.

        Returns
        -------
        dict
            Updated workflow state containing:
                - workflow_state["intent"]
                - workflow_state["execution_plan"]
                - successful IntentRouterAgent pipeline status

        Processing Stages
        -----------------
        1. Build the intent-classification prompt.
        2. Send the user's input to the configured LLM.
        3. Validate the returned intent against supported values.
        4. Normalize the LLM response.
        5. Fall back to general_chat when necessary.
        6. Check whether pitch-deck text is available.
        7. Mark the router as successful.
        8. Construct the workflow-specific execution plans.
        9. Store the selected execution plan.
        10. Return the updated workflow state.

        RAG Behaviour
        -------------
        RAGAgent is conditionally included when
        workflow_state["pitch_deck_text"] contains content.

        This keeps document retrieval optional while allowing
        pitch-deck-grounded workflows when supporting documents
        are available.

        LLM Judge Behaviour
        -------------------
        LLMJudgeAgent is intentionally excluded from the normal
        execution batches.

        OrchestratorAgent is responsible for triggering its
        mid-pipeline and final validation checkpoints at the
        appropriate stages.
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
        # 2. Classify user intent
        # ----------------------------------------------------
        # Send the prepared prompt to the LLM and receive the
        # raw intent classification.

        intent_response = text_call(
            messages=intent_prompt
        )

        # ----------------------------------------------------
        # 3. Validate supported intents
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
        # 4. Normalize LLM output
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
        # 4A. Apply safe fallback for unsupported intent
        # ----------------------------------------------------
        # If the model returns an unsupported value, route the
        # request to the general-chat workflow.

        if normalized_intent not in valid_intents:
            normalized_intent = "general_chat"

        workflow_state["intent"] = normalized_intent

        # ----------------------------------------------------
        # 5. Check whether pitch-deck context is available
        # ----------------------------------------------------
        # Determine whether the user supplied pitch-deck content.
        # This flag controls conditional RAGAgent inclusion.

        rag_response = bool(
            workflow_state["pitch_deck_text"]
        )

        # ----------------------------------------------------
        # 6. Mark IntentRouterAgent as successful
        # ----------------------------------------------------
        # The routing stage is complete once the intent has been
        # classified and the workflow can be constructed.

        workflow_state["pipeline_status"][
            "IntentRouterAgent"
        ] = "success"

        # ----------------------------------------------------
        # 7. Build intent-specific execution plans
        # ----------------------------------------------------
        # Construct the execution configuration for every supported
        # intent. Only the plan matching normalized_intent is stored
        # in workflow_state below.

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
        # 8. Store selected execution plan
        # ----------------------------------------------------
        # Select the workflow configuration corresponding to the
        # normalized user intent.

        workflow_state["execution_plan"] = (
            execution_pipeline[normalized_intent]
        )

        # ----------------------------------------------------
        # 9. Return updated workflow state
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
    # 5. Display detected intent
    # ------------------------------------------------
    # Verify which workflow was selected.

    print(
        workflow_state["intent"]
    )

    # ------------------------------------------------
    # 6. Display generated execution plan
    # ------------------------------------------------
    # Verify the batches and agents selected for the workflow.

    print(
        workflow_state["execution_plan"]
    )