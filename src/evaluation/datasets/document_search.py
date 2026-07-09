"""
============================================================
BizRadar AI
Document Search Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly routes search-style requests that
require locating information inside uploaded documents.

Expected Routing
----------------
True
"""

from typing import Dict, List

CATEGORY = "Document Search"
EXPECTED = True

KEYWORD_SEARCH = "Keyword Search"
SECTION_SEARCH = "Section Search"
ENTITY_SEARCH = "Entity Search"
PAGE_LOCATION = "Page or Location"
MULTI_DOCUMENT = "Multi Document"
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


DOCUMENT_SEARCH_CASES: List[Dict] = [

    # Keyword Search (DSR-001 → DSR-005)
    make_case("DSR-001", KEYWORD_SEARCH, "easy",
              ["keyword"], "Find every mention of AI in the uploaded report."),
    make_case("DSR-002", KEYWORD_SEARCH, "easy",
              ["keyword"], "Search the document for revenue."),
    make_case("DSR-003", KEYWORD_SEARCH, "medium",
              ["keyword"], "Locate all references to cybersecurity."),
    make_case("DSR-004", KEYWORD_SEARCH, "medium",
              ["keyword"], "Find where cloud computing is discussed."),
    make_case("DSR-005", KEYWORD_SEARCH, "hard",
              ["keyword"], "Search the uploaded paper for quantum encryption."),

    # Section Search (DSR-006 → DSR-009)
    make_case("DSR-006", SECTION_SEARCH, "easy",
              ["section"], "Locate the executive summary."),
    make_case("DSR-007", SECTION_SEARCH, "medium",
              ["section"], "Find the methodology section."),
    make_case("DSR-008", SECTION_SEARCH, "medium",
              ["section"], "Show me the conclusion section."),
    make_case("DSR-009", SECTION_SEARCH, "hard",
              ["section"], "Locate the limitations section."),

    # Entity Search (DSR-010 → DSR-012)
    make_case("DSR-010", ENTITY_SEARCH, "easy",
              ["entity"], "Find every company mentioned in the report."),
    make_case("DSR-011", ENTITY_SEARCH, "medium",
              ["entity"], "Locate all people referenced in the document."),
    make_case("DSR-012", ENTITY_SEARCH, "hard",
              ["entity"], "Find every organization cited in the uploaded paper."),

    # Page / Location (DSR-013 → DSR-015)
    make_case("DSR-013", PAGE_LOCATION, "medium",
              ["page"], "Which page discusses market growth?"),
    make_case("DSR-014", PAGE_LOCATION, "medium",
              ["location"], "Where does the report discuss implementation?"),
    make_case("DSR-015", PAGE_LOCATION, "hard",
              ["page"], "On which page are future recommendations listed?"),

    # Multi Document (DSR-016 → DSR-018)
    make_case("DSR-016", MULTI_DOCUMENT, "medium",
              ["multi-document"], "Search both uploaded reports for GDPR."),
    make_case("DSR-017", MULTI_DOCUMENT, "hard",
              ["multi-document"], "Find common topics across the uploaded documents."),
    make_case("DSR-018", MULTI_DOCUMENT, "hard",
              ["multi-document"], "Locate every mention of AI across all uploaded PDFs."),

    # Conversational (DSR-019 → DSR-020)
    make_case("DSR-019", CONVERSATIONAL, "medium",
              ["conversation"], "Can you find where it talks about pricing?"),
    make_case("DSR-020", CONVERSATIONAL, "hard",
              ["conversation", "pronoun"], "I uploaded a report earlier. Find the section about risks."),
]
