# ============================================================
#  tools.py — Tool Definitions for BizRadar AI Agent
# ============================================================
#
#  What this file does:
#  Defines all callable tools used by the BizRadar AI agent.
#  Each tool wraps one external API call (Gemini or Tavily) or
#  one internal pipeline call (RAG), and returns a structured
#  string result back to the orchestrator in orchestrator.py.
#
#  What this file does NOT handle:
#  Does not orchestrate tool call order or stage gating — that belongs to
#  orchestrator.py (see validate_stage_tools()).
#  Does not combine tool outputs into a final report.
#  Does not manage conversation history or agent state.
#
#  Functions (LLM-callable tools):
#  - analyze_market()         → Stage 1: Tavily web search → self-summarizes → returns str
#  - search_knowledge_base()  → Stage 1: deep Tavily search → self-summarizes → returns str
#  - suggest_mvp()            → Stage 2: Gemini MVP recommendation with market context
#  - recommend_tech_stack()   → Stage 2: Gemini tech stack recommendation with market context
#  - risk_analysis()          → Stage 3: Gemini risk report with market + MVP context
#  - search_documents()       → Stage 4: queries local RAG vector store for a specific
#                               uploaded PDF, scoped by file_name. Called on-demand only
#                               after Stage 3, never during Stages 1-3.
#
#  Internal functions (NOT LLM-callable):
#  - summarize_text()         → called inside analyze_market() and search_knowledge_base()
#                               before returning — never exposed to the LLM directly
#
#  Used by:
#  - orchestrator.py → calls these tools based on LLM tool-use decisions, after
#                      validate_stage_tools() confirms each call belongs to its stage
#
#  Pipeline Flow (3+1 stages):
#  Stage 1: analyze_market() + search_knowledge_base() in parallel
#           (each self-summarizes before returning a plain str)
#  Stage 2: suggest_mvp() + recommend_tech_stack() in parallel
#           (both receive market_context from Stage 1)
#  Stage 3: risk_analysis() alone
#           (receives market_context + mvp_context from Stage 2)
#  Stage 4: search_documents() alone, on-demand, only after Stage 3
#           (triggered only when user references an uploaded document;
#            file_name scopes retrieval to one specific PDF — Phase 4
#            multi-document isolation via ChromaDB where filtering)
#
#  Error string conventions (matched by prompts.py Rules 12 and 13):
#  Stage 1 failure → "Summarization unavailable — service error, no data retrieved."
#  Stage 2/3 failure → "<Tool name> unavailable — service error, no data retrieved."
#  Both Stage 1 tools fail → Rule 12 footer triggered in final report
#  Stage 2/3 tool fails → Rule 13 per-section note, no footer
#
#  Phase 4 note on multiple Gemini API keys:
#  Each Gemini-backed tool below uses its own dedicated client / API key
#  (gemini_analyze_client, gemini_search_knowledge_client, gemini_mvp_client,
#  gemini_tech_stack_client, gemini_risk_client). This spreads load across
#  separate quotas rather than funneling every Gemini call through one key —
#  reduces (but does not eliminate) the chance of a single key's free-tier
#  RPM/TPD limit blocking the entire pipeline in one run.
#
#  Imports from:
#  - rag.py → query_rag()
# ============================================================

import time
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.api_core import exceptions
from google import genai
from tavily import TavilyClient
from dotenv import load_dotenv

from src.rag.rag import query_rag


# ── CLIENT SETUP ──────────────────────────────────────────────
# Clients initialized once at module level — reused across all tool calls.
# Avoids re-authenticating on every function call.
# load_dotenv() must run before os.getenv() to populate the environment.

load_dotenv()

TAVILY_API_KEY    = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY_1  = os.getenv("GEMINI_API_KEY_1")
GEMINI_API_KEY_2  = os.getenv("GEMINI_API_KEY_2")
GEMINI_API_KEY_3  = os.getenv("GEMINI_API_KEY_3")
GEMINI_API_KEY_4  = os.getenv("GEMINI_API_KEY_4")
GEMINI_API_KEY_5  = os.getenv("GEMINI_API_KEY_5")
GEMINI_API_KEY_6  = os.getenv("GEMINI_API_KEY_6")
GEMINI_API_KEY_7  = os.getenv("GEMINI_API_KEY_7")
GEMINI_API_KEY_8  = os.getenv("GEMINI_API_KEY_8")
GEMINI_API_KEY_9  = os.getenv("GEMINI_API_KEY_9")
GEMINI_API_KEY_10 = os.getenv("GEMINI_API_KEY_10")

# Explicit api_key passed to avoid ambiguity with GOOGLE_API_KEY env var.
# Each tool gets its own dedicated client/key — see file header note above.

# analyze_market() -> summarize_text()
gemini_analyze_client = genai.Client(api_key=GEMINI_API_KEY_7)

# search_knowledge_base() -> summarize_text()
gemini_search_knowledge_client = genai.Client(api_key=GEMINI_API_KEY_9)

# suggest_mvp()
gemini_mvp_client = genai.Client(api_key=GEMINI_API_KEY_3)

# recommend_tech_stack()
gemini_tech_stack_client = genai.Client(api_key=GEMINI_API_KEY_4)

# risk_analysis()
gemini_risk_client = genai.Client(api_key=GEMINI_API_KEY_5)

tavily_client = TavilyClient(TAVILY_API_KEY)


# ── INTERNAL SUMMARIZATION ────────────────────────────────────
# NOT an LLM-callable tool. Called internally by analyze_market()
# and search_knowledge_base() before each returns its result.
# Not present in tools_description.py — the LLM never sees this function.

def summarize_text(message: dict, client) -> str:
    """Summarizes multiple web pages in parallel using Gemini. Internal use only.

    Called by analyze_market() and search_knowledge_base() to convert raw
    Tavily search results into a clean summarized string before returning
    to the agent. Not exposed to the LLM as a callable tool.

    Parameters:
        message (dict) → URL-keyed dict where each value is [title, content_string].
                         Produced by analyze_market() or search_knowledge_base()
                         before calling this function.
        client  (genai.Client) → the caller's dedicated Gemini client — passed in
                         rather than using a single shared client, so analyze_market()
                         and search_knowledge_base() draw from separate API keys/quotas
                         even though they share this one summarization function.

    Returns:
        str → concatenated block of Title / Summary / URL for each page.
              Returns "Summarization unavailable — service error, no data retrieved."
              if ALL URLs fail. Individual URL failures are skipped silently.

    Why parallel execution via ThreadPoolExecutor:
        Each URL requires a separate Gemini API call. Running them sequentially
        multiplies latency by the number of results. Parallel execution cuts
        total wait time to the duration of the slowest single call.

    Why as_completed() over executor.map():
        as_completed() yields results as each future finishes — faster overall
        when pages have different response times. A fast page does not wait
        for a slow one. executor.map() blocks until all finish and returns in order.

    Why individual URL failures are skipped (not placeholder text):
        Appending "Summary: [unavailable]" would pass placeholder text as real
        market data to the LLM. Skipping entirely means market_context only ever
        contains real summarized content — no hallucination risk from placeholders.

    Why time.sleep(25) between Fan-Out submissions:
        analyze_market() and search_knowledge_base() run in parallel in Stage 1,
        each firing up to 3 Gemini calls via summarize_text(). Without throttling,
        up to 6 simultaneous Gemini calls exceed the free tier 5 RPM limit,
        causing cascading 429 failures into Stages 2 and 3.
        sleep(25) between submissions reduces combined rate to ~6/min — partial
        mitigation. A full fix (shared semaphore across all Gemini callers) is
        logged as a Phase 4 backlog item — see LEARNING_LOG.md.

    Why this is internal and not LLM-callable:
        Passing raw Tavily result dicts through the LLM for JSON reconstruction
        caused 400 schema validation failures due to special characters in real
        web content. Moving summarization internal eliminates this fragility entirely.
    """

    try:

        def _call_gemini_with_retry(prompt: str, max_retries: int = 3):
            """Retries Gemini generate_content on 429/503 with exponential backoff.

            Parameters:
                prompt      (str) → full prompt string to send to Gemini
                max_retries (int) → maximum retry attempts. Default 3.

            Returns:
                Gemini response object on success. Raises on final attempt failure.
            """
            for attempt in range(max_retries):
                try:
                    return client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                except exceptions.ResourceExhausted:
                    if attempt < max_retries - 1:
                        wait = 15 * (attempt + 1)  # 15s, 30s, 45s
                        print(f"   ⏳ Rate limited (429) — retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait)
                    else:
                        raise

                except exceptions.ServiceUnavailable:
                    if attempt < max_retries - 1:
                        wait = 5 * (attempt + 1)  # shorter — 503 is transient
                        print(f"   ⏳ Gemini unavailable (503) — retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait)
                    else:
                        raise

        with ThreadPoolExecutor() as executor:

            # Fan-Out — submit one Gemini call per URL, map future → url.
            # time.sleep(25) between submissions throttles RPM to stay within
            # free tier limits when both Stage 1 tools run in parallel.
            future = {}
            for url in message:
                full_prompt = f"""You are a professional summarizer.
Please read the following text and provide a concise and clear summary.
---
Text to summarize: {message[url][1]}
---
Summary:
"""
                future[executor.submit(_call_gemini_with_retry, full_prompt)] = url
                time.sleep(25)

            # Fan-In — collect results as each future completes.
            # Individual URL failures are skipped — only real summaries appended.
            # Failed futures never contribute placeholder text to market_context.
            response = ""
            for complete_future in as_completed(future):
                url = future[complete_future]
                try:
                    result = complete_future.result(timeout=60)
                    response += (
                        f"Title: {message[url][0]}\n"
                        f"Summary: {result.text}\n"
                        f"URL: {url}\n\n"
                    )
                except Exception:
                    # Skip — retries already exhausted inside _call_gemini_with_retry.
                    # No fallback text — LLM must not treat placeholders as real data.
                    continue

        # All URLs failed — response stayed empty.
        # Distinct error string matched by context guard in analyze_market()
        # and search_knowledge_base() — triggers Rule 12 handling if both fail.
        if not response:
            return "Summarization unavailable — service error, no data retrieved."

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

def analyze_market(startup_idea: str) -> str:
    """Searches the web for market data and returns a summarized analysis string.

    Stage 1 tool — runs in parallel with search_knowledge_base().
    Performs a basic-depth Tavily search for market size, trends, and demand,
    then internally summarizes results via summarize_text() before returning.
    The returned string is passed as part of market_context to Stage 2 tools.

    Parameters:
        startup_idea (str) → raw startup concept or one-liner from the user

    Returns:
        str → summarized market analysis string ready for downstream tools.
              Returns "Summarization unavailable — service error, no data retrieved."
              if summarize_text() fails entirely — matched by Rule 12 in prompts.py.

    Why search_depth="basic":
        Faster and lower-cost than advanced depth. Sufficient for market
        overview — deep fact verification is handled by search_knowledge_base().

    Why self-summarize before returning:
        Passing raw Tavily dicts through the LLM for JSON reconstruction caused
        400 schema validation failures. Summarizing internally returns
        a clean string the LLM can pass directly as market_context.

    Why context guard before returning:
        If summarize_text() returns an error string, passing it as market_context
        would cause the LLM to treat error text as real market research data,
        producing hallucinated reports with false confidence.
    """

    try:
        # Tavily basic search — fast market overview
        response = tavily_client.search(
            query=startup_idea,
            include_answer="advanced",
            search_depth="basic",
            country="india",
            exclude_domains=["facebook.com", "x.com", "instagram.com"],
            max_results=3
        )

        # Reshape results into url → [title, content] dict for summarize_text()
        message = {}
        for result in response["results"]:
            content = result["content"][:300]
            content = content.replace("\xa0", " ").replace("\n", " ").replace('"', "'").replace("\\", "")
            message[result["url"]] = [result["title"], "\nResult:\nContent: " + content]

        # Summarize internally — returns clean str, not raw dict
        result = summarize_text(message, gemini_analyze_client)

        # Context guard — prevents error strings from reaching downstream tools as market data.
        # Covers all known error prefixes from summarize_text() and Gemini exception handlers.
        if any(result.startswith(prefix) for prefix in [
            "Summarization unavailable",
            "An unexpected error",
            "Rate Limited",
            "Auth Error",
            "Generic API Error",
            "Configuration Error"
        ]):
            return "Summarization unavailable — service error, no data retrieved."

        return result

    except requests.exceptions.HTTPError:
        return "Summarization unavailable — service error, no data retrieved."

    except requests.exceptions.ConnectionError:
        return "Summarization unavailable — service error, no data retrieved."

    except requests.exceptions.Timeout:
        return "Summarization unavailable — service error, no data retrieved."

    except requests.exceptions.RequestException:
        return "Summarization unavailable — service error, no data retrieved."

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception:
        return "Summarization unavailable — service error, no data retrieved."


def search_knowledge_base(query: str) -> str:
    """Deep Tavily search to retrieve competitor and industry sources.

    Stage 1 tool — runs in parallel with analyze_market().
    Performs a Tavily search for competitor data and industry insights,
    then internally summarizes results via summarize_text() before returning.
    The returned string is passed as part of market_context to Stage 2 tools
    alongside analyze_market() output.

    Parameters:
        query (str) → specific claim or topic the agent needs to verify or expand

    Returns:
        str → summarized competitor and industry analysis string.
              Returns "Summarization unavailable — service error, no data retrieved."
              if summarize_text() fails entirely — matched by Rule 12 in prompts.py.

    Why search_depth="basic":
        Advanced depth is slower and costlier — kept basic to stay within
        Groq TPM limits during parallel Stage 1 execution.

    Why same return shape as analyze_market():
        Both feed into market_context for Stage 2 — consistent str return
        avoids branching logic in the orchestrator.

    Why same context guard as analyze_market():
        Both Stage 1 tools feed market_context. If either returns an error string
        and it reaches the LLM, the LLM treats it as real competitor data.
        Rule 12 in prompts.py handles the case where both return the unavailable string.
    """

    try:
        # Tavily search — competitor and industry grounding
        response = tavily_client.search(
            query=query,
            include_answer="advanced",
            search_depth="basic",
            country="india",
            exclude_domains=["facebook.com", "x.com", "instagram.com"],
            max_results=3
        )

        # Reshape into url → [title, content] dict for summarize_text()
        message = {}
        for result in response["results"]:
            content = result["content"][:300]
            content = content.replace("\xa0", " ").replace("\n", " ").replace('"', "'").replace("\\", "")
            message[result["url"]] = [result["title"], "\nResult:\nContent: " + content]

        # Summarize internally — returns clean str, not raw dict
        result = summarize_text(message, gemini_search_knowledge_client)

        # Context guard — same logic as analyze_market().
        # Covers all known error prefixes from summarize_text() and Gemini exception handlers.
        if any(result.startswith(prefix) for prefix in [
            "Summarization unavailable",
            "An unexpected error",
            "Rate Limited",
            "Auth Error",
            "Generic API Error",
            "Configuration Error"
        ]):
            return "Summarization unavailable — service error, no data retrieved."

        return result

    except requests.exceptions.HTTPError:
        return "Summarization unavailable — service error, no data retrieved."

    except requests.exceptions.ConnectionError:
        return "Summarization unavailable — service error, no data retrieved."

    except requests.exceptions.Timeout:
        return "Summarization unavailable — service error, no data retrieved."

    except requests.exceptions.RequestException:
        return "Summarization unavailable — service error, no data retrieved."

    except ValueError as e:
        return f"Configuration Error: {e}"

    except Exception:
        return "Summarization unavailable — service error, no data retrieved."


# ── GEMINI LLM TOOLS ──────────────────────────────────────────

def suggest_mvp(startup_idea: str, market_context: str = "") -> str:
    """Asks Gemini to recommend the most essential MVP features for a startup.

    Stage 2 tool — runs in parallel with recommend_tech_stack().
    Receives market_context from combined Stage 1 outputs to produce
    grounded, market-aware MVP recommendations rather than generic ones.
    Output is passed as mvp_context to risk_analysis() in Stage 3.

    Parameters:
        startup_idea   (str) → raw startup concept from the user
        market_context (str) → combined summarized output from Stage 1 tools.
                               Defaults to empty string — function works standalone
                               but produces grounded output when context is provided.

    Returns:
        str → Gemini's plain-text MVP recommendation on success.
              Returns "MVP suggestion unavailable — service error, no data retrieved."
              on failure — matched by Rule 13 in prompts.py for per-section note.

    Why default empty string for market_context:
        Allows standalone testing without requiring the full Stage 1 pipeline
        to have completed first. The orchestrator passes real context in production
        (and forcibly overwrites this argument before execution — see
        orchestrator.py's run() docstring).

    Why startup advisor persona in prompt:
        Role-prompting nudges the model toward focused, 3-month-buildable
        recommendations rather than exhaustive feature lists.
    """

    # Build advisor prompt — inject market data if available
    market_section = market_context if market_context else "No market data available."
    full_prompt = f"""You are a startup advisor. Based on this idea: {startup_idea},

Market Analysis:
{market_section}

Suggest the most essential MVP features that can be built
in under 3 months with a small team. Focus on core value delivery only."""

    for attempt in range(3):
        try:
            response = gemini_mvp_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )
            break

        except exceptions.ResourceExhausted:
            if attempt < 2:
                wait = 15 * (attempt + 1)
                print(f"   ⏳ Rate limited (429) — retrying in {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                return "MVP suggestion unavailable — service error, no data retrieved."

        except exceptions.ServiceUnavailable:
            if attempt < 2:
                wait = 5 * (attempt + 1)
                print(f"   ⏳ Gemini unavailable (503) — retrying in {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                return "MVP suggestion unavailable — service error, no data retrieved."

        except exceptions.Unauthenticated as e:
            return f"Auth Error (401): Check system environment API keys. Details: {e}"

        except exceptions.GoogleAPICallError as e:
            return f"Generic API Error: {e.code} - {e.message}"

        except ValueError as e:
            return f"Configuration Error: {e}"

        except Exception:
            return "MVP suggestion unavailable — service error, no data retrieved."

    return response.text


def recommend_tech_stack(startup_idea: str, market_context: str = "") -> str:
    """Asks Gemini to recommend a lean tech stack for fast time-to-market.

    Stage 2 tool — runs in parallel with suggest_mvp().
    Receives market_context from combined Stage 1 outputs to produce
    stack recommendations informed by what competitors use and what
    the target market expects.

    Parameters:
        startup_idea   (str) → raw startup concept from the user
        market_context (str) → combined summarized output from Stage 1 tools.
                               Defaults to empty string — function works standalone
                               but produces grounded output when context is provided.

    Returns:
        str → Gemini's plain-text tech stack recommendation on success.
              Returns "Tech stack recommendation unavailable — service error, no data retrieved."
              on failure — matched by Rule 13 in prompts.py for per-section note.

    Why CTO persona in prompt:
        Role-prompting nudges the model toward opinionated, practical choices
        rather than exhaustive lists — more useful for a small team deciding fast.

    Why market_context matters here:
        Market data reveals what competitors are using and what target users
        expect — both influence stack decisions beyond just the idea itself.
    """

    # Build CTO-persona prompt — inject market data if available
    market_section = market_context if market_context else "No market data available."
    full_prompt = f"""You are an expert Chief Technology Officer (CTO) and software architect.
Based on this startup idea: {startup_idea},

Market Analysis:
{market_section}

Recommend a lean tech stack that allows a small team to launch in under 3 months.
Focus entirely on speed to market, ease of development, scalability, and minimal maintenance overhead.
"""

    for attempt in range(3):
        try:
            response = gemini_tech_stack_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )
            break

        except exceptions.ResourceExhausted:
            if attempt < 2:
                wait = 15 * (attempt + 1)
                print(f"   ⏳ Rate limited (429) — retrying in {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                return "Tech stack recommendation unavailable — service error, no data retrieved."

        except exceptions.ServiceUnavailable:
            if attempt < 2:
                wait = 5 * (attempt + 1)
                print(f"   ⏳ Gemini unavailable (503) — retrying in {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                return "Tech stack recommendation unavailable — service error, no data retrieved."

        except exceptions.Unauthenticated as e:
            return f"Auth Error (401): Check system environment API keys. Details: {e}"

        except exceptions.GoogleAPICallError as e:
            return f"Generic API Error: {e.code} - {e.message}"

        except ValueError as e:
            return f"Configuration Error: {e}"

        except Exception:
            return "Tech stack recommendation unavailable — service error, no data retrieved."

    return response.text


def risk_analysis(startup_idea: str, market_context: str = "", mvp_context: str = "") -> str:
    """Asks Gemini to identify fatal flaws and risks for a startup idea.

    Stage 3 tool — runs alone after Stage 2 completes.
    Receives both market_context from Stage 1 and mvp_context from Stage 2
    to produce risk analysis targeted at the specific MVP and market conditions,
    not a generic version of the idea.

    Parameters:
        startup_idea   (str) → raw startup concept from the user
        market_context (str) → combined summarized output from Stage 1 tools.
                               Defaults to empty string — function works standalone
                               but produces grounded output when context is provided.
        mvp_context    (str) → suggest_mvp() output from Stage 2.
                               Defaults to empty string — when provided, risk analysis
                               targets the specific MVP recommended, not a generic version.

    Returns:
        str → Gemini's plain-text risk report with mitigation strategies on success.
              Returns "Risk analysis unavailable — service error, no data retrieved."
              on failure — matched by Rule 13 in prompts.py for per-section note.

    Why "fatal flaws" framing in prompt:
        Generic risk prompts return obvious boilerplate ("competition exists").
        Asking specifically for fatal flaws forces the model to prioritize
        high-severity, startup-killing risks over generic concerns.

    Why mvp_context matters:
        Risks are MVP-specific — a marketplace MVP has different failure modes
        than a SaaS MVP. Without mvp_context, Gemini analyses a generic
        version of the idea, not the actual build plan from Stage 2.
    """

    # Build risk analyst prompt — inject market and MVP data if available
    market_section = market_context if market_context else "No market data available."
    mvp_section    = mvp_context    if mvp_context    else "No MVP plan available."

    full_prompt = f"""You are a startup risk management expert and venture analyst.
Based on this startup idea: {startup_idea},

Market Analysis:
{market_section}

MVP Plan:
{mvp_section}

Conduct a rigorous risk analysis for launching this product. Focus on identifying fatal flaws
and hidden bottlenecks, and provide clear, actionable mitigation strategies for a small team.
"""

    for attempt in range(3):
        try:
            response = gemini_risk_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )
            break

        except exceptions.ResourceExhausted:
            if attempt < 2:
                wait = 15 * (attempt + 1)
                print(f"   ⏳ Rate limited (429) — retrying in {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                return "Risk analysis unavailable — service error, no data retrieved."

        except exceptions.ServiceUnavailable:
            if attempt < 2:
                wait = 5 * (attempt + 1)
                print(f"   ⏳ Gemini unavailable (503) — retrying in {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                return "Risk analysis unavailable — service error, no data retrieved."

        except exceptions.Unauthenticated as e:
            return f"Auth Error (401): Check system environment API keys. Details: {e}"

        except exceptions.GoogleAPICallError as e:
            return f"Generic API Error: {e.code} - {e.message}"

        except ValueError as e:
            return f"Configuration Error: {e}"

        except Exception:
            return "Risk analysis unavailable — service error, no data retrieved."

    return response.text


# ── RAG TOOL ──────────────────────────────────────────────────

def search_documents(user_input: str, file_name: str) -> str:
    """Queries the local RAG vector store for relevant chunks from one specific uploaded PDF.

    Stage 4 tool — called on-demand, ONLY after Stages 1, 2, and 3 have completed.
    Triggered only when the user explicitly references an uploaded document.
    Delegates entirely to query_rag() in rag.py — this function is intentionally
    thin to keep tool logic separate from RAG pipeline logic.

    Parameters:
        user_input (str) → natural language query from the user or agent
        file_name  (str) → the exact uploaded filename to scope retrieval to.
                           Phase 4 addition — passed straight through to query_rag()'s
                           where={"file_name": file_name} filter, so retrieval only
                           searches the named document's chunks in a shared ChromaDB
                           collection, even when multiple PDFs have been uploaded
                           this session. Currently LLM-trusted (the LLM supplies this
                           value itself from the filenames visible in FILE_PROMPT) —
                           a deliberate, accepted-risk scope decision, not validated
                           against the live file list inside this function. See
                           LEARNING_LOG.md Phase 4 section for the full rationale and
                           the planned hardening path via get_available_files().

    Returns:
        str → formatted plain text string with page citations per chunk.
              Format: "[Page N, filename]: chunk text"
              Returns error string if the vector store is empty, the filename
              doesn't match anything, or the connection is unavailable.

    Why plain text format (not list of dicts):
        Returning a stringified list of dicts required the LLM to parse structured
        data from a string — fragile and error-prone. Plain text with inline
        citations lets the LLM read and cite directly without parsing.

    Why chunk text truncated to 300 chars:
        search_documents() is called as Stage 4, after Stages 1-3 have already
        populated self.messages with substantial context. Untruncated chunks bloat
        the message history and can crowd out the LLM's reasoning room for the
        final answer generation. 300 chars preserves enough for citation and context.

    Why separate from search_knowledge_base():
        This queries local PDFs the user uploaded — private, session-specific context.
        search_knowledge_base() queries the live web. Different grounding purposes,
        should never be merged — one is offline/private, one is online/public.

    Why this function is thin (delegates to query_rag()):
        All RAG pipeline logic belongs in rag.py — ingest, embed, store, retrieve,
        and the where-clause filtering itself. Keeping this wrapper thin means
        tools.py stays decoupled from RAG internals. rag.py can be tested and
        updated independently — including the Phase 4 multi-document filtering.
    """

    print(f"   🔍 Querying local document store — file: {file_name}, query: {user_input}")

    # Delegate to RAG pipeline — file_name scopes the search to one document
    # via query_rag()'s where clause. Returns list of {text, metadata} dicts.
    search_response = query_rag(user_input=user_input, where={"file_name": file_name})

    # Guard against empty results — handles both "no PDF was ingested at all"
    # and "file_name didn't match anything in the collection."
    if not search_response:
        return "No data found in document store. Please check that a file was uploaded successfully."

    # Format as plain text with inline page citations.
    # Truncate each chunk to 300 chars — prevents context window overflow at Stage 4.
    formatted_response = ""
    for chunk in search_response:
        page  = chunk["metadata"]["page_number"]
        fname = chunk["metadata"]["file_name"]
        text  = chunk["text"][:300]
        formatted_response += f"[Page {page}, {fname}]: {text}\n\n"

    return formatted_response