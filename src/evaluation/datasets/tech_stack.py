"""
============================================================
BizRadar AI
Tech Stack Recommendation Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly avoids routing technology recommendation
requests to document retrieval.

Expected Routing
----------------
False
"""

from typing import Dict, List

CATEGORY = "Tech Stack"
EXPECTED = False

FRONTEND = "Frontend"
BACKEND = "Backend"
DATABASE = "Database"
CLOUD = "Cloud"
ARCHITECTURE = "Architecture"
AI_STACK = "AI Stack"
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


TECH_STACK_CASES: List[Dict] = [

    # Frontend (TS-001 → TS-003)
    make_case("TS-001", FRONTEND, "easy",
              ["frontend"], "Suggest a frontend framework for my SaaS."),
    make_case("TS-002", FRONTEND, "medium",
              ["frontend"], "Should I use React or Vue?"),
    make_case("TS-003", FRONTEND, "hard",
              ["frontend"], "Recommend a modern frontend stack for scalability."),

    # Backend (TS-004 → TS-007)
    make_case("TS-004", BACKEND, "easy",
              ["backend"], "Recommend a backend framework."),
    make_case("TS-005", BACKEND, "medium",
              ["backend"], "Should I use FastAPI or Express?"),
    make_case("TS-006", BACKEND, "medium",
              ["backend"], "Which backend language should I choose?"),
    make_case("TS-007", BACKEND, "hard",
              ["backend"], "Design a scalable backend stack."),

    # Database (TS-008 → TS-011)
    make_case("TS-008", DATABASE, "easy",
              ["database"], "Recommend a database for my application."),
    make_case("TS-009", DATABASE, "medium",
              ["database"], "Should I choose PostgreSQL or MongoDB?"),
    make_case("TS-010", DATABASE, "medium",
              ["database"], "Which database scales better?"),
    make_case("TS-011", DATABASE, "hard",
              ["database"], "Suggest a persistence strategy."),

    # Cloud (TS-012 → TS-015)
    make_case("TS-012", CLOUD, "easy",
              ["cloud"], "Which cloud platform should I use?"),
    make_case("TS-013", CLOUD, "medium",
              ["cloud"], "AWS or Azure for a startup?"),
    make_case("TS-014", CLOUD, "medium",
              ["deployment"], "Recommend a deployment platform."),
    make_case("TS-015", CLOUD, "hard",
              ["infrastructure"], "Suggest a cloud architecture for growth."),

    # Architecture (TS-016 → TS-018)
    make_case("TS-016", ARCHITECTURE, "medium",
              ["architecture"], "Monolith or microservices?"),
    make_case("TS-017", ARCHITECTURE, "hard",
              ["architecture"], "Recommend a scalable software architecture."),
    make_case("TS-018", AI_STACK, "hard",
              ["ai"], "Suggest the best AI stack for an agentic application."),

    # Conversational (TS-019 → TS-020)
    make_case("TS-019", CONVERSATIONAL, "easy",
              ["conversation"], "Can you recommend a tech stack for my idea?"),
    make_case("TS-020", CONVERSATIONAL, "medium",
              ["conversation"], "I'm building a startup. What technologies should I use?"),
]
