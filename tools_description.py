tools = [
  {
    "type": "function",
    "function": {
      "name": "analyze_market",
      "description": "Analyzes the market potential, competition, and trends for a specific startup idea by performing a live web search.",
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
      "name": "summarize_text",
      "description": "Condenses long text inputs, conversations, or large system responses into a short, structured summary.",
      "parameters": {
        "type": "object",
        "properties": {
          "message": {
            "type": "object",
            "description": "The full text or document content that needs to be summarized."
          }
        },
        "required": ["message"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "search_knowledge_base",
      "description": "Identifies existing competitors and current market solutions to outline competitive advantages and product differentiation strategies.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "The startup concept, business idea, or industry niche to research."
          }
        },
        "required": ["query"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "suggest_mvp",
      "description": "Generates a Minimum Viable Product (MVP) plan detailing core features, target user personas, and a step-by-step launch sequence.",
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
      "name": "recommend_tech_stack",
      "description": "Recommends an optimized software architecture, programming languages, databases, and frameworks tailored to scale the business efficiently.",
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
      "name": "risk_analysis",
      "description": "Evaluates potential market, operational, financial, and legal risks for a business idea and provides specific mitigation strategies.",
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
  }
]



