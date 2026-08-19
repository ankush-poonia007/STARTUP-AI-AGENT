# Provides pre-filled workflow_state dicts for testing each agent independently
# Every agent must be testable WITHOUT running the full pipeline

MOCK_STATE_FULL = {
    "user_input": "I want to build an AI-powered tiffin delivery service for college students in Pune",
    "pitch_deck_text" : [],
    "startup_idea": "AI-powered tiffin delivery service for college students",
    "startup_type": "FoodTech / Food Delivery",
    "intent": "full_analysis",
    "execution_plan": [
        {"batch": 1, "agents": ["MarketResearchAgent", "WebSearchAgent", "RAGAgent"], "parallel": True},
        {"batch": 2, "agents": ["MVPAdvisorAgent", "TechAdvisorAgent"], "parallel": True},
        {"batch": 3, "agents": ["RiskAnalystAgent"], "parallel": False},
        {"batch": 4, "agents": ["StartupScorerAgent"], "parallel": False},
        {"batch": 5, "agents": ["RecommendationAgent"], "parallel": False},
        {"batch": 6, "agents": ["ReportWriterAgent"], "parallel": False}
    ],
    "market_data": "Title: India Online Food Delivery Market 2024\nSummary: India food delivery market valued at $7.5B in 2023, projected to reach $15B by 2028. College student segment drives 34% of orders in Tier-1 and Tier-2 cities. Key players: Swiggy, Zomato dominate but lack homestyle meal focus.\nURL: https://example-market-research.com/india-foodtech-2024\n\nTitle: Tiffin Service Demand Surge Post-COVID\nSummary: Homestyle tiffin demand grew 67% among students aged 18-24 post-2021. Price sensitivity is high — average acceptable price point is Rs 80-120 per meal.\nURL: https://example-foodtech-trends.com/tiffin-demand",
    "web_search_results": "Title: Competitors in Student Tiffin Space\nSummary: Startups like TiffinBox, HomeChef, and MealMate operate regionally. None use AI for demand prediction or personalization. Funding: TiffinBox raised $2M seed in 2023.\nURL: https://example-competitor-analysis.com/tiffin-startups\n\nTitle: Swiggy Daily — Subscription Meal Play\nSummary: Swiggy launched Daily subscription targeting office workers. Student segment underserved. Opportunity exists for hyper-local AI-driven tiffin scheduling.\nURL: https://example-funding-news.com/swiggy-daily-2024",
    "rag_context": [
        {
            "text": "Our target demographic is college students aged 18-24 in Pune with monthly food budget of Rs 3000-5000.",
            "metadata": {"page_number": 2, "file_name": "tiffin_pitch_deck.pdf"},
            "rerank_score": 0.91
        },
        {
            "text": "Core differentiator: AI meal scheduling based on college timetables and exam schedules.",
            "metadata": {"page_number": 4, "file_name": "tiffin_pitch_deck.pdf"},
            "rerank_score": 0.87
        },
        {
            "text": "Go-to-market: Partner with 5 college canteens in Pune in Month 1. Target 500 subscribers by Month 3.",
            "metadata": {"page_number": 7, "file_name": "tiffin_pitch_deck.pdf"},
            "rerank_score": 0.82
        }
    ],
    "mvp_suggestions": "## Core Features\n1. AI meal scheduling based on college timetable\n2. WhatsApp-based order management\n3. Subscription plan — weekly/monthly\n4. Real-time delivery tracking\n\n## Target User Personas\n- Out-of-town college student, hostel resident\n- Budget-conscious, wants homestyle food\n\n## 3-Month Build Scope\nMonth 1: WhatsApp bot + manual kitchen onboarding\nMonth 2: Basic AI scheduling + payment integration\nMonth 3: Delivery tracking + feedback loop\n\n## Launch Sequence\nSoft launch → 2 colleges → 100 students → iterate",
    "tech_recommendations": "## Frontend\nWhatsApp Business API — zero app install friction\n\n## Backend\nPython FastAPI — lightweight, async-ready\n\n## Database\nPostgreSQL — reliable relational data for orders/subscriptions\n\n## Infrastructure\nSingle VPS (DigitalOcean) — sufficient for 0-1 stage\n\n## Rationale\nLean stack chosen for 2-person team. Avoid Kubernetes until 10k+ users.",
    "risk_analysis": "### Feature: AI Meal Scheduling\nRisk: Prediction accuracy low with cold-start data\nWhy: No historical data at launch\nImpact: Poor user experience in Week 1-2\nMitigation: Manual override option always available\n\n### Feature: WhatsApp Order Management\nRisk: WhatsApp API policy changes\nWhy: Meta controls API access\nImpact: Entire order flow breaks\nMitigation: Build email/SMS fallback in Month 2\n\n## Highest Business Risk\nRisk: Kitchen partner reliability\nReason: Single kitchen failure stops all deliveries\nMitigation: Onboard minimum 3 kitchen partners before launch",
    "startup_score": {
        "score": 74,
        "reasoning": "Strong market demand signal with clear underserved segment. Execution risk is moderate due to kitchen dependency. Tech approach is appropriately lean for stage.",
        "breakdown": {
            "market": 82,
            "mvp": 76,
            "tech": 80,
            "risk": 58
        },
        "highest_risk_flag": "risk"
    },
    "recommendations": [
        {
            "title": "Add kitchen partner redundancy",
            "description": "Onboard minimum 3 kitchen partners before launch to avoid single point of failure",
            "evidence": "https://example-foodtech.com/kitchen-partner-strategy",
            "linked_weakness": "RiskAnalystAgent flagged kitchen reliability as highest business risk"
        },
        {
            "title": "Introduce loyalty program early",
            "description": "Student retention is driven by consistency and rewards. Introduce stamp-card style loyalty in Month 2.",
            "evidence": "https://example-retention-study.com/student-loyalty",
            "linked_weakness": "MVPAdvisorAgent did not include retention mechanic in core features"
        },
        {
            "title": "Target exam season surge demand",
            "description": "Food delivery spikes 40% during exam periods. Build surge capacity planning into Month 3 roadmap.",
            "evidence": "https://example-demand-study.com/exam-season-food",
            "linked_weakness": "MarketResearchAgent identified student demand patterns"
        }
    ],
    "generated_ideas": [],
    "nurtured_idea": "",
    "advancement_plan": "",
    "chat_response": "",
    "final_report": "# Startup Analysis Report\n\n## 1. Market Overview\nIndia food delivery market at $7.5B, growing to $15B by 2028. Student segment drives 34% of orders. Tiffin demand grew 67% post-COVID among 18-24 age group.\n\n## 2. MVP Recommendations\nWhatsApp-first ordering, AI meal scheduling, subscription model. 3-month phased build for 2-person team.\n\n## 3. Tech Stack\nFastAPI backend, PostgreSQL, WhatsApp Business API, single VPS. Lean and appropriate for 0-1 stage.\n\n## 4. Risk Analysis\nHighest risk: kitchen partner reliability. Secondary: WhatsApp API dependency. Mitigations defined per feature.\n\n## 5. Startup Score\nOverall: 74/100. Market: 82, MVP: 76, Tech: 80, Risk: 58.\n\n## 6. Improvement Recommendations\n3 specific improvements: kitchen redundancy, loyalty program, exam season capacity.\n\n## 7. Pitch Deck Insights\nTarget: 18-24 Pune students. Differentiator: AI timetable-based scheduling. GTM: 5 canteen partners, 500 subscribers by Month 3.\n\n## 8. Strategic Summary\nStrong market fit with lean execution path. Primary focus: kitchen reliability and WhatsApp fallback before scaling.",
    "pdf_path": "",
    "judge_feedback": {
        "mid_pipeline": {
            "judgment": "PASS",
            "reason": (
                "The workflow correctly identifies a full startup analysis request and "
                "executes the expected research, RAG, MVP, and technology stages. The "
                "market evidence, web research, RAG context, MVP scope, and lean technology "
                "recommendations remain relevant to the AI-powered tiffin delivery concept "
                "for college students."
            ),
            "issues": []
        },
        "final": {
            "judgment": "PASS",
            "reason": (
                "The final report covers the required analysis areas and remains consistent "
                "with the supplied workflow state. The market evidence, MVP direction, "
                "technology stack, risk analysis, startup score, recommendations, and "
                "strategic summary are coherent with the startup idea and supporting inputs."
            ),
            "issues": []
        }
    },
    "pipeline_status": {
        "IntentRouterAgent": "success",
        "MarketResearchAgent": "success",
        "WebSearchAgent": "success",
        "RAGAgent": "success",
        "MVPAdvisorAgent": "success",
        "TechAdvisorAgent": "success",
        "RiskAnalystAgent": "success",
        "StartupScorerAgent": "success",
        "RecommendationAgent": "success",
        "ReportWriterAgent": "success",
        "PDFGeneratorAgent": "pending",
        "LLMJudgeAgent": {}
    },
    "agent_retry_count": {
        "MarketResearchAgent": 0,
        "RiskAnalystAgent": 0,
        "StartupScorerAgent": 0
    },
    "execution_log": [
        {"agent": "IntentRouterAgent", "status": "success", "duration_seconds": 1.2},
        {"agent": "MarketResearchAgent", "status": "success", "duration_seconds": 3.4},
        {"agent": "WebSearchAgent", "status": "success", "duration_seconds": 2.9},
        {"agent": "RAGAgent", "status": "success", "duration_seconds": 1.8},
        {"agent": "MVPAdvisorAgent", "status": "success", "duration_seconds": 2.1},
        {"agent": "TechAdvisorAgent", "status": "success", "duration_seconds": 1.9},
        {"agent": "RiskAnalystAgent", "status": "success", "duration_seconds": 4.2},
        {"agent": "StartupScorerAgent", "status": "success", "duration_seconds": 1.6},
        {"agent": "RecommendationAgent", "status": "success", "duration_seconds": 3.8},
        {"agent": "ReportWriterAgent", "status": "success", "duration_seconds": 5.1}
    ],
    "errors": []
}

MOCK_STATE_EMPTY = {
    # All keys initialized to None / "" / [] as per schema
    # Used for testing early-stage agents like MarketResearchAgent
    "user_input": "",
    "pitch_deck_text" : [],
    "startup_idea": "",
    "startup_type": "",
    "intent": "",
    "execution_plan": [],
    "market_data": "",
    "web_search_results": "",
    "rag_context": [],
    "mvp_suggestions": "",
    "tech_recommendations": "",
    "risk_analysis": "",
    "startup_score": {
        "score": 0,
        "reasoning": "",
        "breakdown": {},
        "highest_risk_flag": ""
    },
    "recommendations": [],
    "generated_ideas": [],
    "nurtured_idea": "",
    "advancement_plan": "",
    "chat_response": "",
    "final_report": "",
    "pdf_path": "",
    "judge_feedback": {
        "mid_pipeline": {
            "judgment": "",
            "reason" : "",
            "issues" : []
        },
        "final": {
            "judgment": "",
            "reason" : "",
            "issues" : []
        }
    },
    "pipeline_status": {},
    "agent_retry_count": {},
    "execution_log": [],
    "errors": []
}