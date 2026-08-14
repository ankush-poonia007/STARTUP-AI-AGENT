""" 
File        : agents/recommendation_agent.py
Triggered By: full_analysis, nurturing
Tools       : tavily_tool.py + groq_tool.py
Input       : ALL previous workflow_state outputs
Output      : workflow_state["recommendations"]

Output Format:
    workflow_state["recommendations"] → list of dicts
        [
            {
                "title"         : str,  # short improvement title
                "description"   : str,  # what to improve + why
                "evidence"      : str,  # URL or search evidence
                "linked_weakness": str  # which agent flagged this weakness
            },
            ...  # 3-5 items maximum
        ]

Responsibilities:
- Run FRESH Tavily search — comparison + improvement focused
- Query: "how can [startup type] improve vs competitors"
- Generate 3-5 specific actionable improvements
- Ground each recommendation in fresh search evidence
- Tie each recommendation to a specific weakness from previous agents
"""
from src.core.decorators import ( 
    handle_errors,
    log_execution,
    track_timing,
    retry_on_failure
)

from src.prompts.prompts import RECOMMENDATION_PROMPT
from src.tools.tavily_tool import ask_tavily
from src.tools.groq_tool import text_call

import json 
import re

class RecommendationAgent:
    
    @handle_errors
    @log_execution
    @track_timing
    @retry_on_failure
    def run(self, workflow_state:dict)->dict:
        """_summary_

        Args:
            workflow_state (dict): _description_

        Returns:
            dict: _description_
        """
        
        """_summary_

        Returns:
            _type_: _description_
        """
        """
        INPUT
        └── workflow_state: user_input, startup_score, 
                            risk_analysis, mvp_suggestions

        STEP 1 → Extract highest_risk_flag from startup_score
        STEP 2 → Extract key risks from risk_analysis
        STEP 3 → Build Tavily query f-string using extracted data
        STEP 4 → Call Tavily → store raw results
        STEP 5 → Call Groq with: raw results + extracted weaknesses
                → instruct JSON output (list of dicts)
        STEP 6 → json.loads() → validate structure
        STEP 7 → Write to workflow_state["recommendations"]
        STEP 8 → Update pipeline_status
        STEP 9 → Return workflow_state

        OUTPUT
        └── workflow_state["recommendations"] → list of dicts
            {title, description, evidence, linked_weakness}
        """
        user_input = workflow_state["user_input"]
        
        # startup_idea, startup_type = workflow_state["startup_idea"], workflow_state["startup_type"]
        
        highest_risk_flag = workflow_state["startup_score"]["highest_risk_flag"]
        
        risk_analysis = workflow_state["risk_analysis"]
        
        tavily_prompt = f"how can {user_input} improve vs competitors"
        
        # tavily_prompt = f"how can {startup_idea} type of {startup_type} impove vs competitors"
        
        tavily_response = ask_tavily(
            user_query= tavily_prompt
        )
        
        system_prompt = RECOMMENDATION_PROMPT
        
        user_prompt = f"""
Startup: 
{user_input}

Highest Risk Flag: 
{highest_risk_flag}

Risk Analysis:
{risk_analysis}

Search Results:
{chr(10).join([f"- URL: {r['url']}{chr(10)}  Content: {r['content']}" for r in tavily_response])}

Generate the JSON recommendation array now.

"""
        
        messages = [
            {
                "role":"system",
                "content":system_prompt
            },
            {
                "role":"user",
                "content":user_prompt
            }
        ]
        
        groq_response = text_call(
            prompt= messages
        )
        
        clean_response = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            groq_response.strip(),
            flags=re.IGNORECASE
        )
        
        data = json.loads(clean_response)
        
        workflow_state["recommendations"] = (
            data
        )
        workflow_state["pipeline_status"]["RecommendationAgent"] = (
            "success"
        )
        return workflow_state
    
if __name__ == "__main__":
    
    MOCK_STATE_RECOMMENDATION = {

        # ── INPUTS ──────────────────────────────────────────
        "user_input": "AI-powered tiffin delivery platform for college students",
        "pitch_deck_text"      : [],     # extracted PDF text chunks, [] if none

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
        "risk_analysis": """
    ## Feature Risks

    ### Feature: Weekly Tiffin Subscription
    Risk: Customer churn if meal quality or menu variety is inconsistent.
    Why: Students may switch providers when meals become repetitive or unreliable.
    Impact: High
    Mitigation: Introduce menu rotation, quality monitoring, and subscription feedback loops.

    ### Feature: Scheduled Meal Delivery
    Risk: Late or missed deliveries can reduce customer trust.
    Why: Students depend on predictable meal timing around classes and schedules.
    Impact: High
    Mitigation: Start with limited delivery zones, defined delivery windows, and operational tracking.

    ### Feature: Digital Payments
    Risk: Payment failures may interrupt subscription purchases.
    Why: Failed transactions can create friction during onboarding and renewal.
    Impact: Medium
    Mitigation: Support reliable payment flows and provide clear retry/failure handling.

    ## Highest Business Risk

    Risk: Customer retention and delivery reliability.

    Reason:
    The business depends on recurring subscriptions, so poor food consistency or unreliable delivery could increase churn and weaken unit economics.

    Mitigation:
    Validate retention through a small geographic pilot, monitor repeat orders and cancellations, and improve delivery operations before expanding.
        """,
        "startup_score": {
            "score": 68,
            "reasoning": (
                "The startup addresses a recurring student food-delivery need "
                "with a focused target segment, but customer retention and "
                "operational execution remain important concerns."
            ),
            "breakdown": {
                "market": 72,
                "mvp": 70,
                "tech": 68,
                "risk": 58
            },
            "highest_risk_flag": "risk"
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
    
    
    agent = RecommendationAgent()
    
    workflow_state = agent.run(
        MOCK_STATE_RECOMMENDATION.copy()
    )
    
    print(workflow_state["recommendations"])