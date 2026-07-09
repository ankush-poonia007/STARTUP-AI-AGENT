"""
============================================================
BizRadar AI
Information Extraction Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly routes information extraction requests
that require reading uploaded documents.

Expected Routing
----------------
True
"""

from typing import Dict, List

CATEGORY = "Information Extraction"
EXPECTED = True

LIST_EXTRACTION = "List Extraction"
ENTITY_EXTRACTION = "Entity Extraction"
NUMERIC_EXTRACTION = "Numeric Extraction"
DATE_EXTRACTION = "Date Extraction"
TABLE_EXTRACTION = "Table Extraction"
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


INFORMATION_EXTRACTION_CASES: List[Dict] = [

    # List Extraction (IE-001 → IE-005)
    make_case("IE-001", LIST_EXTRACTION, "easy", ["extract","bullet"], "Extract all key findings from the uploaded report."),
    make_case("IE-002", LIST_EXTRACTION, "easy", ["extract","action-items"], "Extract all action items from the document."),
    make_case("IE-003", LIST_EXTRACTION, "medium", ["extract","recommendations"], "List every recommendation in the uploaded paper."),
    make_case("IE-004", LIST_EXTRACTION, "medium", ["extract","risks"], "Extract all risks mentioned in the report."),
    make_case("IE-005", LIST_EXTRACTION, "hard", ["extract","limitations"], "Extract every limitation discussed in the document."),

    # Entity Extraction (IE-006 → IE-009)
    make_case("IE-006", ENTITY_EXTRACTION, "easy", ["companies"], "Extract all company names."),
    make_case("IE-007", ENTITY_EXTRACTION, "medium", ["people"], "Extract every person mentioned in the report."),
    make_case("IE-008", ENTITY_EXTRACTION, "medium", ["organizations"], "Extract all organizations referenced."),
    make_case("IE-009", ENTITY_EXTRACTION, "hard", ["products"], "Extract all product names from the uploaded document."),

    # Numeric Extraction (IE-010 → IE-013)
    make_case("IE-010", NUMERIC_EXTRACTION, "easy", ["numbers"], "Extract all percentages from the report."),
    make_case("IE-011", NUMERIC_EXTRACTION, "medium", ["financial"], "Extract every financial metric mentioned."),
    make_case("IE-012", NUMERIC_EXTRACTION, "medium", ["statistics"], "List all statistics from the uploaded paper."),
    make_case("IE-013", NUMERIC_EXTRACTION, "hard", ["market-size"], "Extract every market size estimate in the report."),

    # Date Extraction (IE-014 → IE-016)
    make_case("IE-014", DATE_EXTRACTION, "easy", ["dates"], "Extract all dates from the document."),
    make_case("IE-015", DATE_EXTRACTION, "medium", ["timeline"], "Extract the project timeline."),
    make_case("IE-016", DATE_EXTRACTION, "hard", ["deadlines"], "List every deadline mentioned in the uploaded report."),

    # Table Extraction (IE-017 → IE-018)
    make_case("IE-017", TABLE_EXTRACTION, "medium", ["tables"], "Extract the data from Table 1."),
    make_case("IE-018", TABLE_EXTRACTION, "hard", ["figures"], "Extract all values shown in Figure 2."),

    # Multi Document (IE-019)
    make_case("IE-019", MULTI_DOCUMENT, "hard", ["multi-document"], "Extract the common recommendations from all uploaded reports."),

    # Conversational (IE-020)
    make_case("IE-020", CONVERSATIONAL, "medium", ["conversation"], "Can you pull out all the important numbers from the report I uploaded?"),
]
