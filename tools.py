# tools.py
from google import genai
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import requests 

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


def summarize_text(text: str) -> str:
    """
    Basic placeholder summarizer.
    """
        
    if len(text) <= 200:
        return text

    full_prompt = f"""You are a professional summarizer. 
Please read the following text and provide a concise and clear summary.
Also keep the mentioned source of the information you gathered for future verification and confident response Properly.
After the summary, analyze the response to ensure it accurately matches the sources, does not cause hallucination, and maintains high quality. --- 

Text to summarize: {text} --- 

Summary:
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


def analyze_market(startup_idea: str) -> str:
    """
    Analyze market potential for a startup idea.
    """
    try :
        response = tavily_client.search(
            query=startup_idea,
            search_depth="basic"
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


def search_knowledge_base(query: str) -> str:
    """
    Simulated knowledge base search.
    """

    new_query =  f"""
Knowledge Base Results for Project :
- Found related insights for '{query}'
- Similar startup trends detected
- Moderate market opportunity identified
"""
    try :
        response = tavily_client.search(
                query = new_query,
                search_depth = "basic"
            )
        
        message = """"""
        for result in response["results"]:
                message += "\nResult :" 
                message += "\nTitle: "+ result["title"]
                message += "\nContent: " + result["content"]
                message += "\nURL:"+result["url"]
        
        return f"""Search Knowledge Base Result :
    {message}
    """
    
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


def suggest_mvp(startup_idea: str, market_analysis:str) -> str:

    full_prompt = f"""You are a startup advisor. Based on this idea: {startup_idea},
Market Analysis: {market_analysis}, 
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
        


def recommend_tech_stack(startup_idea:str, mvp_suggestions:str) -> str:

    full_prompt= f"""You are an expert Chief Technology Officer (CTO) and software architect.
Based on this startup idea: {startup_idea} and these specific MVP suggestions: {mvp_suggestions},
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


def risk_analysis(idea:str, mvp_suggestions:str, market_analysis:str) -> str:

    full_prompt = f"""You are a startup risk management expert and venture analyst.
Based on this startup idea: {idea}, these MVP features: {mvp_suggestions}, and this market analysis: {market_analysis},
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
