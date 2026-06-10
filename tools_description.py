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
      "description": "Condenses long text inputs, conversations, or large system responses into a short, structured summary. Called after analyze_market and search_knowledge_base tool calls to summarize their url and summmarixing their text generation in short making it consise and keep the content complied  ",
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
      "description": "Generates a Minimum Viable Product (MVP) plan detailing core features, target user personas, and a step-by-step launch sequence.Before calling this tool we need to have the response readu fo analyze_market and then summazize that tool result with summarize_text and that response will be the input of this tool ",
      "parameters": {
        "type": "object",
        "properties": {
          "startup_idea": {
            "type": "string",
            "description": "The startup concept, business idea, or industry niche to research."
          },
          "market_context":{
            "type":"string",
            "description":"brings the market_context in the tool containing all the necessary information about the market"
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
      "description": "Recommends an optimized software architecture, programming languages, databases, and frameworks tailored to scale the business efficiently.Before calling this tool we need to have the response readu fo analyze_market and then summazize that tool result with summarize_text and that response will be the input of this tool ",
      "parameters": {
        "type": "object",
        "properties": {
          "startup_idea": {
            "type": "string",
            "description": "The startup concept, business idea, or industry niche to research."
          },
          "market_context":{
            "type":"string",
            "description":"brings the market_context in the tool containing all the necessary information about the market"
          }
        },
        "required": ["startup_idea","market_context"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "risk_analysis",
      "description": "Evaluates potential market, operational, financial, and legal risks for a business idea and provides specific mitigation strategies. Before calling this tool we need to have the response ready fo analyze_market and  MVP_suggestions then summazize that tool result with summarize_text and that response will be the input of this tool ",
      "parameters": {
        "type": "object",
        "properties": {
          "startup_idea": {
            "type": "string",
            "description": "The startup concept, business idea, or industry niche to research."
          },
          "market_context":{
            "type":"string",
            "description":"brings the market_context in the tool containing all the necessary information about the market"
          },
          "mvp_context":{
            "type":"string",
            "description":"Takes MVP content to the tool giving him the knowledge of current thinking MVP features "
          }
        },
        "required": ["startup_idea","market_context","mvp_context"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "search_documents",
      "description": "Use this tool when the user explicitly references or relies on their uploaded file, specific document, or local attachment to complete the request.",
      "parameters": {
        "type": "object",
        "properties": {
          "user_input": {
            "type": "string",
            "description": "The user query or search terms to look up within the attached document database."
          }
        },
        "required": ["user_input"]
      }
    }
  }
]



