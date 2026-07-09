"""
============================================================
BizRadar AI
Document Comparison Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly routes comparison requests that
require reading two or more uploaded documents.

Expected Routing
----------------
True
"""

from typing import Dict, List

CATEGORY = "Document Comparison"
EXPECTED = True

DIRECT_COMPARISON = "Direct Comparison"
SIMILARITIES = "Similarity Analysis"
DIFFERENCES = "Difference Analysis"
SECTION_COMPARISON = "Section Comparison"
METRIC_COMPARISON = "Metric Comparison"
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


DOCUMENT_COMPARISON_CASES: List[Dict] = [

    # Direct Comparison (DC-001 → DC-005)
    make_case("DC-001", DIRECT_COMPARISON, "easy",
              ["compare"], "Compare the two uploaded reports."),
    make_case("DC-002", DIRECT_COMPARISON, "easy",
              ["compare"], "Compare both uploaded PDFs."),
    make_case("DC-003", DIRECT_COMPARISON, "medium",
              ["compare"], "Compare the uploaded research papers."),
    make_case("DC-004", DIRECT_COMPARISON, "medium",
              ["compare"], "Compare all uploaded documents."),
    make_case("DC-005", DIRECT_COMPARISON, "hard",
              ["compare"], "Compare the findings from every uploaded report."),

    # Similarities (DC-006 → DC-009)
    make_case("DC-006", SIMILARITIES, "easy",
              ["similarities"], "What do both reports have in common?"),
    make_case("DC-007", SIMILARITIES, "medium",
              ["similarities"], "Find the common recommendations across the documents."),
    make_case("DC-008", SIMILARITIES, "medium",
              ["similarities"], "Which topics appear in every uploaded report?"),
    make_case("DC-009", SIMILARITIES, "hard",
              ["similarities"], "Compare the shared assumptions in the uploaded papers."),

    # Differences (DC-010 → DC-013)
    make_case("DC-010", DIFFERENCES, "easy",
              ["differences"], "How do the conclusions differ?"),
    make_case("DC-011", DIFFERENCES, "medium",
              ["differences"], "What are the major differences between the reports?"),
    make_case("DC-012", DIFFERENCES, "medium",
              ["differences"], "Which risks are unique to each document?"),
    make_case("DC-013", DIFFERENCES, "hard",
              ["differences"], "Compare the recommendations made in both reports."),

    # Section Comparison (DC-014 → DC-016)
    make_case("DC-014", SECTION_COMPARISON, "medium",
              ["sections"], "Compare the executive summaries."),
    make_case("DC-015", SECTION_COMPARISON, "hard",
              ["sections"], "Compare the methodology sections."),
    make_case("DC-016", SECTION_COMPARISON, "hard",
              ["sections"], "How do the conclusion sections differ?"),

    # Metric Comparison (DC-017 → DC-019)
    make_case("DC-017", METRIC_COMPARISON, "medium",
              ["metrics"], "Compare the market growth projections."),
    make_case("DC-018", METRIC_COMPARISON, "hard",
              ["metrics"], "Which report predicts the highest CAGR?"),
    make_case("DC-019", METRIC_COMPARISON, "hard",
              ["metrics"], "Compare the financial projections across the reports."),

    # Conversational (DC-020)
    make_case("DC-020", CONVERSATIONAL, "medium",
              ["conversation"], "I uploaded two reports. Can you compare them?"),
]
