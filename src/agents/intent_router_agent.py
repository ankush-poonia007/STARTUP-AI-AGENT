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
    """This Agent is to detect the intent of the user based on the user_input from workflow_agent and write in the intent, execution_plan in the workflow_state back"""
    
    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    
    def run(self,workflow_state: dict):
        intent_prompt = [
            {
                "role":"system",
                "content":INTENT_ROUTER_PROMPT
            },
            {
                "role":"user",
                "content":workflow_state['user_input']
            }
        ]
        intent_response = text_call(prompt=intent_prompt)

        valid_intents = {
            "full_analysis",
            "partial_idea",
            "idea_exploration",
            "nurturing",
            "advancement",
            "general_chat",
            "pdf_request"
        }
        normalized_intent = str(intent_response).strip().lower().replace(" ", "_")
        normalized_intent = normalized_intent.replace("-", "_")
        if normalized_intent not in valid_intents:
            normalized_intent = "general_chat"

        workflow_state['intent'] = normalized_intent

        rag_response = bool(workflow_state.get('pitch_deck_text'))
        workflow_state.setdefault("pipeline_status", {})["IntentRouterAgent"] = "success"

        execution_pipeline = {
            "full_analysis": {
                "execution_order": [
                    "IntentRouterAgent",
                    "MarketResearchAgent",
                    "WebSearchAgent"
                ] + (["RAGAgent"] if rag_response else []) + [
                    "MVPAdvisorAgent",
                    "TechAdvisorAgent",
                    "LLMJudgeAgent.run_mid",
                    "RiskAnalystAgent",
                    "StartupScorerAgent",
                    "RecommendationAgent",
                    "ReportWriterAgent",
                    "LLMJudgeAgent.run_final",
                    "PDFGeneratorAgent (on request)"
                ],
                "execution_plan": [
                    {
                        "batch": 1,
                        "agents": ["MarketResearchAgent", "WebSearchAgent"] + (["RAGAgent"] if rag_response else []),
                        "parallel": True,
                        "note": "RAGAgent conditional if pitch_deck_text non-empty" if rag_response else None
                    },
                    {"batch": 2, "agents": ["MVPAdvisorAgent", "TechAdvisorAgent"], "parallel": True},
                    {"batch": 3, "agents": ["LLMJudgeAgent.run_mid"], "parallel": False},
                    {"batch": 4, "agents": ["RiskAnalystAgent"], "parallel": False},
                    {"batch": 5, "agents": ["StartupScorerAgent"], "parallel": False},
                    {"batch": 6, "agents": ["RecommendationAgent"], "parallel": False},
                    {"batch": 7, "agents": ["ReportWriterAgent"], "parallel": False},
                    {"batch": 8, "agents": ["LLMJudgeAgent.run_final"], "parallel": False},
                    {"batch": 9, "agents": ["PDFGeneratorAgent"], "parallel": False, "note": "Generate only if user explicitly requests PDF"}
                ]
            },

            "partial_idea": {
                "execution_order": [
                    "IntentRouterAgent",
                    "MarketResearchAgent",
                    "WebSearchAgent"
                ] + (["RAGAgent"] if rag_response else []) + [
                    "MVPAdvisorAgent",
                    "TechAdvisorAgent",
                    "RecommendationAgent",
                    "NurturingAgent",
                    "ReportWriterAgent",
                    "LLMJudgeAgent.run_final",
                    "PDFGeneratorAgent (on request)"
                ],
                "execution_plan": [
                    {
                        "batch": 1,
                        "agents": ["MarketResearchAgent", "WebSearchAgent"] + (["RAGAgent"] if rag_response else []),
                        "parallel": True,
                        "note": "RAGAgent conditional if pitch_deck_text non-empty" if rag_response else None
                    },
                    {"batch": 2, "agents": ["MVPAdvisorAgent", "TechAdvisorAgent"], "parallel": True},
                    {"batch": 3, "agents": ["RecommendationAgent", "NurturingAgent"], "parallel": False},
                    {"batch": 4, "agents": ["ReportWriterAgent"], "parallel": False},
                    {"batch": 5, "agents": ["LLMJudgeAgent.run_final"], "parallel": False},
                    {"batch": 6, "agents": ["PDFGeneratorAgent"], "parallel": False, "note": "On-demand only; requires final_report"}
                ]
            },

            "idea_exploration": {
                "execution_order": [
                    "IntentRouterAgent",
                    "IdeaGenerationAgent"
                ],
                "execution_plan": [
                    {"batch": 1, "agents": ["IdeaGenerationAgent"], "parallel": False}
                ]
            },

            "nurturing": {
                "execution_order": [
                    "IntentRouterAgent"
                ] + (["RAGAgent"] if rag_response else []) + [
                    "RecommendationAgent",
                    "NurturingAgent",
                    "ReportWriterAgent",
                    "LLMJudgeAgent.run_final",
                    "PDFGeneratorAgent (on request)"
                ],
                "execution_plan": [
                    {
                        "batch": 1,
                        "agents": ["RecommendationAgent", "NurturingAgent"] + (["RAGAgent"] if rag_response else []),
                        "parallel": True,
                        "note": "RAGAgent conditional if pitch_deck_text non-empty" if rag_response else None
                    },
                    {"batch": 2, "agents": ["ReportWriterAgent"], "parallel": False},
                    {"batch": 3, "agents": ["LLMJudgeAgent.run_final"], "parallel": False},
                    {"batch": 4, "agents": ["PDFGeneratorAgent"], "parallel": False, "note": "On-demand only"}
                ]
            },

            "advancement": {
                "execution_order": [
                    "IntentRouterAgent",
                    "AdvancementAgent",
                    "ReportWriterAgent",
                    "LLMJudgeAgent.run_final",
                    "PDFGeneratorAgent (on request)"
                ],
                "execution_plan": [
                    {"batch": 1, "agents": ["AdvancementAgent"], "parallel": False},
                    {"batch": 2, "agents": ["ReportWriterAgent"], "parallel": False},
                    {"batch": 3, "agents": ["LLMJudgeAgent.run_final"], "parallel": False},
                    {"batch": 4, "agents": ["PDFGeneratorAgent"], "parallel": False, "note": "On-demand only"}
                ]
            },

            "general_chat": {
                "execution_order": [
                    "IntentRouterAgent",
                    "GeneralChatAgent"
                ],
                "execution_plan": [
                    {"batch": 1, "agents": ["GeneralChatAgent"], "parallel": False}
                ]
            },

            "pdf_request": {
                "execution_order": [
                    "IntentRouterAgent",
                    "PDFGeneratorAgent (requires final_report)"
                ],
                "execution_plan": [
                    {"batch": 1, "agents": ["PDFGeneratorAgent"], "parallel": False, "note": "PDF generation is on-demand and requires workflow_state['final_report'] to exist; if final_report missing, orchestrator should produce or return error"}
                ]
            }
        }

        workflow_state["execution_plan"] = execution_pipeline[normalized_intent]

        return workflow_state
        

if __name__ == "__main__":
    workflow_state = MOCK_STATE_EMPTY
    workflow_state['user_input'] = "AI-powered tiffin delivery for college students"
    
    obj = Intent_Router_Agent()
    
    workflow_state = obj.run(workflow_state)
    
    print(workflow_state['intent'])
    print(workflow_state['execution_plan'])
    
    