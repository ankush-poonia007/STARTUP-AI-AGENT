from src.tools.tavily_tool import ask_tavily
from concurrent.futures import ThreadPoolExecutor, as_completed
from tests.mock_workflow_state import MOCK_STATE_FULL 
from src.core.decorators import handle_errors, track_timing, log_execution, retry_on_failure

class MarketResearchAgent:
    
    """
    Input  → workflow_state['user_input']
    Steps  →
    1. Build 3 query strings embedding user_input
    2. Submit 3 tavily calls to ThreadPoolExecutor → store futures dict with labels
    3. Iterate futures with as_completed
    4. Extract title, summary, url from each result
    5. Format each as Title/Summary/URL block → concatenate to market_data string
    6. Write final string to workflow_state['market_data']
    7. Update workflow_state['pipeline_status']
    Output → workflow_state['market_data']
    """
    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state:dict)->dict:
        
        user_input:str = workflow_state['user_input']
        
        market_size_prompt = f"Market Size for {user_input} industry"
        trends_prompt = f"Market trends for {user_input} industry"
        demand_prompt = f"Market demand for {user_input} industry"
        
        
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(ask_tavily, market_size_prompt):"market_size",
                executor.submit(ask_tavily, trends_prompt):"trends",
                executor.submit(ask_tavily, demand_prompt):"demand",
            }

            text = """"""
            for completed_future in as_completed(futures):
                                    
                
                result = completed_future.result()
                label = futures[completed_future]
                
                text += f"\n=== {label} ===\n"
                
                for item in result:
                    text += f"""Title: {item["title"]}
Summary: {item["content"]}
URL: {item["url"]}"""
                
                text += "\n"
        
        
        workflow_state["market_data"] = text
        workflow_state["pipeline_status"]["MarketResearchAgent"] = "success"
        
        return workflow_state
    

if __name__ == "__main__":
    
    workflow_state = MOCK_STATE_FULL
    
    call = MarketResearchAgent()
    
    workflow_state = call.run(workflow_state)
    
    print(workflow_state["market_data"])
    