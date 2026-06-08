# tools.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.api_core import exceptions
from google import genai
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import requests 

from rag import (
    query_rag,
    embed_and_store,
    ingest_pdf
)

"""

    user_input
        ↓
    summarize_text() Done
        ↓
        ├──→ analyze_market() ──→ search_knowledge_base()[sources for hallucination removal]  Done
        │                                   
        ├──→ suggest_mvp()              
        │                               
        ├──→ recommend_tech_stack()      
        │
        └──→ risk_analysis()
                ↓
        All results accumulate context
                ↓
        LLM Final Report
        
    1. Shared client initialized once in tools.py ✅ 

    2. Tools using Tavily — analyze_market(), search_knowledge_base()

    3. Tools using Groq/Gemini + prompt template — suggest_mvp(), recommend_tech_stack(), risk_analysis()

    4. Input flow — user_input → summarize_text() → feeds all parallel tools

    5. Next to build — suggest_mvp() using summarized text + prompt template

    6. To research — asyncio, concurrent.futures, Fan-Out Fan-In pattern

"""

load_dotenv()

        
# To install: pip install tavily-python
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini API 
gemini_client = genai.Client(api_key = GEMINI_API_KEY)
# Automatically detects GOOGLE_API_KEY from the environment
# gemini_client = genai.Client()

# Tavily API 
tavily_client = TavilyClient(TAVILY_API_KEY)


def summarize_text(message: dict) -> str:
    """
    Basic placeholder summarizer.
    """
        
    try:
        with ThreadPoolExecutor() as executor:
        
            future ={}
            for url in message:
                full_prompt = f"""You are a professional summarizer. 
Please read the following text and provide a concise and clear summary.
--- 

Text to summarize: {message[url][1]} --- 

Summary:
    """ 
                future[executor.submit(gemini_client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=full_prompt
                )] = url
                
            
            response =""""""
            
            for complete_future in as_completed(future):
                
                response += f"""Title: {message[future[complete_future]][0]}
Summary:{complete_future.result( timeout= 60 ).text}
URL:{future[complete_future]} 
"""

        return response
    
    except exceptions.ResourceExhausted as e:
        return f"Rate Limited (429): Backing off request loops. Details: {e}"
    
    except exceptions.Unauthenticated as e:
        return f"Auth Error (401): Check system environment API keys. Details: {e}"
    
    except exceptions.GoogleAPICallError as e:
        return f"Generic API Error: {e.code} - {e.message}"
    
    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"


# Tavily API Search Web Browser
def analyze_market(startup_idea: str) -> str:
    """
    Analyze market potential for a startup idea.
    """
    
    try :
        response = tavily_client.search(
            query=startup_idea,
            include_answer="advanced",
            search_depth="basic",
            country="india",
            exclude_domains=["facebook.com", "x.com", "instagram.com"]
        )

        
        message = {}
        for result in response["results"]:
            mess = """"""
            mess += "\nResult :"
            mess += "\nContent: " + result["content"]
            message[result["url"]] = [result["title"],mess]
            
            
        return message
    
    except requests.exceptions.HTTPError :
        return f"HTTP error occurred" # e.g., 404 Not Found
        
    except requests.exceptions.ConnectionError:
        return "Connection error: Check your internet or server URL."
    
    except requests.exceptions.Timeout:
        return  "Timeout error: The server took too long to respond."
    
    except requests.exceptions.RequestException :
        return f"An unexpected error occurred"

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"


# Tavily API Search Web Browser
def search_knowledge_base(query: str) -> str:
    """
    Simulated knowledge base search.
    """

    try :
        response = tavily_client.search(
                query = query,
                include_answer="advanced",
                search_depth = "advanced",
                country="india",
                exclude_domains=["facebook.com", "x.com", "instagram.com"]
            )
        
        message = {}
        for result in response["results"]:
            mess = """"""
            mess += "\nResult :"
            mess += "\nContent: " + result["content"]
            message[result["url"]] = [result["title"],mess]
        
        return message
    
    except requests.exceptions.HTTPError :
        return f"HTTP error occurred" # e.g., 404 Not Found
        
    except requests.exceptions.ConnectionError:
        return "Connection error: Check your internet or server URL."
    
    except requests.exceptions.Timeout:
        return  "Timeout error: The server took too long to respond."
    
    except requests.exceptions.RequestException :
        return f"An unexpected error occurred"

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"


def suggest_mvp(startup_idea: str) -> str:

    full_prompt = f"""You are a startup advisor. Based on this idea: {startup_idea},
Market Analysis:...., 
Suggest the most essential MVP features that can be built 
in under 3 months with a small team. Focus on core value 
delivery only."""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
            )
        
        return response.text
    

    except requests.exceptions.HTTPError :
        return f"HTTP error occurred" # e.g., 404 Not Found
        
    except requests.exceptions.ConnectionError:
        return "Connection error: Check your internet or server URL."
    
    except requests.exceptions.Timeout:
        return  "Timeout error: The server took too long to respond."
    
    except requests.exceptions.RequestException :
        return f"An unexpected error occurred"

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"
        


def recommend_tech_stack(startup_idea:str,) -> str:

    full_prompt= f"""You are an expert Chief Technology Officer (CTO) and software architect.
Based on this startup idea: {startup_idea},
Recommend a lean tech stack that allows a small team to launch in under 3 months.
Focus entirely on speed to market, ease of development, scalability, and minimal maintenance overhead.
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
            )
        
        return response.text
    

    except requests.exceptions.HTTPError :
        return f"HTTP error occurred" # e.g., 404 Not Found
        
    except requests.exceptions.ConnectionError:
        return "Connection error: Check your internet or server URL."
    
    except requests.exceptions.Timeout:
        return  "Timeout error: The server took too long to respond."
    
    except requests.exceptions.RequestException :
        return f"An unexpected error occurred"

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"


def risk_analysis(idea:str) -> str:

    full_prompt = f"""You are a startup risk management expert and venture analyst.
Based on this startup idea: {idea},  MVP features and  market analysis,
Conduct a rigorous risk analysis for launching this product. Focus on identifying fatal flaws and hidden bottlenecks,
and provide clear, actionable mitigation strategies for a small team.
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
            )
        
        return response.text
    

    except requests.exceptions.HTTPError :
        return f"HTTP error occurred" # e.g., 404 Not Found
        
    except requests.exceptions.ConnectionError:
        return "Connection error: Check your internet or server URL."
    
    except requests.exceptions.Timeout:
        return  "Timeout error: The server took too long to respond."
    
    except requests.exceptions.RequestException :
        return f"An unexpected error occurred"

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"


# A new tool called `search_documents` that calls `query_rag()`
def search_documents(user_input: str):
    print("calling search_document tool...")
    search_response = query_rag(user_input)
    
    if not search_response:
        return "No data found. The file does not exist. Please check the file connection."
    
    return search_response