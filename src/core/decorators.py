"""
Every agent run() method wrapped with 4 decorators:

@log_execution    → logs agent name + start time + end time
@track_timing     → records duration to workflow_state["execution_log"]
@retry_on_failure → retries up to MAX_RETRIES on any failure
@handle_errors    → catches ALL exceptions, logs to workflow_state["errors"]

Decorator import chain:
    core/decorators.py imports MAX_RETRIES from config/settings.py
    Agents import decorators from core/decorators.py
    Agents NEVER define retry or error logic themselves

Rules:
- ALL decorator logic lives in core/decorators.py ONLY
- NO retry logic written inside any agent file
- NO try/except blocks inside any agent file
- NO logging code inside any agent file
- Agents stay clean — zero boilerplate
- MAX_RETRIES defined once in settings.py — imported by decorators.py
"""
import time
from functools import wraps
from datetime import datetime, timezone
from src.config.settings import MAX_RETRIES, MIN_COOLTIME_RETRY
from src.core.exceptions import ( 
    AgentExecutionError,
    ToolConnectionError,
    WorkflowStateError
)

def log_execution(func):
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        
        try:
            start_time = time.time()
            workflow_state = args[1]
            
            res = func(*args, **kwargs)
            return res
        
        finally:
            workflow_state['execution_log'].append(
                {
                    'agent_name':args[0].__class__.__name__,
                    'start_time':start_time,
                    'end_time':time.time()
                }
            )
    
    return wrapper


def track_timing(func):
    
    @wraps(func)
    def wrapper(*args,**kwargs):
        
        try:
            start_time = time.time()
            workflow_state = args[1]
            
            res = func(*args,**kwargs)
            return res
        
        finally:
            workflow_state['execution_log'].append(
                {
                    "agent_name":args[0].__class__.__name__,
                    "execution_time":time.time() - start_time
                }
            )
            
    return wrapper
        

def retry_on_failure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0 
        
        while True:
            
            try :
                return func(*args , **kwargs)
            
            except (
                ToolConnectionError,  
                WorkflowStateError, 
                ) as e :
                
                retries += 1
              
                
                if retries > MAX_RETRIES:
                    raise AgentExecutionError(
                        f"Agent failed after {MAX_RETRIES} retries. Original error {str(e)}"
                    ) from e 
                time.sleep(MIN_COOLTIME_RETRY)
            
            except Exception as e:
                retries += 1 
        
                if retries > MAX_RETRIES:
                    raise AgentExecutionError(
                        f"Agent failed after {MAX_RETRIES} retries. Original error {str(e)}"
                    ) from e 
                else:
                    time.sleep(MIN_COOLTIME_RETRY)
                    
    return wrapper

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        workflow_state = args[1]
        try:
            return func(*args,**kwargs)
        
        except Exception as e :
            workflow_state["errors"].append(
                {
                    "agent"    : args[0].__class__.__name__,   # agent class name
                    "error"    : str(e),   # exception message
                    "timestamp": datetime.now(timezone.utc).isoformat()    # ISO 8601 format
                }
            )
            return None
        
    return wrapper


# ==========================================
# __main__ Block Simulation
# ==========================================
if __name__ == "__main__":
    # Create an empty shared workflow state object
    state = {
        "execution_log": [],
        "errors": []
    }

    # Set up a sample Agent class utilizing your decorators
    class OperationalAgent:
        def __init__(self):
            self.attempts = 0

        @handle_errors
        @log_execution
        @track_timing
        @retry_on_failure
        def run(self, workflow_state):
            self.attempts += 1
            print(f"[{datetime.now(timezone.utc).isoformat()}] OperationalAgent: Call attempt #{self.attempts}")
            
            # Simulate a transient Tool connection failure on the first attempt
            if self.attempts < 2:
                raise ToolConnectionError("Database connection dropped.")
                
            return "Task completed successfully!"

    print("--- Executing Standalone Agent System Test ---")
    agent = OperationalAgent()
    output = agent.run(state)
    
    print("\n--- Final Workflow Results ---")
    print(f"Return payload: {output}")
    print(f"State Logs: {state['execution_log']}")
    print(f"State Errors: {state['errors']}")