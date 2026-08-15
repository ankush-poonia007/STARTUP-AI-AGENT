"""
Question:

File        : agents/pdf_generator_agent.py
Triggered By: pdf_request — ON-DEMAND ONLY
Tools       : pdf_tool.py
Input       : workflow_state["final_report"]
Output      : workflow_state["pdf_path"]

Output Format:
    workflow_state["pdf_path"] → str
        Absolute file path to generated PDF.
        "" (empty string) if not requested or generation failed.
        Example: "data/outputs/cofoundr_report_20260714.pdf"

PDF Rules:
- Text response ALWAYS shown in chat — PDF is optional
- PDF generated ONLY on explicit user request
- Qualifies for PDF: full_analysis, partial_idea outputs only
- Does NOT qualify: general_chat, idea_exploration outputs
- Auto-cleanup of unrequested PDFs → Phase 6 (frontend concern)

Responsibilities:
- Convert final_report markdown to professionally formatted PDF
- Apply clean formatting via ReportLab
- Return absolute download file path
- Triggered ONLY when user explicitly requests PDF

"""

from src.core.decorators import (
    log_execution,
    track_timing,
    retry_on_failure,
    handle_errors
)
from src.tools.pdf_tool import write_pdf

class PDFGeneratorAgent:
    
    @log_execution
    @track_timing
    @retry_on_failure
    @handle_errors
    def run(self, workflow_state:dict)->dict:
        
        final_report = workflow_state["final_report"]
        
        if not final_report:
            workflow_state["pipeline_status"]["PDFGeneratorAgent"] = (
                "skipped"
            )
            return workflow_state
        
        file_path = write_pdf(
            content= final_report
        )
        
        workflow_state["pdf_path"] = (
            file_path
        )
        
        workflow_state["pipeline_status"]["PDFGeneratorAgent"] = (
            "success"
        )
        
        return workflow_state
        
if __name__ == "__main__":
    
    from tests.mock_workflow_state import MOCK_STATE_FULL
    
    workflow_state = MOCK_STATE_FULL.copy()
    
    workflow_state["final_report"] = """
# Startup Analysis Report

## 1. Market Overview
Personalized and subscription-based food delivery models are gaining attention in the food-delivery industry. In addition, student-focused meal delivery services are exploring subscription models, healthier meal options, and personalized food experiences.
**Sources:**
* https://foodtech.folio3.com/blog/top-20-food-delivery-trends
* https://example.com/student-food-delivery-trends
---

## 2. MVP Recommendations

### Core MVP Features
* **Student Registration & Preference System:** Student registration and preference collection.
* **Meal Selection & Recommendations:** Weekly meal-plan selection and personalized meal recommendations.
* **Subscription Management:** Tiffin subscription management.
* **Order Tracking:** Order and delivery tracking.
* **Feedback Mechanism:** Meal feedback collection.
* **Partnerships:** Local food-provider partnerships.
---

## 3. Tech Stack
* **Frontend:** React
* **Backend:** FastAPI
* **Database:** PostgreSQL
* **AI:** Python-based recommendation service
* **Deployment:** Docker
---

## 4. Risk Analysis
1. **Customer Acquisition Risk:** Students may be unwilling to switch from existing food-delivery services.
2. **Operational Risk:** Maintaining consistent food quality and delivery times may be difficult.
3. **Unit Economics Risk:** Low student budgets may make delivery costs difficult to absorb.
4. **Retention Risk:** Students may cancel subscriptions if meal variety is insufficient.
---

## 5. Startup Score
* **Overall Score:** 78
* **Highest Risk Flag:** Feasibility
* **Reasoning:** The concept addresses a practical problem with a clearly defined target audience, but operational feasibility and willingness to pay require further validation.

### Score Breakdown
| Dimension | Score |
| :--- | :--- |
| **Product** | 82 |
| **Market** | 80 |
| **Business Model** | 76 |
| **Scalability** | 74 |
| **Feasibility** | 70 |
---

## 6. Improvement Recommendations
1. **Validate student willingness to pay through a small campus pilot.**
   * **Reason:** Pricing and demand are critical assumptions.
   * **Source:** https://example.com/student-food-delivery-trends
2. **Start with a limited weekly subscription plan before expanding into on-demand delivery.**
   * **Reason:** A limited subscription model can simplify initial operations.
   * **Source:** https://example.com/subscription-food-models
---

## 7. Pitch Deck Insights
*Note: Direct pitch deck text was not provided in the available workflow data. The following insights are structured from the supplied workflow data.*

### Concept
A personalized, AI-powered tiffin subscription service designed specifically for college students.
### Target Customer
College students.

### Value Proposition
Students receive convenient and affordable meals tailored to their food preferences and dietary requirements.

### Business Model
Weekly and monthly meal subscriptions with optional individual meal purchases.

### Differentiators
* Student-focused pricing
* Personalized meal recommendations
* Subscription convenience
---

## 8. Strategic Summary
The proposed business concept addresses student meal needs through an AI-powered, personalized tiffin delivery subscription service. Current market trends indicate growing interest in subscription models, personalization, and student-centric meal solutions. While the core product and market alignment show solid potential, primary challenges center around operational feasibility, customer acquisition, unit economics, and subscription retention. Operational validation—specifically testing student willingness to pay via campus pilots and streamlining early service using limited weekly plans—serves as the primary path forward before expanding capabilities.
    """
    
    agent = PDFGeneratorAgent()
    
    workflow_state = agent.run(
        workflow_state.copy()
    )
    
    print(workflow_state["pdf_path"])