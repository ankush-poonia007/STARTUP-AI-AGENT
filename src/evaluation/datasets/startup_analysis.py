"""
============================================================
BizRadar AI
Startup Analysis Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly avoids routing general startup analysis
requests to document retrieval.

Expected Routing
----------------
False
"""

from typing import Dict, List

CATEGORY = "Startup Analysis"
EXPECTED = False

IDEA_ANALYSIS = "Idea Analysis"
MARKET_ANALYSIS = "Market Analysis"
BUSINESS_MODEL = "Business Model"
GO_TO_MARKET = "Go To Market"
VALIDATION = "Validation"
CONVERSATIONAL = "Conversational"


def make_case(case_id: str, intent: str, difficulty: str,
              tags: List[str], query: str) -> Dict:
    return {
        "case_id": case_id,
        "category": CATEGORY,
        "intent": intent,
        "difficulty": difficulty,
        "tags": tags,
        "query": query,
        "expected": EXPECTED,
    }


STARTUP_ANALYSIS_CASES: List[Dict] = [

    # Idea Analysis (SA-001 → SA-005)
    make_case("SA-001", IDEA_ANALYSIS, "easy", ["startup"], "Analyze my startup idea."),
    make_case("SA-002", IDEA_ANALYSIS, "easy", ["startup"], "Evaluate this business idea."),
    make_case("SA-003", IDEA_ANALYSIS, "medium", ["startup"], "Is this startup worth building?"),
    make_case("SA-004", IDEA_ANALYSIS, "medium", ["startup"], "Review my SaaS concept."),
    make_case("SA-005", IDEA_ANALYSIS, "hard", ["startup"], "Give detailed feedback on my AI startup idea."),

    # Market Analysis (SA-006 → SA-009)
    make_case("SA-006", MARKET_ANALYSIS, "easy", ["market"], "Analyze the market potential."),
    make_case("SA-007", MARKET_ANALYSIS, "medium", ["market"], "Estimate the target market."),
    make_case("SA-008", MARKET_ANALYSIS, "medium", ["competition"], "Who are the competitors?"),
    make_case("SA-009", MARKET_ANALYSIS, "hard", ["industry"], "Evaluate the industry opportunity."),

    # Business Model (SA-010 → SA-013)
    make_case("SA-010", BUSINESS_MODEL, "easy", ["business-model"], "Suggest a business model."),
    make_case("SA-011", BUSINESS_MODEL, "medium", ["pricing"], "Recommend a pricing strategy."),
    make_case("SA-012", BUSINESS_MODEL, "medium", ["revenue"], "How can this startup generate revenue?"),
    make_case("SA-013", BUSINESS_MODEL, "hard", ["monetization"], "Evaluate the monetization potential."),

    # Go To Market (SA-014 → SA-017)
    make_case("SA-014", GO_TO_MARKET, "easy", ["gtm"], "Suggest a go-to-market strategy."),
    make_case("SA-015", GO_TO_MARKET, "medium", ["marketing"], "How should I launch this product?"),
    make_case("SA-016", GO_TO_MARKET, "medium", ["customers"], "Who should be my first customers?"),
    make_case("SA-017", GO_TO_MARKET, "hard", ["growth"], "Recommend an early growth strategy."),

    # Validation (SA-018 → SA-019)
    make_case("SA-018", VALIDATION, "medium", ["validation"], "How can I validate this idea?"),
    make_case("SA-019", VALIDATION, "hard", ["product-fit"], "How do I achieve product-market fit?"),

    # Conversational (SA-020)
    make_case("SA-020", CONVERSATIONAL, "medium", ["conversation"], "I have a startup idea. Can you analyze it?"),
]
