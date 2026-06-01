# agent.py
import os
import json
from groq import Groq
from groq import AuthenticationError, NotFoundError, RateLimitError,  BadRequestError, APIStatusError, APIConnectionError
from prompts import SYSTEM_PROMPT
from context_manager import get_context
from concurrent.futures import ThreadPoolExecutor, as_completed
from tools_description import tools
from dotenv import load_dotenv
from tools import (
    summarize_text,
    search_knowledge_base,
    analyze_market,
    suggest_mvp,
    recommend_tech_stack,
    risk_analysis
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key = GROQ_API_KEY
)


class StartupAgent:
    
    
    def __init__( self, model_name="llama-3.3-70b-versatile"):
        self.model_name = model_name
        self.messages = []
        self.future ={}
        self.available_functions = {
                    "analyze_market": analyze_market,
                    "summarize_text": summarize_text,
                    "search_knowledge_base": search_knowledge_base,
                    "suggest_mvp": suggest_mvp,
                    "recommend_tech_stack": recommend_tech_stack,
                    "risk_analysis": risk_analysis,
                }

    # =====================================================
    # Main Agent Runner
    # =====================================================

    def run(self, user_input: str) -> str:

        try:
            
            context = get_context()

            self.messages.append({"role": "system", "content": SYSTEM_PROMPT})
            
            for item in context:

                role = item["role"]
                content = item["content"]

                self.messages.append( {"role": role, "content":content } )
            
            self.messages.append( {"role": "user", "content": user_input} )
            
            


            while True:
                # make the API call with messages and tools
                response = client.chat.completions.create(
                    messages= self.messages,
                    model = self.model_name,
                    tools=tools,
                    temperature=0.5,
                    max_completion_tokens=4096,
                    )

                response_message = response.choices[0].message
                
                self.messages.append(response.choices[0].message)   

                tool_calls = response_message.tool_calls or []
                
                
                if tool_calls :
                    # what three things do you do here?
                    # tool_use handling — collect tool names and inputs, execute in parallel, append results to messages
                    
                    
                    with ThreadPoolExecutor() as executor:
                        
                        for tool_call in tool_calls:
                            # submit tasks here
                            
                            function_name = tool_call.function.name
                            function_to_call = self.available_functions[function_name]
                            function_args = json.loads(tool_call.function.arguments)
                            
                            self.future[executor.submit(function_to_call , **function_args)] = tool_call.id
                            print(f"🔧 Calling tool: {function_name}")
                            
                        for completed_future in as_completed(self.future):
                            tool_call_id = self.future[completed_future]
                            function_response = completed_future.result( timeout = 60 )
                            
                            self.messages.append(
                                {"role": "tool",
                                "content": str(function_response),
                                "tool_call_id": tool_call_id,
                                }
                        )
                    self.future.clear()
                else:
                    
                    return response_message.content
            

        except AuthenticationError as e:
    # Handle bad API keys (401)
           return f"Authentication failed. Check your API key. Details: {e}"

        except NotFoundError as e:
            # Handle bad model names or wrong URLs (404)
            return f"Resource not found. Check the model ID string. Details: {e}"

        except RateLimitError as e:
            # Handle rate limiting (429)
            return f"Rate limit exceeded. Implement backoff retry. Details: {e}"

        except BadRequestError as e:
            # Handle invalid payload schema / parameters (400)
            return f"Invalid request parameters. Details: {e}"

        except APIStatusError as e:
            # Catch-all for other non-success HTTP status codes (e.g., 403, 500)
            return f"Groq API returned an error status ({e.status_code}): {e.message}"

        except APIConnectionError as e:
            # Network issues, DNS failures, or connection timeouts
            return f"Failed to connect to Groq servers: {e}"
        
        except Exception as error:

                    return f"""
❌ Agent Error

Details:
{str(error)}
"""