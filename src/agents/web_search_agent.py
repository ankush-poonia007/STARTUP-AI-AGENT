"""
File        : agents/web_search_agent.py
Triggered By: full_analysis, partial_idea
Tools       : tavily_tool.py
Input       : workflow_state["user_input"]
Output      : workflow_state["web_search_results"]

Why separate from MarketResearchAgent:
    MarketResearchAgent → "what is the market?"
    WebSearchAgent      → "who exists in this market?"
    Different query intent = different results = different downstream value.

Output Format:
    workflow_state["web_search_results"] → str
        === Competitors ===
        Title: <title>
        Summary: <summary>
        URL: <url>

        === Funding Landscape ===
        Title: <title>
        Summary: <summary>
        URL: <url>

        === Existing Solutions ===
        Title: <title>
        Summary: <summary>
        URL: <url>

Responsibilities:
- Tavily search for competitors
- Search for funding landscape
- Search for existing market solutions
- Return summarized competitor string with citations
"""
from src.core.decorators import handle_errors, log_execution, track_timing, retry_on_failure
from tests.mock_workflow_state import MOCK_STATE_FULL
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.tools.tavily_tool import ask_tavily

class WebSearchAgent:
    
    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    
    def run(self, workflow_state:dict)->dict:
        
        user_input = workflow_state["user_input"]
        
        competitor_prompt = f"Search for competitors in market for {user_input}"
        funding_prompt = f"Search for funding landscape insights for {user_input}"
        solutions_prompt = f"Search for existing market solutions present in market for {user_input}"
        
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(ask_tavily, competitor_prompt) : "Competitor",
                executor.submit(ask_tavily, funding_prompt) : "Funding",
                executor.submit(ask_tavily, solutions_prompt) : "Solutions",
            }
            
            content = """"""
            
            for completed_futures in as_completed(futures):
                
                result = completed_futures.result()
                label = futures[completed_futures]
                
                content += f"""
================================================================================
+++++++++++++++++++++++++++++++++  {label}  ++++++++++++++++++++++++++++++++++
================================================================================"""
                
                for item in result:
                    content += f"""Title:  {item["title"]}

Summary: {item["content"]}

URL: {item["url"]}
"""
                content += "\n\n"
                
        workflow_state["web_search_results"] = content
        workflow_state["pipeline_status"]["WebSearchAgent"] = "sucess"
        return workflow_state
    
    
if __name__ == "__main__":
    
    workflow_state = MOCK_STATE_FULL
    
    mock_call = WebSearchAgent()
    
    workflow_state = mock_call.run(workflow_state)
    
    print(workflow_state["web_search_results"])