# Session 26 — Complete Debug Roadmap

## Schema Decisions Locked

```
IntentRouterAgent writes:
  → intent
  → execution_plan
  → startup_idea   (NEW)
  → startup_type   (NEW)

NurturingAgent reads recommendations → LLM handles absence naturally
```

---

## FLAG 1 — Workflow State Schema

### Task 1.1 — Update `workflow_state.py`
**Branch:** `debug/flag1-workflow-state-schema`

**Changes:**
- Add `startup_idea: str` key
- Add `startup_type: str` key
- Add `judge_feedback` key (already decided Session 23)

**Files:** `workflow_state.py` only

---

### Task 1.2 — Update Mock State
**Branch:** `debug/flag1-mock-state-update`

**Changes:**
- Add `startup_idea` to `MOCK_STATE_FULL` with realistic value
- Add `startup_type` to `MOCK_STATE_FULL` with realistic value
- Add all keys with realistic content throughout

**Realistic mock data I'm generating for you:**

```python
MOCK_STATE_FULL = {
    "user_input": "I want to build an AI-powered tiffin delivery service for college students in Pune",
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
    "judge_feedback": "",
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
        "LLMJudgeAgent": "pending"
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
```

**Files:** `tests/mock_workflow_state.py` only

---

## FLAG 2 — IntentRouterAgent Prompt

### Task 2.1 — Remove PDFGeneratorAgent from prompt
**Branch:** `debug/flag2-intent-router-pdf-removal`

**Changes:**
- Remove `PDFGeneratorAgent` from execution plan instructions in prompt
- Verify batch structure matches locked execution plan format

**Files:** `prompts/prompts.py` only

### Task 2.2 — Add startup_idea + startup_type to prompt output
**Branch:** `debug/flag2-intent-router-new-outputs`

**Changes:**
- Add instruction to extract `startup_idea` from `user_input`
- Add instruction to classify `startup_type` as single string
- Update expected JSON output format in prompt
- Update `IntentRouterAgent` to write both new keys

**Files:** `prompts/prompts.py`, `agents/intent_router_agent.py`

---

## FLAG 3 — TechAdvisorAgent Prompt

### Task 3.1 — Fix over-engineering bias
**Branch:** `debug/flag3-tech-advisor-lean-stack`

**Changes:**
- Remove Docker/Kubernetes recommendation bias from prompt
- Add explicit rule: prefer modular monolith for early-stage
- Add rule: no orchestration tools until 10k+ users
- Add rule: justify every tool choice against team size
- Read startup_idea and startup_type from workflow_state
- Inject startup_idea and startup_type into user prompt
- Update TECH_ADVISOR_PROMPT to use both fields as context
- Update docstring: Reads section

**Files:** `prompts/prompts.py`, `agents/tech_advisor_agent.py`

---

## FLAG 4 — IdeaGenerationAgent Prompt

### Task 4.1 — Tighten market_signal specificity
**Branch:** `debug/flag4-idea-gen-market-signal`

**Changes:**
- Add explicit rule: `market_signal` must name specific trend, number, or event
- Add rule: signal must directly support the proposed idea
- Add negative example in prompt: "growing market" is not acceptable
- Add positive example: "India edtech grew 38% YoY in 2023 per KPMG" is acceptable
- Read startup_idea and startup_type from workflow_state
- Inject startup_idea and startup_type into user prompt
- Update IDEA_GENERATION_PROMPT to use both fields as context
- Update docstring: Reads section

**Files:** `prompts/prompts.py`, `agents/idea_generation_agent.py`

---

## FLAG 5 — MOCK_STATE_FULL Realistic Data

### Task 5.1 — Replace placeholder data
**Branch:** `debug/flag5-mock-state-realistic-data`

**Changes:**
- Replace all placeholder strings with realistic content from Task 1.2 above
- Verify every agent key has enough content to produce meaningful output
- Add `startup_idea` and `startup_type` realistic values

**Files:** `tests/mock_workflow_state.py` only

---

## FLAG 6 — JSON Output Tests + Fixes

### Task 6.1 — Test + fix StartupScorerAgent
**Branch:** `debug/flag6-json-startup-scorer`

**Changes:**
- Run agent against `MOCK_STATE_FULL`
- Verify structured dict output parses correctly
- Fix prompt if output is malformed

**Files:** `prompts/prompts.py`, `agents/startup_scorer_agent.py` if broken

---

### Task 6.2 — Test + fix RecommendationAgent
**Branch:** `debug/flag6-json-recommendation`

**Changes:**
- Run agent against `MOCK_STATE_FULL`
- Verify structured list of dicts parses correctly
- Fix prompt if output is malformed
- Read startup_idea and startup_type from workflow_state
- Inject startup_idea and startup_type into user prompt
- Update RECOMMENDATION_PROMPT to use both fields as context
- Update docstring: Reads section

**Files:** `prompts/prompts.py`, `agents/recommendation_agent.py`

---

### Task 6.3 — Test + fix IdeaGenerationAgent
**Branch:** `debug/flag6-json-idea-generation`

**Changes:**
- Run agent against `MOCK_STATE_FULL`
- Verify ranked list of dicts parses correctly
- Fix prompt if output is malformed

**Files:** `prompts/prompts.py`, `agents/idea_generation_agent.py` if broken

---

### Task 6.4 — Test + fix LLMJudgeAgent
**Branch:** `debug/flag6-json-llm-judge`

**Changes:**
- Run `run_mid()` and `run_final()` against mock state
- Verify PASS/FAIL + feedback output parses correctly
- Fix prompt if output is malformed
- Read startup_idea and startup_type from workflow_state
- Inject startup_idea and startup_type into user prompt
- Update LLM_JUDGE_PROMPT to use both fields as context
- Update docstring: Reads section

**Files:** `prompts/prompts.py`, `agents/llm_judge_agent.py`

---

## FLAG 7 — NurturingAgent + Recommendations

### Task 7.1 — Wire recommendations into NurturingAgent
**Branch:** `debug/flag7-nurturing-recommendations`

**Changes:**
- Add `recommendations` to `NurturingAgent` input keys
- Update prompt to include `recommendations` context
- No branching logic — LLM handles empty list naturally
- Update docstring: Reads + Writes section
- Read startup_idea and startup_type from workflow_state
- Inject startup_idea and startup_type into user prompt
- Update NURTURING_PROMPT to use both fields as context
- Update docstring: Reads section

**Files:** `prompts/prompts.py`, `agents/nurturing_agent.py`

---

## FLAG 8 — startup_idea + startup_type Sweep (Remaining Agents)

### Task 8.1 — Update remaining agents
**Branch:** `debug/flag8-startup-context-sweep`

**Changes:**
- Add startup_idea and startup_type to reads + user prompt injection for:
  - market_research_agent.py + MARKET_RESEARCH_PROMPT
  - web_search_agent.py + WEB_SEARCH_PROMPT
  - rag_agent.py + RAG_AGENT_PROMPT
  - mvp_advisor_agent.py + MVP_ADVISOR_PROMPT
  - risk_analyst_agent.py + RISK_ANALYST_PROMPT
  - advancement_agent.py + ADVANCEMENT_PROMPT
  - general_chat_agent.py + GENERAL_CHAT_PROMPT
  - report_writer_agent.py + REPORT_WRITER_PROMPT
  - pdf_generator_agent.py + PDF_GENERATOR_PROMPT

**Files:** all agent files listed above + prompts/prompts.py

**Note:** OrchestratorAgent is excluded — it delegates only, no LLM prompt.

---

## Complete Flag Summary

```
FLAG 1 → Task 1.1 + Task 1.2   → 2 branches
FLAG 2 → Task 2.1 + Task 2.2   → 2 branches
FLAG 3 → Task 3.1               → 1 branch
FLAG 4 → Task 4.1               → 1 branch
FLAG 5 → Task 5.1               → 1 branch
FLAG 6 → Task 6.1 + 6.2 + 6.3 + 6.4 → 4 branches
FLAG 7 → Task 7.1               → 1 branch
FLAG 8 → Task 8.1               → 1 branch

TOTAL  → 13 branches, 13 PRs, 13 merges
```

---

**Confirm this roadmap. Then we start FLAG 1, Task 1.1.**