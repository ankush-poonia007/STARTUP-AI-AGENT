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

from src.core.decorators import log_execution, handle_errors, track_timing, retry_on_failure
from src.core.exceptions import WorkflowStateError

from src.tools.pdf_tool import read_pdf
from src.tools.gemini_tool import text_call

from src.config.settings import GEMINI_LITE_MODEL

import copy
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class OrchestratorAgent:
    
    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, user_input:str, pitch_deck_path:str)->dict:
        
        # 1. Init workflow_state — all keys at empty defaults
        workflow_state = copy.deepcopy(STATE_SCHEMA)
        workflow_state['user_input'] = user_input
        
        # 2. Validate inputs — raise WorkflowStateError if user_input empty
        if  not workflow_state['user_input']:
            raise WorkflowStateError
        
        # 3. Extract pitch_deck_text via pdf_tool if path provided
        text = read_pdf(pitch_deck_path) if pitch_deck_path else ""
        workflow_state['pitch_deck_text'] = text
        
        # 4. Create state_lock = threading.Lock()
        state_lock = threading.Lock()  
                    
        # LOCK automatically released — even if exception occurs

        # 5. Build AGENT_REGISTRY dict inside run()
        AGENT_REGISTRY:dict = {
            "IntentRouterAgent":Intent_Router_Agent(),
            "MarketResearchAgent":MarketResearchAgent(),
            "WebSearchAgent":WebSearchAgent(),
            "RAGAgent":RAGAgent(),
            "LLMJudgeAgent":LLMJudgeAgent(),
            "PDFGeneratorAgent":PDFGeneratorAgent(),
            "ReportWriterAgent":ReportWriterAgent(),
            "GeneralChatAgent":GeneralChatAgent(),
            "AdvancementAgent":AdvancementAgent(),
            "NurturingAgent":NurturingAgent(),
            "IdeaGenerationAgent":IdeaGenerationAgent(),
            "RecommendationAgent":RecommendationAgent(),
            "RiskAnalystAgent":RiskAnalystAgent(),
            "TechAdvisorAgent":TechAdvisorAgent(),
            "MVPAdvisorAgent":MVPAdvisorAgent(),
            "StartupScorerAgent":StartupScorerAgent()
        }
        
        
        # 6. Run IntentRouterAgent — always first, always synchronous
        workflow_state = AGENT_REGISTRY["IntentRouterAgent"].run(workflow_state=workflow_state)
        
        # 7. Read execution_plan from workflow_state
        plan_order = workflow_state['execution_plan']
        
        # 8. Loop through execution_plan batches:
        #    - parallel=True  → ThreadPoolExecutor + state_lock on every state.update()
        #    - parallel=False → sequential single agent call
        #    - On failure     → log to workflow_state["errors"]
        #                     → update pipeline_status to "failed"
        #                     → continue remaining agents
        
        
        
        for batch in plan_order['execution_plan']:
            
            if batch['parallel']:
                
                
                with ThreadPoolExecutor() as executor:
                    futures = []
                    for agent in batch['agents']:
                        agent_name = AGENT_REGISTRY[agent]
                        futures.append( executor.submit( agent_name.run, workflow_state ) ) 
                    
                     
                    for completed_future in as_completed(futures):
                        
                        try:
                            result = completed_future.result()
                            with state_lock:           # LOCK acquired before write
                                workflow_state.update(result)   # safe write
                                
                        except Exception as e :
                                    workflow_state['errors'].append(
                                    {
                                            "agent_name":agent,
                                            "attempt":1,
                                            "time_stamp":datetime.now().isoformat(),
                                            "error":e
                                        }
                                    )
                                    workflow_state['pipeline_status'][agent] = "failed"
                            
            else:
                for agent in batch['agents']:
                    try:
                        agent_name = AGENT_REGISTRY[agent]
                        workflow_state = agent_name.run(workflow_state)
                    
                    except Exception as e :
                        workflow_state['errors'].append(
                            {
                                "agent_name":agent,
                                "attempt":1,
                                "time_stamp":datetime.now().isoformat(),
                                "error":e
                            }
                        )
                        workflow_state['pipeline_status'][agent] = "failed"
        
        # 9. Trigger PDFGeneratorAgent via Gemini Lite if user explicitly requested PDF
        
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a deterministic intent classifier. The user input may request a PDF document or export. "
                    "Respond with ONLY True or False. Do not add any other words, punctuation, or explanation."
                )
            },
            {
                "role": "user",
                "content": (
                    "User request: \"" + workflow_state['user_input'].strip() + "\"\n\n"
                    "Return True only if the user explicitly asks to generate, export, download, receive, or create a PDF document or report. "
                    "Return False otherwise."
                )
            }
        ]

        response = text_call(prompt, gemini_model=GEMINI_LITE_MODEL)
        normalized = str(response).strip().lower()
        if ( normalized == 'true'):
            workflow_state = PDFGeneratorAgent().run(workflow_state)
            
        return workflow_state


if __name__ == "__main__":
    print("OrchestratorAgent smoke test:")
    agent = OrchestratorAgent()
    print(f"  Created agent: {agent.__class__.__name__}")
    print(f"  Workflow state keys: {list(STATE_SCHEMA.keys())}")
    print("OrchestratorAgent guard is working.")

