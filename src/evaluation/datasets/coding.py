"""
============================================================
BizRadar AI
Coding Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly avoids routing general programming
requests to document retrieval.

Expected Routing
----------------
False
"""

from typing import Dict, List

CATEGORY = "Coding"
EXPECTED = False

DEBUGGING = "Debugging"
CODE_GENERATION = "Code Generation"
ALGORITHMS = "Algorithms"
FRAMEWORKS = "Frameworks"
SYSTEM_DESIGN = "System Design"
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


CODING_CASES: List[Dict] = [

    # Debugging (CODE-001 → CODE-004)
    make_case("CODE-001", DEBUGGING, "easy",
              ["python","debug"], "Help me debug this Python code."),
    make_case("CODE-002", DEBUGGING, "medium",
              ["javascript","debug"], "Why is my JavaScript function failing?"),
    make_case("CODE-003", DEBUGGING, "medium",
              ["fastapi"], "Fix the error in my FastAPI application."),
    make_case("CODE-004", DEBUGGING, "hard",
              ["sql"], "Debug this SQL query."),

    # Code Generation (CODE-005 → CODE-008)
    make_case("CODE-005", CODE_GENERATION, "easy",
              ["python"], "Write a Python function to reverse a string."),
    make_case("CODE-006", CODE_GENERATION, "medium",
              ["api"], "Generate a REST API using FastAPI."),
    make_case("CODE-007", CODE_GENERATION, "medium",
              ["react"], "Create a React login component."),
    make_case("CODE-008", CODE_GENERATION, "hard",
              ["agent"], "Build an agentic AI workflow in Python."),

    # Algorithms (CODE-009 → CODE-012)
    make_case("CODE-009", ALGORITHMS, "easy",
              ["dsa"], "Explain binary search."),
    make_case("CODE-010", ALGORITHMS, "medium",
              ["graph"], "Implement Dijkstra's algorithm."),
    make_case("CODE-011", ALGORITHMS, "medium",
              ["dynamic-programming"], "Solve this dynamic programming problem."),
    make_case("CODE-012", ALGORITHMS, "hard",
              ["complexity"], "Optimize this algorithm."),

    # Frameworks (CODE-013 → CODE-016)
    make_case("CODE-013", FRAMEWORKS, "easy",
              ["django"], "Should I use Django or FastAPI?"),
    make_case("CODE-014", FRAMEWORKS, "medium",
              ["flask"], "How do I build APIs with Flask?"),
    make_case("CODE-015", FRAMEWORKS, "medium",
              ["react"], "How does React state management work?"),
    make_case("CODE-016", FRAMEWORKS, "hard",
              ["langchain"], "How do I use LangChain with Ollama?"),

    # System Design (CODE-017 → CODE-019)
    make_case("CODE-017", SYSTEM_DESIGN, "medium",
              ["architecture"], "Design a scalable chat application."),
    make_case("CODE-018", SYSTEM_DESIGN, "hard",
              ["distributed"], "Explain distributed system design."),
    make_case("CODE-019", SYSTEM_DESIGN, "hard",
              ["microservices"], "Design a microservices architecture."),

    # Conversational (CODE-020)
    make_case("CODE-020", CONVERSATIONAL, "easy",
              ["conversation"], "Can you help me write some code?"),
]
