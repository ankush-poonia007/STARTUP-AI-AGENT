"""
============================================================
BizRadar AI
General Knowledge Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly avoids routing general knowledge
questions to document retrieval.

Expected Routing
----------------
False
"""

from typing import Dict, List

CATEGORY = "General Knowledge"
EXPECTED = False

SCIENCE = "Science"
TECHNOLOGY = "Technology"
HISTORY = "History"
MATHEMATICS = "Mathematics"
BUSINESS = "Business"
AI = "Artificial Intelligence"
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


GENERAL_KNOWLEDGE_CASES: List[Dict] = [

    # Science (GK-001 → GK-003)
    make_case("GK-001", SCIENCE, "easy",
              ["science"], "Why is the sky blue?"),
    make_case("GK-002", SCIENCE, "medium",
              ["physics"], "Explain quantum entanglement."),
    make_case("GK-003", SCIENCE, "hard",
              ["biology"], "How does CRISPR gene editing work?"),

    # Technology (GK-004 → GK-006)
    make_case("GK-004", TECHNOLOGY, "easy",
              ["internet"], "How does the internet work?"),
    make_case("GK-005", TECHNOLOGY, "medium",
              ["cloud"], "What is cloud computing?"),
    make_case("GK-006", TECHNOLOGY, "hard",
              ["blockchain"], "Explain blockchain consensus mechanisms."),

    # History (GK-007 → GK-009)
    make_case("GK-007", HISTORY, "easy",
              ["history"], "Who discovered America?"),
    make_case("GK-008", HISTORY, "medium",
              ["world-war"], "What caused World War II?"),
    make_case("GK-009", HISTORY, "hard",
              ["industrial"], "Explain the Industrial Revolution."),

    # Mathematics (GK-010 → GK-012)
    make_case("GK-010", MATHEMATICS, "easy",
              ["math"], "What is the Pythagorean theorem?"),
    make_case("GK-011", MATHEMATICS, "medium",
              ["calculus"], "Explain derivatives."),
    make_case("GK-012", MATHEMATICS, "hard",
              ["linear-algebra"], "What are eigenvalues and eigenvectors?"),

    # Business (GK-013 → GK-016)
    make_case("GK-013", BUSINESS, "easy",
              ["business"], "What is a business model?"),
    make_case("GK-014", BUSINESS, "medium",
              ["marketing"], "Explain SWOT analysis."),
    make_case("GK-015", BUSINESS, "medium",
              ["finance"], "What is EBITDA?"),
    make_case("GK-016", BUSINESS, "hard",
              ["economics"], "How do network effects create competitive advantages?"),

    # Artificial Intelligence (GK-017 → GK-019)
    make_case("GK-017", AI, "easy",
              ["ai"], "What is machine learning?"),
    make_case("GK-018", AI, "medium",
              ["llm"], "How do large language models work?"),
    make_case("GK-019", AI, "hard",
              ["rag"], "Explain Retrieval-Augmented Generation."),

    # Conversational (GK-020)
    make_case("GK-020", CONVERSATIONAL, "easy",
              ["conversation"], "Can you explain this concept to me?"),
]
