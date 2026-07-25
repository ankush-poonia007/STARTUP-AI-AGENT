# workflow_state.py — schema only, zero logic, zero imports

workflow_state = {

    # ── INPUTS ──────────────────────────────────────────
    "user_input"           : "",     # raw user message
    "pitch_deck_text"      : "",     # extracted PDF text, "" if none

    # ── LLM AS JUDGE  ───────────────────────────────────
    "judge_feedback": {
        "mid_pipeline": "",
        "final"       : ""
    },
    
    # ── INTENT & PLAN ───────────────────────────────────
    "intent"               : "",     # classified by IntentRouterAgent
    "execution_plan"       : [],    # ordered agent execution list with parallel flags

    # ── AGENT OUTPUTS ────────────────────────────────────
    "market_data"          : "",     # MarketResearchAgent — plain text + citations
    "web_search_results"   : "",     # WebSearchAgent —  teplainxt + citations
    "rag_context"          : [],    # RAGAgent — list of chunk dicts with metadata
    "mvp_suggestions"      : "",     # MVPAdvisorAgent — structured plain text
    "tech_recommendations" : "",     # TechAdvisorAgent — structured plain text
    "risk_analysis"        : "",     # RiskAnalystAgent — per-feature risk plain text
    "startup_score"        : {
        "score"           : 0,     # 0-100 overall
        "reasoning"        : "",     # explanation
        "breakdown"        : {},    # per-section scores
        "highest_risk_flag": ""     # lowest scoring area name
    },
    "recommendations"      : [],    # RecommendationAgent — list of dicts
    "generated_ideas"      : [],    # IdeaGenerationAgent — list of ranked dicts
    "nurtured_idea"        : "",     # NurturingAgent — structured plain text
    "advancement_plan"     : "",     # AdvancementAgent — structured plain text
    "chat_response"        : "",     # GeneralChatAgent — plain conversational text
    "final_report"         : "",     # ReportWriterAgent — full markdown document
    "pdf_path"             : "",     # PDFGeneratorAgent — file path, "" if none

    # ── PIPELINE TRACKING ────────────────────────────────
    "pipeline_status"      : {},    # per-agent: "success"/"failed"/"skipped"/"pending"
    "agent_retry_count"    : {},    # per-agent: int — tracks retries vs MAX_RETRIES
    "execution_log"        : [],    # per-agent: name + timing + status entries
    "errors"               : []     # per-agent: error log — see Error Log Format above
    
}

if __name__ == "__main__":
    print("Hello")
    