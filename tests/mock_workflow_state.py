# Provides pre-filled workflow_state dicts for testing each agent independently
# Every agent must be testable WITHOUT running the full pipeline

MOCK_STATE_FULL = {
    "user_input": (
        "I want to build an AI-powered tiffin delivery service for college "
        "students. It should offer affordable subscriptions, personalized "
        "meal recommendations, and reliable campus delivery. Help me analyze "
        "the market, define an MVP, recommend a practical tech stack, identify "
        "risks, score the idea, and suggest ways to improve it."
    ),

    "startup_idea": (
        "An AI-powered tiffin subscription and delivery service for college "
        "students, focused on affordable meals, personalized recommendations, "
        "and reliable campus delivery."
    ),

    "startup_type": (
        "FoodTech / Subscription Food Delivery"
    ),

    "pitch_deck_text": "",

    "judge_feedback": {
        "mid_pipeline": "",
        "final": ""
    },

    "intent": "full_analysis",

    "execution_plan": [
        "MarketResearchAgent",
        "WebSearchAgent",
        "MVPAdvisorAgent",
        "TechAdvisorAgent",
        "RiskAnalystAgent",
        "StartupScorerAgent",
        "RecommendationAgent",
        "NurturingAgent",
        "AdvancementAgent",
        "ReportWriterAgent",
        "PDFGeneratorAgent"
    ],

    "market_data": (
        "Mock market evidence: Subscription-based meal services may provide "
        "predictable recurring revenue. Personalized food experiences may "
        "improve customer engagement. Direct validation with college students "
        "is still required.\n"
        "Source: MOCK_SOURCE_01"
    ),

    "web_search_results": (
        "Mock competitor research: Existing meal-delivery services compete "
        "through pricing, convenience, subscription plans, meal variety, and "
        "delivery coverage.\n"
        "Source: MOCK_SOURCE_02"
    ),

    "rag_context": [
        {
            "text": (
                "College students often prioritize affordability, convenience, "
                "meal variety, and predictable availability."
            ),
            "source": "mock_student_food_research",
            "page": 4
        }
    ],

    "mvp_suggestions": (
        "Start with student registration, dietary preference collection, "
        "weekly subscription selection, basic meal recommendations, order "
        "tracking, and meal feedback."
    ),

    "tech_recommendations": (
        "Frontend: React. Backend: FastAPI. Database: PostgreSQL. "
        "AI recommendation service: Python. Deployment: Docker."
    ),

    "risk_analysis": (
        "Customer acquisition risk: students may not switch from existing "
        "options. Operational risk: delivery consistency and food quality. "
        "Unit economics risk: low student budgets may limit margins. "
        "Retention risk: insufficient meal variety may cause cancellations."
    ),

    "startup_score": {
        "score": 72,
        "reasoning": (
            "The concept addresses a clear student need, but willingness to "
            "pay, delivery economics, and operational feasibility require "
            "validation."
        ),
        "breakdown": {
            "product": 78,
            "market": 74,
            "business_model": 70,
            "scalability": 68,
            "feasibility": 65
        },
        "highest_risk_flag": "feasibility"
    },

    "recommendations": [
        {
            "rank": 1,
            "title": "Run a campus pilot",
            "action": (
                "Test the service with a small student group before scaling."
            ),
            "reason": (
                "This validates willingness to pay and operational feasibility."
            )
        },
        {
            "rank": 2,
            "title": "Start with subscriptions",
            "action": (
                "Offer a limited weekly subscription before adding on-demand "
                "delivery."
            ),
            "reason": (
                "A narrower initial model can simplify operations."
            )
        }
    ],

    "generated_ideas": [
        {
            "rank": 1,
            "idea": (
                "Student meal subscriptions with preference-based weekly "
                "recommendations."
            ),
            "market_signal": (
                "Mock evidence indicates interest in personalized food "
                "experiences."
            )
        }
    ],

    "nurtured_idea": (
        "Refine the service around affordable student subscriptions, "
        "preference-based meal recommendations, and reliable campus delivery."
    ),

    "advancement_plan": (
        "Launch a small campus pilot focused on personalized subscriptions "
        "and measure willingness to pay, retention, satisfaction, and delivery "
        "reliability."
    ),

    "chat_response"      : "",

    "final_report"       : "",

    "pdf_path"           : "",

    "pipeline_status"    : {},

    "agent_retry_count"  : {},

    "execution_log"      : [],

    "errors"             : []
}

MOCK_STATE_EMPTY = {
    # All keys initialized to None / "" / [] as per schema
    # Used for testing early-stage agents like MarketResearchAgent
    "user_input"              : "",
    "startup_idea"            : "",
    "startup_type"            : "",
    "pitch_deck_text"         : "",
    "judge_feedback"          : {
        "mid_pipeline"        : "",
        "final"               : ""
    },
    "intent"                  : "",
    "execution_plan"          : [],
    "market_data"             : "",
    "web_search_results"      : "",
    "rag_context"             : [],
    "mvp_suggestions"         : "",
    "tech_recommendations"    : "",
    "risk_analysis"           : "",
    "startup_score"           : {},
    "recommendations"         : [],
    "generated_ideas"         : [],
    "nurtured_idea"           : "",
    "advancement_plan"        : "",
    "chat_response"           : "",
    "final_report"            : "",
    "pdf_path"                : "",
    "pipeline_status"         : {},
    "agent_retry_count"       : {},
    "execution_log"           : [],
    "errors"                  : []
}