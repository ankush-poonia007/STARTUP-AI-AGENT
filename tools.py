# tools.py
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import requests 

"""

user_input
    ↓
summarize_text()
    ↓
    ├──→ analyze_market() ──→ search_knowledge_base()
    │                                   ↓
    ├──→ suggest_mvp()              [sources for
    │                               hallucination
    ├──→ recommend_tech_stack()      removal]
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

7. Final Homework Before Next Session: 
    1. Build — suggest_mvp() yourself using summarized text + prompt template
    2. Research — asyncio for parallel execution
    3. Write — PROGRESS.md in your project from memory


"""

load_dotenv()


def search_knowledge_base(query: str) -> str:
    """
    Simulated knowledge base search.
    """

    return f"""
Knowledge Base Results:
- Found related insights for '{query}'
- Similar startup trends detected
- Moderate market opportunity identified
"""


def summarize_text(text: str) -> str:
    """
    Basic placeholder summarizer.
    """

    if len(text) <= 200:
        return text

    return text[:200] + "..."



def analyze_market(startup_idea: str) -> str:
    """
    Analyze market potential for a startup idea.
    """
    try :
        TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        
        # To install: pip install tavily-python
        client = TavilyClient(TAVILY_API_KEY)
        response = client.search(
            query=startup_idea,
            search_depth="basic"
        )
        
        message = """"""
        for result in response["results"]:
            message += "\nResult :" 
            message += "n\Title: "+ result["title"]
            message += "\nContent: " + result["content"]
            message += "\nURL:"+result["url"]
            
            
        return f"""Market Analysis Results:
    {message}"""
    
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

    return """
Suggested MVP Features:
- User authentication
- Dashboard
- Subscription system
- Notifications
- Analytics panel
"""


def recommend_tech_stack() -> str:

    return """
Recommended Tech Stack:
- Frontend: React
- Backend: FastAPI
- Database: PostgreSQL
- AI Layer: Gemini API
"""


def risk_analysis() -> str:

    return """
Possible Risks:
- User acquisition cost
- Competition from established startups
- Scaling infrastructure
- Retention challenges
"""
