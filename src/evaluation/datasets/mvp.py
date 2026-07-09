"""
============================================================
BizRadar AI
MVP Recommendation Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly avoids routing MVP planning requests
to document retrieval.

Expected Routing
----------------
False
"""

from typing import Dict, List

CATEGORY = "MVP"
EXPECTED = False

FEATURES = "Feature Planning"
PRIORITIZATION = "Prioritization"
ROADMAP = "Roadmap"
VALIDATION = "Validation"
TECH_DECISIONS = "Technical Decisions"
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


MVP_CASES: List[Dict] = [

    # Feature Planning (MVP-001 → MVP-005)
    make_case("MVP-001", FEATURES, "easy",
              ["mvp","features"], "Suggest an MVP for my startup."),
    make_case("MVP-002", FEATURES, "easy",
              ["mvp","features"], "What should my first version include?"),
    make_case("MVP-003", FEATURES, "medium",
              ["mvp","scope"], "Help me define the MVP scope."),
    make_case("MVP-004", FEATURES, "medium",
              ["mvp","launch"], "Which features should I launch first?"),
    make_case("MVP-005", FEATURES, "hard",
              ["mvp","lean"], "Design a lean MVP for my SaaS idea."),

    # Prioritization (MVP-006 → MVP-009)
    make_case("MVP-006", PRIORITIZATION, "easy",
              ["priority"], "Prioritize the core features."),
    make_case("MVP-007", PRIORITIZATION, "medium",
              ["priority"], "Which features can wait for later releases?"),
    make_case("MVP-008", PRIORITIZATION, "medium",
              ["priority"], "Identify the must-have functionality."),
    make_case("MVP-009", PRIORITIZATION, "hard",
              ["priority"], "Rank the proposed features by business value."),

    # Roadmap (MVP-010 → MVP-013)
    make_case("MVP-010", ROADMAP, "easy",
              ["roadmap"], "Create an MVP roadmap."),
    make_case("MVP-011", ROADMAP, "medium",
              ["roadmap"], "Plan the first three development milestones."),
    make_case("MVP-012", ROADMAP, "medium",
              ["roadmap"], "Suggest a phased rollout plan."),
    make_case("MVP-013", ROADMAP, "hard",
              ["roadmap"], "Build a six-month MVP roadmap."),

    # Validation (MVP-014 → MVP-017)
    make_case("MVP-014", VALIDATION, "easy",
              ["validation"], "How should I validate the MVP?"),
    make_case("MVP-015", VALIDATION, "medium",
              ["validation"], "What experiments should I run before launch?"),
    make_case("MVP-016", VALIDATION, "medium",
              ["validation"], "Suggest MVP success metrics."),
    make_case("MVP-017", VALIDATION, "hard",
              ["validation"], "How can I test product-market fit with an MVP?"),

    # Technical Decisions (MVP-018 → MVP-019)
    make_case("MVP-018", TECH_DECISIONS, "medium",
              ["tech"], "Recommend a tech stack for the MVP."),
    make_case("MVP-019", TECH_DECISIONS, "hard",
              ["architecture"], "Suggest the best architecture for an MVP."),

    # Conversational (MVP-020)
    make_case("MVP-020", CONVERSATIONAL, "medium",
              ["conversation"], "I have an idea. Can you help me design an MVP?"),
]
