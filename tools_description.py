# ============================================================
#  tools_description.py — Groq Tool Schemas for BizRadar AI
# ============================================================
#
#  What this file does:
#  Defines the tools list passed to the Groq API on every chat completion call.
#  Each entry tells the LLM what tools exist, when to call them, and what
#  parameters to pass — the LLM reads these descriptions to make tool decisions.
#
#  What this file does NOT handle:
#  Does not implement any tool logic — that belongs to tools.py.
#  Does not execute tool calls — that belongs to agent.py.
#  Does not define prompts or agent identity — that belongs to prompts.py.
#
#  Tools defined (in pipeline call order):
#  - analyze_market()        → Stage 1: web search for market data, self-summarizes before returning
#  - search_knowledge_base() → Stage 1: deep web search for competitor grounding, self-summarizes
#  - suggest_mvp()           → Stage 2: MVP features, requires market_context from Stage 1
#  - recommend_tech_stack()  → Stage 2: tech stack, requires market_context from Stage 1
#  - risk_analysis()         → Stage 3: risk report, requires market_context + mvp_context
#  - search_documents()      → Stage 4: on-demand RAG query, called alone AFTER Stage 3 completes
#                              only when user explicitly references an uploaded document
#
#  NOT in this list (internal only, not LLM-callable):
#  - summarize_text()        → called inside analyze_market() and search_knowledge_base()
#                              before each returns — the LLM never sees or calls this directly
#
#  Used by:
#  - agent.py → passed directly as the tools= parameter in client.chat.completions.create()
#
#  Important:
#  The LLM reads every description field to decide when and how to call each tool.
#  Keep descriptions precise and instruction-like — vague descriptions cause wrong
#  tool call ordering or missing required parameters.
#  Stage references in descriptions must stay consistent with TOOL CALL ORDER in prompts.py.
#  search_documents() must always reference Stage 4 — never during Stages 1, 2, or 3.
# ============================================================


# ── TOOL SCHEMAS ──────────────────────────────────────────────
# Ordered by pipeline stage for readability.
# The LLM does not rely on list order — it uses descriptions to decide call order.

tools = [

    # ── STAGE 1 — PARALLEL SEARCH ─────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "analyze_market",
            "description": (
                "Searches the live web for market potential, competition, trends, and industry data "
                "for a given startup idea. Internally summarizes results before returning — "
                "returns a clean summarized string ready for use as market_context. "
                "Always call in Stage 1, in parallel with search_knowledge_base(). "
                "Do not call any Stage 2, 3, or 4 tools until both Stage 1 tools have returned. "
                "Pass the returned string as part of market_context to Stage 2 tools."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "startup_idea": {
                        "type": "string",
                        "description": "The startup concept, business idea, or industry niche to research."
                    }
                },
                "required": ["startup_idea"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Performs a deep web search to identify existing competitors, current market solutions, "
                "and grounding sources that reduce hallucination in downstream tool calls. "
                "Internally summarizes results before returning — "
                "returns a clean summarized string ready for use as market_context. "
                "Always call in Stage 1, in parallel with analyze_market(). "
                "Do not call any Stage 2, 3, or 4 tools until both Stage 1 tools have returned. "
                "Pass the returned string as part of market_context to Stage 2 tools."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The startup concept, business idea, or competitive landscape to research."
                    }
                },
                "required": ["query"]
            }
        }
    },

    # ── STAGE 2 — PARALLEL ANALYSIS ───────────────────────────
    {
        "type": "function",
        "function": {
            "name": "suggest_mvp",
            "description": (
                "Generates a Minimum Viable Product (MVP) plan with core features, target user personas, "
                "and a step-by-step launch sequence grounded in real market data. "
                "Call this tool in Stage 2, in parallel with recommend_tech_stack(). "
                "Do not call before both Stage 1 tools have returned. "
                "Do not call risk_analysis() or search_documents() in this stage. "
                "The output of this tool is the mvp_context value required by risk_analysis() in Stage 3."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "startup_idea": {
                        "type": "string",
                        "description": "The startup concept, business idea, or industry niche to build an MVP for."
                    },
                    "market_context": {
                        "type": "string",
                        "description": (
                            "The combined summarized market research string from Stage 1. "
                            "Concatenate the outputs of analyze_market() and search_knowledge_base(). "
                            "Contains competitor landscape, market trends, and grounding sources."
                        )
                    }
                },
                "required": ["startup_idea", "market_context"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_tech_stack",
            "description": (
                "Recommends a lean software architecture, programming languages, databases, and frameworks "
                "tailored for a small team to launch in under 3 months. Prioritizes speed to market, "
                "ease of development, and minimal maintenance overhead. "
                "Call this tool in Stage 2, in parallel with suggest_mvp(). "
                "Do not call before both Stage 1 tools have returned. "
                "Do not call risk_analysis() or search_documents() in this stage."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "startup_idea": {
                        "type": "string",
                        "description": "The startup concept, business idea, or industry niche to recommend a stack for."
                    },
                    "market_context": {
                        "type": "string",
                        "description": (
                            "The combined summarized market research string from Stage 1. "
                            "Concatenate the outputs of analyze_market() and search_knowledge_base(). "
                            "Used to align stack recommendations with what competitors use and what users expect."
                        )
                    }
                },
                "required": ["startup_idea", "market_context"]
            }
        }
    },

    # ── STAGE 3 — RISK ANALYSIS (ALONE) ───────────────────────
    {
        "type": "function",
        "function": {
            "name": "risk_analysis",
            "description": (
                "Evaluates market, operational, financial, and technical risks for a startup idea "
                "and provides specific mitigation strategies targeted at a small team. "
                "Call this tool alone in Stage 3, after both Stage 2 tools have completed. "
                "Do not call this tool in the same batch as suggest_mvp() or recommend_tech_stack(). "
                "Do not call search_documents() in this stage. "
                "Requires market_context from Stage 1 and mvp_context from suggest_mvp() in Stage 2 — "
                "risks are evaluated against the specific MVP plan, not a generic version of the idea."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "startup_idea": {
                        "type": "string",
                        "description": "The startup concept, business idea, or industry niche to analyse risks for."
                    },
                    "market_context": {
                        "type": "string",
                        "description": (
                            "The combined summarized market research string from Stage 1. "
                            "Concatenate the outputs of analyze_market() and search_knowledge_base(). "
                            "Contains competitor landscape, market trends, and grounding sources."
                        )
                    },
                    "mvp_context": {
                        "type": "string",
                        "description": (
                            "The MVP plan string returned by suggest_mvp() in Stage 2. "
                            "Used to evaluate risks specific to the recommended build plan, "
                            "not a generic startup risk assessment."
                        )
                    }
                },
                "required": ["startup_idea", "market_context", "mvp_context"]
            }
        }
    },

    # ── STAGE 4 — RAG DOCUMENT SEARCH (ON-DEMAND, AFTER STAGE 3) ──
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Queries the local RAG vector store to retrieve relevant chunks from PDFs or documents "
                "the user has uploaded. "
                "Call this tool as Stage 4 — ONLY after Stages 1, 2, and 3 have all completed. "
                "Do not call this tool during Stage 1, 2, or 3. "
                "Call it exactly once. Do not batch with any other tool. "
                "Trigger ONLY when the user explicitly references an uploaded file, pitch deck, "
                "document, or attachment — not for general web research. "
                "This tool queries private local content only; it does not search the web. "
                "If the user did not reference a document — do not call this tool at all."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "The user's natural language query to search within the uploaded document store."
                    }
                },
                "required": ["user_input"]
            }
        }
    }
]