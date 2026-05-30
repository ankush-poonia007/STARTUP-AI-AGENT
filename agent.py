# agent.py
import requests
from prompts import SYSTEM_PROMPT
from context_manager import get_context
from concurrent.futures import ThreadPoolExecutor, as_completed

from tools import (
    summarize_text,
    search_knowledge_base,
    analyze_market,
    suggest_mvp,
    recommend_tech_stack,
    risk_analysis
)

class StartupAgent:
    
    """
    Main BizRadar AI Agent

    Responsibilities:
    - Load conversation context
    - Execute tools
    - Build final prompt
    - Send prompt to Ollama
    - Return structured response
    """
    
    def __init__( self, model_name="llama3.2:3b", base_url="http://127.0.0.1:11434" ):
        self.model_name = model_name
        self.base_url = base_url

    # =====================================================
    # Main Agent Runner
    # =====================================================

    def run(self, user_input: str) -> str:

        try:

            # =================================================
            # Get Context Memory
            # =================================================

            context = get_context()

            # =================================================
            # Execute Tools
            # =================================================
            
            """

    user_input
        ↓
    summarize_text()
        ↓
        ├──→ analyze_market() ──→ search_knowledge_base()
        │
        └──→ suggest_mvp()
                ↓
        ┌───────┴────────────┐
        ↓                    ↓
    recommend_tech_stack()  risk_analysis()
        └─────────┬──────────┘
                ↓
            LLM Final Report
            
"""

            """
            Source citation being stripped by summarization
            Parallel execution not implemented yet
            concurrent.futures still to research

            """


            """

            Group 1 — sequential
            summarize_text() → analyze_market()

            Group 2 — sequential
            suggest_mvp()

            Group 3 — parallel
            search_knowledge_base(), recommend_tech_stack(), risk_analysis()

            Group 4 — single
            LLM Final Report

            """
            
            

            with ThreadPoolExecutor() as executor:
                # submit tasks here
                summarized_text = summarize_text(user_input)

                market_analysis = analyze_market(summarized_text)
                
                mvp_suggestions = suggest_mvp(summarized_text, market_analysis)
                
                future ={
                    executor.submit(search_knowledge_base, market_analysis):"knowledge",
                    executor.submit(recommend_tech_stack, summarized_text, mvp_suggestions):"tech_stack",
                    executor.submit(risk_analysis, summarized_text, mvp_suggestions, market_analysis ):"risk"
                }
                
                for completed_future in as_completed(future):
                    name = future[completed_future]
                    result = completed_future.result()
                    
                    if name == "knowledge":
                        knowledge_results = result
                    elif name == "tech_stack":
                        tech_stack = result
                    elif name == "risk":
                        risk_results = result
                        
            # =================================================
            # Build Conversation Prompt
            # =================================================

            conversation = SYSTEM_PROMPT

            conversation += "\n\n"

            conversation += "CONVERSATION CONTEXT:\n"

            for item in context:

                role = item["role"]
                content = item["content"]

                conversation += f"{role}: {content}\n"

            # =================================================
            # Add Tool Outputs
            # =================================================

            conversation += f"""

TOOL RESULTS:

{knowledge_results}

{market_analysis}

{mvp_suggestions}

{tech_stack}

{summarize_text (risk_results)}

"""

            # =================================================
            # Add Current User Input
            # =================================================

            conversation += f"""

CURRENT USER INPUT:
{summarized_text}

"""

            # =================================================
            # Generate Ollama Response
            # =================================================

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": conversation,
                    "stream": False,
                    "keep_alive": "30m",
                    "options": {
                        "temperature": 0.4,
                        "num_predict": 1200,
                        "num_ctx": 6000
                    }
                },
                timeout=180
            )

            response.raise_for_status()

            result = response.json()

            final_response = result.get(
                "response",
                "No response generated."
            )

            return final_response

        except requests.exceptions.ConnectionError:

            return """
❌ Connection Error

Could not connect to Ollama.

Make sure:

1. Ollama is running
2. Port 11434 is available
3. The model is installed

Run:

ollama serve
"""


        except requests.exceptions.Timeout:

            return """
❌ Timeout Error

The model took too long to respond.

Possible causes:
- Large prompt
- Low system memory
- Model still loading
"""


        except Exception as error:

            return f"""
❌ Agent Error

Details:
{str(error)}

Checklist:
✓ Ollama running
✓ Model installed
✓ Model name correct
✓ Port 11434 available
"""