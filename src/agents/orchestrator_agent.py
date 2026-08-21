"""
File        : agents/orchestrator_agent.py
Triggered By: Every request — always first
Tools       : None — delegation only
Input       : user_input (str) + pitch_deck_path (str)
Output      : Complete final workflow_state dict

Purpose:
    OrchestratorAgent is the central coordinator of the multi-agent
    startup-analysis workflow.

    It does not perform startup analysis itself. Instead, it:
        - Initializes the shared workflow state.
        - Runs IntentRouterAgent first.
        - Reads the execution plan selected by the intent router.
        - Executes agents according to the defined batches.
        - Coordinates parallel and sequential execution.
        - Triggers LLMJudgeAgent at the required checkpoints.
        - Handles explicit PDF-generation requests.
        - Returns the final workflow state.

What it does NOT do:
    Does NOT contain startup-analysis business logic.
    Does NOT generate market, MVP, technology, risk, or recommendation content.
    Does NOT own the output keys produced by downstream agents.
    Does NOT decide which workflow should run — IntentRouterAgent does that.

Execution Sequence:
    1. Initialize workflow_state from the shared state schema.
    2. Store the user's input in workflow_state.
    3. Validate user_input.
    4. Extract pitch_deck_text when a pitch deck path is provided.
    5. Create a state lock for safe parallel state updates.
    6. Build the AGENT_REGISTRY.
    7. Run IntentRouterAgent first and synchronously.
    8. Read the selected execution_plan.
    9. Execute each planned batch.
    10. Run LLMJudgeAgent.run_mid() after MVPAdvisorAgent for full_analysis.
    11. Run LLMJudgeAgent.run_final() after ReportWriterAgent for
        full_analysis and partial_idea.
    12. Check whether the user explicitly requested a PDF.
    13. Run PDFGeneratorAgent when required.
    14. Return the completed workflow_state.

Parallel Execution:
    Agents belonging to a parallel batch are submitted to
    ThreadPoolExecutor.

    Each completed result is merged into workflow_state while
    state_lock is held so concurrent writes do not occur unsafely.

Sequential Execution:
    Agents in sequential batches execute one after another.
    This allows downstream agents to consume state produced by
    upstream agents.

LLM Judge Checkpoints:
    run_mid():
        Runs only for full_analysis after the MVPAdvisorAgent batch.

    run_final():
        Runs for full_analysis and partial_idea after ReportWriterAgent.

    Judge failures are recorded in workflow_state["errors"] rather than
    directly stopping the remaining pipeline.

Failure Handling:
    Input validation failure → WorkflowStateError.
    Parallel agent failure → record error + mark agent failed.
    Sequential agent failure → record error + mark agent failed.
    Mid-judge failure → record error and continue.
    Final-judge failure → record error and continue.
    PDF generation is executed only when explicitly requested.
"""

from src.agents.intent_router_agent import Intent_Router_Agent
from src.agents.advancement_agent import AdvancementAgent
from src.agents.general_chat_agent import GeneralChatAgent
from src.agents.idea_generation_agent import IdeaGenerationAgent
from src.agents.llm_judge_agent import LLMJudgeAgent
from src.agents.market_research_agent import MarketResearchAgent
from src.agents.mvp_advisor_agent import MVPAdvisorAgent
from src.agents.nurturing_agent import NurturingAgent
from src.agents.pdf_generator_agent import PDFGeneratorAgent
from src.agents.rag_agent import RAGAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.report_writer_agent import ReportWriterAgent
from src.agents.risk_analyst_agent import RiskAnalystAgent
from src.agents.startup_scorer_agent import StartupScorerAgent
from src.agents.tech_advisor_agent import TechAdvisorAgent
from src.agents.web_search_agent import WebSearchAgent
from src.agents.workflow_state import workflow_state as STATE_SCHEMA


from src.core.exceptions import WorkflowStateError
from src.core.decorators import (
    log_execution,
    handle_errors,
    track_timing,
    retry_on_failure
)


from src.config.settings import GEMINI_LITE_MODEL


from src.tools.gemini_tool import text_call
from src.tools.pdf_tool import read_pdf


import threading
import copy


from datetime import datetime
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)


class OrchestratorAgent:
    """
    Central workflow coordinator for the BizRadar multi-agent system.

    OrchestratorAgent does not perform domain-specific startup analysis.
    Its responsibility is to coordinate the agents that perform that work.

    The agent receives the user's request, initializes the shared state,
    delegates intent detection to IntentRouterAgent, and then executes
    the resulting workflow plan.

    Responsibilities:
        - Initialize and prepare workflow_state.
        - Validate the initial user input.
        - Load pitch-deck content when available.
        - Maintain the registry of available agents.
        - Execute parallel agent batches safely.
        - Execute sequential agent batches in order.
        - Trigger the mid-pipeline LLM judge when required.
        - Trigger the final LLM judge when required.
        - Trigger PDF generation when explicitly requested.
        - Preserve execution errors in the shared workflow state.

    Important:
        IntentRouterAgent decides the workflow.
        OrchestratorAgent executes that workflow.

        LLMJudgeAgent is not treated as a normal execution-plan batch.
        The orchestrator triggers its checkpoints after the required
        upstream stage has completed.
    """

    @log_execution
    @track_timing
    @retry_on_failure
    @handle_errors
    def run( 
            self,
            user_input: str,
            pitch_deck_path: str
        ) -> dict:
        """
        Execute the startup-analysis workflow from initialization
        through final workflow-state generation.

        Parameters
        ----------
        user_input : str
            Original startup idea, question, or user request.

        pitch_deck_path : str
            Path to the user's pitch deck when one is provided.
            An empty path means no pitch deck is available.

        Returns
        -------
        dict
            The final shared workflow state after all applicable
            workflow stages have been executed.

        Processing Stages
        -----------------
        1. Initialize a fresh workflow state from STATE_SCHEMA.
        2. Store the user's input.
        3. Validate that user_input is available.
        4. Extract pitch-deck text when a path is provided.
        5. Create the thread-safety lock.
        6. Register all available workflow agents.
        7. Run IntentRouterAgent synchronously.
        8. Read the selected execution plan.
        9. Execute every workflow batch according to its configuration.
        10. Trigger run_mid() when full_analysis reaches MVPAdvisorAgent.
        11. Trigger run_final() after ReportWriterAgent for
            full_analysis or partial_idea.
        12. Perform the explicit PDF-request check.
        13. Run PDFGeneratorAgent when required.
        14. Return the final workflow state.

        Parallel Batch Behaviour
        -------------------------
        Agents in a parallel batch are submitted to a
        ThreadPoolExecutor.

        Each completed future is mapped back to its originating agent.
        Successful results are merged into workflow_state under
        state_lock.

        Failed agents are recorded in workflow_state["errors"] and
        their pipeline status is marked as "failed".

        Sequential Batch Behaviour
        ---------------------------
        Agents in a sequential batch execute one at a time.
        Each agent receives the workflow state returned by the
        previous agent.

        LLM Judge Behaviour
        -------------------
        The mid-pipeline judge is executed only when:

            intent == "full_analysis"

        and the current batch contains:

            "MVPAdvisorAgent"

        The final judge is executed when:

            intent in {"full_analysis", "partial_idea"}

        and the current batch contains:

            "ReportWriterAgent"

        Judge failures are recorded in the workflow state so that
        the normal pipeline is not unnecessarily interrupted.
        """

        # ----------------------------------------------------
        # 1. Initialize workflow state
        # ----------------------------------------------------
        # Create an isolated copy of the predefined workflow schema.
        # This prevents one request from modifying the shared template.

        workflow_state = copy.deepcopy(STATE_SCHEMA)
        workflow_state["user_input"] = user_input

        # ----------------------------------------------------
        # 2. Validate user input
        # ----------------------------------------------------
        # The workflow cannot start without a usable user request.

        if not workflow_state["user_input"]:
            raise WorkflowStateError

        # ----------------------------------------------------
        # 3. Extract pitch-deck text when provided
        # ----------------------------------------------------
        # If a pitch-deck path exists, read its contents through pdf_tool.
        # Otherwise, keep pitch_deck_text empty so RAG can be skipped.

        text = (
            read_pdf(pitch_deck_path)
            if pitch_deck_path
            else ""
        )

        workflow_state["pitch_deck_text"] = text

        # ----------------------------------------------------
        # 4. Create lock for safe parallel state updates
        # ----------------------------------------------------
        # Parallel agents may finish at different times.
        # The lock protects the shared workflow_state during updates.

        state_lock = threading.Lock()

        # ----------------------------------------------------
        # 5. Build agent registry
        # ----------------------------------------------------
        # Create one registry containing every agent that the
        # execution plans can reference.

        AGENT_REGISTRY: dict = {
            "IntentRouterAgent": Intent_Router_Agent(),
            "MarketResearchAgent": MarketResearchAgent(),
            "WebSearchAgent": WebSearchAgent(),
            "RAGAgent": RAGAgent(),
            "LLMJudgeAgent": LLMJudgeAgent(),
            "PDFGeneratorAgent": PDFGeneratorAgent(),
            "ReportWriterAgent": ReportWriterAgent(),
            "GeneralChatAgent": GeneralChatAgent(),
            "AdvancementAgent": AdvancementAgent(),
            "NurturingAgent": NurturingAgent(),
            "IdeaGenerationAgent": IdeaGenerationAgent(),
            "RecommendationAgent": RecommendationAgent(),
            "RiskAnalystAgent": RiskAnalystAgent(),
            "TechAdvisorAgent": TechAdvisorAgent(),
            "MVPAdvisorAgent": MVPAdvisorAgent(),
            "StartupScorerAgent": StartupScorerAgent()
        }

        # ----------------------------------------------------
        # 6. Run IntentRouterAgent first
        # ----------------------------------------------------
        # IntentRouterAgent determines the user's intent and creates
        # the execution plan that controls the remaining pipeline.

        workflow_state = (
            AGENT_REGISTRY["IntentRouterAgent"]
            .run(workflow_state=workflow_state)
        )

        # ----------------------------------------------------
        # 7. Read execution plan
        # ----------------------------------------------------
        # Retrieve the plan selected by IntentRouterAgent.

        plan_order = workflow_state["execution_plan"]

        # ----------------------------------------------------
        # 8. Execute workflow batches
        # ----------------------------------------------------
        # Each batch defines which agents run and whether they
        # can execute concurrently.

        for batch in plan_order["execution_plan"]:

            # ------------------------------------------------
            # 8A. Execute parallel batch
            # ------------------------------------------------
            # Submit all agents in the current parallel batch.
            # Their futures are mapped to agent names so failures
            # can be attributed to the correct agent.

            if batch["parallel"]:

                with ThreadPoolExecutor() as executor:

                    futures = {}

                    for agent in batch["agents"]:

                        # ------------------------------------------------
                        # PDFGeneratorAgent is never executed from a
                        # normal execution-plan batch.
                        #
                        # PDF generation is handled explicitly after the
                        # workflow when the user requests a PDF.
                        # ------------------------------------------------
                        if agent == "PDFGeneratorAgent":
                            continue

                        agent_instance = AGENT_REGISTRY[agent]

                        future = executor.submit(
                            agent_instance.run,
                            workflow_state
                        )

                        futures[future] = agent

                    for completed_future in as_completed(
                        futures
                    ):

                        agent = futures[completed_future]

                        try:

                            # Retrieve the completed agent's result.
                            result = (
                                completed_future.result()
                            )

                            # Safely merge the result into shared state.
                            with state_lock:
                                workflow_state.update(result)

                        except Exception as e:

                            # Record the failure without stopping
                            # the remaining parallel agents.

                            workflow_state["errors"].append(
                                {
                                    "agent_name": agent,
                                    "attempt": 1,
                                    "time_stamp": (
                                        datetime.now().isoformat()
                                    ),
                                    "error": e
                                }
                            )

                            workflow_state[
                                "pipeline_status"
                            ][agent] = "failed"

            # ------------------------------------------------
            # 8B. Execute sequential batch
            # ------------------------------------------------
            # Sequential agents run in the exact order defined
            # by the execution plan.

            else:

                for agent in batch["agents"]:

                    # ------------------------------------------------
                    # PDFGeneratorAgent is never executed from a
                    # normal execution-plan batch.
                    #
                    # PDF generation is handled explicitly after the
                    # workflow when the user requests a PDF.
                    # ------------------------------------------------
                    if agent == "PDFGeneratorAgent":
                        continue

                    try:

                        # Resolve the requested agent from the registry.
                        agent_instance = (
                            AGENT_REGISTRY[agent]
                        )

                        # Pass the latest workflow state into the agent.
                        workflow_state = (
                            agent_instance.run(
                                workflow_state
                            )
                        )

                    except Exception as e:

                        # Record the failure and allow the orchestrator
                        # to continue to the next workflow stage.

                        workflow_state["errors"].append(
                            {
                                "agent_name": agent,
                                "attempt": 1,
                                "time_stamp": (
                                    datetime.now().isoformat()
                                ),
                                "error": e
                            }
                        )

                        workflow_state[
                            "pipeline_status"
                        ][agent] = "failed"

            # ------------------------------------------------
            # 8C. Mid-pipeline LLM judge checkpoint
            #
            # Runs only for full_analysis after the
            # MVPAdvisorAgent batch has completed.
            # ------------------------------------------------
            # At this point MVP and technology recommendations
            # are available for quality validation.
            #
            # The judge is executed here instead of being placed
            # inside the normal execution plan so the checkpoint
            # occurs only after its required upstream batch finishes.

            if (
                workflow_state["intent"] == "full_analysis"
                and "MVPAdvisorAgent" in batch["agents"]
            ):

                try:

                    workflow_state = (
                        AGENT_REGISTRY["LLMJudgeAgent"]
                        .run_mid(workflow_state)
                    )

                except Exception as e:

                    # A judge failure is recorded but does not
                    # directly terminate the analysis pipeline.

                    workflow_state["errors"].append(
                        {
                            "agent_name": (
                                "LLMJudgeAgent.run_mid"
                            ),
                            "attempt": 1,
                            "time_stamp": (
                                datetime.now().isoformat()
                            ),
                            "error": e
                        }
                    )

            # ------------------------------------------------
            # 8D. Final LLM judge checkpoint
            #
            # Runs after ReportWriterAgent for
            # full_analysis and partial_idea.
            # ------------------------------------------------
            # The complete report is now available, allowing the
            # final judge to evaluate the finished analysis.

            elif (
                workflow_state["intent"]
                in {"full_analysis", "partial_idea"}
                and "ReportWriterAgent" in batch["agents"]
            ):

                try:

                    workflow_state = (
                        AGENT_REGISTRY["LLMJudgeAgent"]
                        .run_final(workflow_state)
                    )

                except Exception as e:

                    # Final-judge failure is preserved in the shared
                    # error list while allowing the workflow to finish.

                    workflow_state["errors"].append(
                        {
                            "agent_name": (
                                "LLMJudgeAgent.run_final"
                            ),
                            "attempt": 1,
                            "time_stamp": (
                                datetime.now().isoformat()
                            ),
                            "error": e
                        }
                    )

        # ----------------------------------------------------
        # 9. Detect explicit PDF request
        # ----------------------------------------------------
        # Use the lightweight Gemini model to determine whether
        # the user explicitly requested PDF generation.

        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a deterministic intent classifier. "
                    "The user input may request a PDF document "
                    "or export. Respond with ONLY True or False. "
                    "Do not add any other words, punctuation, "
                    "or explanation."
                )
            },
            {
                "role": "user",
                "content": (
                    "User request: \""
                    + workflow_state["user_input"].strip()
                    + "\"\n\n"
                    "Return True only if the user explicitly "
                    "asks to generate, export, download, receive, "
                    "or create a PDF document or report. "
                    "Return False otherwise."
                )
            }
        ]

        response = text_call(
            prompt,
            gemini_model=GEMINI_LITE_MODEL
        )

        normalized = str(response).strip().lower()

        if normalized == "true":

            # Run PDF generation only after the user has explicitly
            # requested a PDF document or report.

            workflow_state = (
                AGENT_REGISTRY["PDFGeneratorAgent"]
                .run(workflow_state)
            )

        # ----------------------------------------------------
        # 10. Return final workflow state
        # ----------------------------------------------------
        # The orchestrator returns the accumulated state containing
        # all outputs, statuses, errors, and generated reports.

        return workflow_state


# ----------------------------------------------------
# LOCAL TEST
# ----------------------------------------------------
# This smoke test verifies that the orchestrator class can be
# initialized and that the workflow schema is accessible.

if __name__ == "__main__":

    print("OrchestratorAgent smoke test:")

    agent = OrchestratorAgent()

    print(
        f"Created agent: {agent.__class__.__name__}"
    )

    print(
        f"Workflow state keys: {list(STATE_SCHEMA.keys())}"
    )

    print("OrchestratorAgent guard is working.")