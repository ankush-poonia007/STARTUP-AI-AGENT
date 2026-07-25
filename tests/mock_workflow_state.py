# Provides pre-filled workflow_state dicts for testing each agent independently
# Every agent must be testable WITHOUT running the full pipeline

MOCK_STATE_FULL = {
    "user_input"          : "AI-powered tiffin delivery for college students",
    "pitch_deck_text"     : "",
    "judge_feedback": {"mid_pipeline": "", "final": ""},
    "intent"              : "full_analysis",
    "execution_plan"      : [],
    "market_data"         : "Sample market data with citations...",
    "web_search_results"  : "Sample competitor data with citations...",
    "rag_context"         : [],
    "mvp_suggestions"     : "Sample MVP suggestions...",
    "tech_recommendations": "Sample tech stack...",
    "risk_analysis"       : "Sample risk analysis...",
    "startup_score"       : {"score": 72, "reasoning": "...", "breakdown": {}, "highest_risk_flag": "market"},
    "recommendations"     : [],
    "generated_ideas"     : [],
    "nurtured_idea"       : "",
    "advancement_plan"    : "",
    "chat_response"       : "",
    "final_report"        : "",
    "pdf_path"            : "",
    "pipeline_status"     : {},
    "agent_retry_count"   : {},
    "execution_log"       : [],
    "errors"              : []
}

MOCK_STATE_EMPTY = {
    # All keys initialized to None / "" / [] as per schema
    # Used for testing early-stage agents like MarketResearchAgent
    "user_input"              : "",
        "pitch_deck_text"     : "",
        "judge_feedback": {"mid_pipeline": "", "final": ""},
        "intent"              : "",
        "execution_plan"      : [],
        "market_data"         : "",
        "web_search_results"  : "",
        "rag_context"         : [],
        "mvp_suggestions"     : "",
        "tech_recommendations": "",
        "risk_analysis"       : "",
        "startup_score"       : {},
        "recommendations"     : [],
        "generated_ideas"     : [],
        "nurtured_idea"       : "",
        "advancement_plan"    : "",
        "chat_response"       : "",
        "final_report"        : "",
        "pdf_path"            : "",
        "pipeline_status"     : {},
        "agent_retry_count"   : {},
        "execution_log"       : [],
        "errors"              : []
}