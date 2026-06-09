# ============================================================
#  tools.py — Tool Definitions for Startup Analysis Agent
# ============================================================
#
#  What this file does:
#  Defines all callable tools used by the startup analysis agent.
#  Each tool wraps one external API call (Gemini or Tavily) and
#  returns a structured string/dict result back to the orchestrator.
#
#  What this file does NOT handle:
#  Does not orchestrate tool call order — that belongs to the agent.
#  Does not combine tool outputs into a final report.
#  Does not manage conversation history or agent state.
#
#  Functions:
#  - summarize_text()         → parallel-summarizes web content via Gemini
#  - analyze_market()         → searches market data for a startup idea via Tavily
#  - search_knowledge_base()  → deep Tavily search to ground LLM with sources
#  - suggest_mvp()            → asks Gemini to recommend core MVP features
#  - recommend_tech_stack()   → asks Gemini for a lean, fast-to-ship tech stack
#  - risk_analysis()          → asks Gemini to identify fatal flaws and risks
#  - search_documents()       → queries local RAG vector store for uploaded PDFs
#
#  Used by:
#  - agent.py → calls these tools based on LLM tool-use decisions
#
#  Pipeline Flow:
#  user_input → summarize_text() → [analyze_market(), suggest_mvp(),
#               recommend_tech_stack(), risk_analysis()] → final LLM report
#
#  Imports from:
#  - rag.py → query_rag(), embed_and_store(), ingest_pdf()
# ============================================================

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
    ingest_pdf,
)


# ── CLIENT SETUP ──────────────────────────────────────────────
# Clients initialized once at module level — reused across all tool calls
# Avoids re-authenticating on every function call

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Explicit key passed to avoid ambiguity with GOOGLE_API_KEY env var
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

tavily_client = TavilyClient(TAVILY_API_KEY)


# ── SUMMARIZATION ─────────────────────────────────────────────

def summarize_text(message: dict) -> str:
    """Summarizes multiple web pages in parallel using Gemini.

    Parameters:
        message (dict) → URL-keyed dict where each value is [title, content].
                         Produced by analyze_market() or search_knowledge_base().

    Returns:
        str → concatenated block of Title / Summary / URL for each page,
              or an error string if the API call fails.

    Flow:
        1. Spin up a ThreadPoolExecutor — one Gemini call submitted per URL
        2. Build a prompt per URL using the page content from message[url][1]
        3. Map each Future back to its URL using a future → url dict
        4. As futures complete, collect and concatenate Title + Summary + URL
        5. Return the full concatenated response string

    Concepts used:
        - ThreadPoolExecutor  → runs all Gemini calls concurrently instead of
                                sequentially, cutting total wait time significantly
        - as_completed()      → yields futures as they finish, not in submission
                                order — faster response from quicker pages first
        - future dict (future→url) → standard Fan-Out pattern; lets us recover
                                     which URL each future belongs to after completion
    """

    try:
        with ThreadPoolExecutor() as executor:

            # Step 1: Submit one Gemini call per URL, map future → url
            future = {}
            for url in message:
                full_prompt = f"""You are a professional summarizer.
Please read the following text and provide a concise and clear summary.
---

Text to summarize: {message[url][1]} ---

Summary:
"""
                future[executor.submit(
                    gemini_client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=full_prompt
                )] = url

            # Step 2: Collect results as each future completes
            response = ""
            for complete_future in as_completed(future):
                url = future[complete_future]
                response += (
                    f"Title: {message[url][0]}\n"
                    f"Summary: {complete_future.result(timeout=60).text}\n"
                    f"URL: {url}\n\n"
                )

        # Step 3: Return full concatenated summary block
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


# ── TAVILY TOOLS ──────────────────────────────────────────────

def analyze_market(startup_idea: str) -> dict:
    """Searches the web for market data related to a startup idea.

    Parameters:
        startup_idea (str) → raw startup concept or one-liner from the user

    Returns:
        dict → URL-keyed dict where each value is [title, content_string],
               ready to be passed into summarize_text().
               Returns an error string on failure.

    Flow:
        1. Run a basic-depth Tavily search using startup_idea as the query
        2. Loop through results and build a url → [title, content] dict
        3. Return the dict for downstream summarization

    Concepts used:
        - search_depth="basic"  → faster, lower-cost search; sufficient for
                                  market overview (not deep fact verification)
        - exclude_domains       → filters social media noise that Tavily often
                                  surfaces for business queries
    """

    try:
        # Step 1: Tavily web search — basic depth for speed
        response = tavily_client.search(
            query=startup_idea,
            include_answer="advanced",
            search_depth="basic",
            country="india",
            exclude_domains=["facebook.com", "x.com", "instagram.com"],
        )

        # Step 2: Reshape results into url → [title, content] format
        message = {}
        for result in response["results"]:
            content = "\nResult :\nContent: " + result["content"]
            message[result["url"]] = [result["title"], content]

        # Step 3: Return structured dict for summarize_text()
        return message

    except requests.exceptions.HTTPError:
        return "HTTP error occurred"

    except requests.exceptions.ConnectionError:
        return "Connection error: Check your internet or server URL."

    except requests.exceptions.Timeout:
        return "Timeout error: The server took too long to respond."

    except requests.exceptions.RequestException:
        return "An unexpected request error occurred."

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"


def search_knowledge_base(query: str) -> dict:
    """Deep Tavily search to retrieve grounding sources and reduce hallucination.

    Parameters:
        query (str) → specific claim or topic the agent needs to verify or expand

    Returns:
        dict → URL-keyed dict where each value is [title, content_string],
               same structure as analyze_market() — compatible with summarize_text().
               Returns an error string on failure.

    Flow:
        1. Run an advanced-depth Tavily search on the query
        2. Loop through results and build url → [title, content] dict
        3. Return the dict

    Concepts used:
        - search_depth="advanced" → slower but more thorough than analyze_market();
                                    used here because accuracy matters more than speed
                                    when grounding LLM claims with real sources
    Why same return shape as analyze_market():
        Both feed into summarize_text() — consistent shape avoids branching logic
        in the orchestrator.
    """

    try:
        # Step 1: Deep Tavily search for factual grounding
        response = tavily_client.search(
            query=query,
            include_answer="advanced",
            search_depth="advanced",
            country="india",
            exclude_domains=["facebook.com", "x.com", "instagram.com"],
        )

        # Step 2: Reshape into url → [title, content] format
        message = {}
        for result in response["results"]:
            content = "\nResult :\nContent: " + result["content"]
            message[result["url"]] = [result["title"], content]

        # Step 3: Return structured dict
        return message

    except requests.exceptions.HTTPError:
        return "HTTP error occurred"

    except requests.exceptions.ConnectionError:
        return "Connection error: Check your internet or server URL."

    except requests.exceptions.Timeout:
        return "Timeout error: The server took too long to respond."

    except requests.exceptions.RequestException:
        return "An unexpected request error occurred."

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"


# ── GEMINI LLM TOOLS ──────────────────────────────────────────

def suggest_mvp(startup_idea: str, market_context: str = "") -> str:
    """Asks Gemini to recommend the most essential MVP features for a startup.

    Parameters:
        startup_idea   (str) → raw startup concept from the user
        market_context (str) → summarized market data from summarize_text(analyze_market()).
                               Defaults to empty string — function works standalone
                               but produces grounded output when context is provided.

    Returns:
        str → Gemini's plain-text MVP recommendation,
              or an error string on failure.

    Flow:
        1. Build advisor prompt — inject market_context if available, else note its absence
        2. Call Gemini with the prompt
        3. Return the response text

    Why default empty string for market_context:
        Allows the function to be called standalone during testing or early pipeline
        stages, without requiring the full Fan-Out to have completed first.
        The orchestrator passes real context when available.
    """

    # Step 1: Build advisor prompt — ground with market data if available
    market_section = market_context if market_context else "No market data available."
    full_prompt = f"""You are a startup advisor. Based on this idea: {startup_idea},

Market Analysis:
{market_section}

Suggest the most essential MVP features that can be built
in under 3 months with a small team. Focus on core value delivery only."""

    try:
        # Step 2: Single Gemini call — no parallelism needed here
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )

        # Step 3: Return raw text response
        return response.text

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
    


def recommend_tech_stack(startup_idea: str, market_context: str = "") -> str:
    """Asks Gemini to recommend a lean tech stack for fast time-to-market.

    Parameters:
        startup_idea   (str) → raw startup concept from the user
        market_context (str) → summarized market data from summarize_text(analyze_market()).
                               Defaults to empty string — function works standalone
                               but produces grounded output when context is provided.

    Returns:
        str → Gemini's plain-text tech stack recommendation,
              or an error string on failure.

    Flow:
        1. Build a CTO-persona prompt — inject market_context if available
        2. Call Gemini with the prompt
        3. Return the response text

    Why CTO persona in prompt:
        Role-prompting nudges the model toward opinionated, practical choices
        rather than exhaustive lists — more useful for a small team deciding fast.

    Why market_context matters here:
        Market data reveals what competitors are using and what the target users
        expect — both influence stack decisions beyond just the idea itself.
    """

    # Step 1: Build CTO-persona prompt — ground with market data if available
    market_section = market_context if market_context else "No market data available."
    full_prompt = f"""You are an expert Chief Technology Officer (CTO) and software architect.
Based on this startup idea: {startup_idea},

Market Analysis:
{market_section}

Recommend a lean tech stack that allows a small team to launch in under 3 months.
Focus entirely on speed to market, ease of development, scalability, and minimal maintenance overhead.
"""

    try:
        # Step 2: Gemini call
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )

        # Step 3: Return recommendation text
        return response.text

    except requests.exceptions.HTTPError:
        return "HTTP error occurred"

    except requests.exceptions.ConnectionError:
        return "Connection error: Check your internet or server URL."

    except requests.exceptions.Timeout:
        return "Timeout error: The server took too long to respond."

    except requests.exceptions.RequestException:
        return "An unexpected request error occurred."

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"



def risk_analysis(idea: str, market_context: str = "", mvp_context: str = "") -> str:
    """Asks Gemini to identify fatal flaws and risks for a startup idea.

    Parameters:
        idea           (str) → raw startup concept from the user
        market_context (str) → summarized market data from summarize_text(analyze_market()).
                               Defaults to empty string — function works standalone
                               but produces grounded output when context is provided.
        mvp_context    (str) → suggest_mvp() output from Stage 3.
                               Defaults to empty string — when provided, risk analysis
                               targets the specific MVP recommended, not a generic version.

    Returns:
        str → Gemini's plain-text risk report with mitigation strategies,
              or an error string on failure.

    Flow:
        1. Build venture-analyst prompt — inject market_context and mvp_context if available
        2. Call Gemini with the prompt
        3. Return the response text

    Why "fatal flaws" framing in prompt:
        Generic risk prompts return obvious answers. Asking specifically for
        fatal flaws forces the model to prioritise high-severity risks over
        boilerplate concerns like "competition exists".

    Why mvp_context matters:
        Risks are MVP-specific — a risk relevant to a marketplace MVP is different
        from one relevant to a SaaS MVP. Without mvp_context, Gemini analyses
        risks against a generic version of the idea, not the actual build plan.
    """

    # Step 1: Build risk analyst prompt — ground with market and MVP data if available
    market_section = market_context if market_context else "No market data available."
    mvp_section    = mvp_context    if mvp_context    else "No MVP plan available."
    full_prompt = f"""You are a startup risk management expert and venture analyst.
Based on this startup idea: {idea},

Market Analysis:
{market_section}

MVP Plan:
{mvp_section}

Conduct a rigorous risk analysis for launching this product. Focus on identifying fatal flaws and hidden bottlenecks,
and provide clear, actionable mitigation strategies for a small team.
"""

    try:
        # Step 2: Gemini call
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )

        # Step 3: Return risk report text
        return response.text

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


# ── RAG TOOL ──────────────────────────────────────────────────

def search_documents(user_input: str) -> str:
    """Queries the local RAG vector store for relevant chunks from uploaded PDFs.

    Parameters:
        user_input (str) → natural language query from the user or agent

    Returns:
        str → matched document chunks from the vector store,
              or a not-found message if no results are returned.

    Flow:
        1. Call query_rag() with the user input
        2. Check if any results were returned
        3. Return results, or a fallback message if empty

    Concepts used:
        - RAG (Retrieval-Augmented Generation) → retrieves grounding context
          from user-uploaded documents before passing to LLM, reducing hallucination
          on domain-specific content that Gemini hasn't seen

    Why separate from search_knowledge_base():
        This queries local PDFs the user uploaded — private, offline context.
        search_knowledge_base() queries the live web. They serve different
        grounding purposes and should not be merged.
    """

    print("Calling search_documents tool...")

    # Step 1: Query the local RAG vector store
    search_response = query_rag(user_input)

    # Step 2: Guard against empty results — RAG can return None or []
    if not search_response:
        return "No data found. The file does not exist. Please check the file connection."

    # Step 3: Return matched chunks to the agent
    return search_response