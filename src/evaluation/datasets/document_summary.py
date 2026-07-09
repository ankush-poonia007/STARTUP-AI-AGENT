"""
============================================================
BizRadar AI
Document Summary Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly routes document-summary requests.

Every query in this dataset REQUIRES reading one or more
uploaded documents.

Expected Routing
----------------
True

Author
------
BizRadar AI
"""

from typing import Dict, List


# ============================================================
# CATEGORY CONSTANTS
# ============================================================

CATEGORY = "Document Summary"

EXPECTED = True


# ============================================================
# INTENT TYPES
# ============================================================

EXPLICIT_SUMMARY = "Explicit Summary"

NATURAL_LANGUAGE = "Natural Language"

SYNONYM = "Summary Synonym"

MULTI_DOCUMENT = "Multi Document"

CONVERSATIONAL = "Conversational"

IMPLICIT_REFERENCE = "Implicit Reference"

DOCUMENT_VARIATION = "Document Type Variation"


# ============================================================
# HELPER
# ============================================================

def make_case(
    case_id: str,
    intent: str,
    difficulty: str,
    tags: List[str],
    query: str,
) -> Dict:
    """
    Create one benchmark case.

    Every Document Summary benchmark expects
    the classifier to return True.
    """

    return {
        "case_id": case_id,
        "category": CATEGORY,
        "intent": intent,
        "difficulty": difficulty,
        "tags": tags,
        "query": query,
        "expected": EXPECTED,
    }


# ============================================================
# DATASET
# ============================================================

DOCUMENT_SUMMARY_CASES: List[Dict] = [

    # ========================================================
    # Explicit Summary (DS-001 → DS-008)
    # ========================================================

    make_case(
        "DS-001",
        EXPLICIT_SUMMARY,
        "easy",
        ["summary", "explicit", "pdf"],
        "Summarize the uploaded PDF.",
    ),

    make_case(
        "DS-002",
        EXPLICIT_SUMMARY,
        "easy",
        ["summary", "explicit", "report"],
        "Summarize the uploaded report.",
    ),

    make_case(
        "DS-003",
        EXPLICIT_SUMMARY,
        "easy",
        ["summary", "explicit", "document"],
        "Summarize the uploaded document.",
    ),

    make_case(
        "DS-004",
        EXPLICIT_SUMMARY,
        "easy",
        ["summary", "explicit", "file"],
        "Summarize the attached file.",
    ),

    make_case(
        "DS-005",
        EXPLICIT_SUMMARY,
        "medium",
        ["summary", "research-paper"],
        "Summarize the uploaded research paper.",
    ),

    make_case(
        "DS-006",
        EXPLICIT_SUMMARY,
        "medium",
        ["summary", "proposal"],
        "Summarize the uploaded proposal.",
    ),

    make_case(
        "DS-007",
        EXPLICIT_SUMMARY,
        "medium",
        ["summary", "whitepaper"],
        "Summarize the uploaded whitepaper.",
    ),

    make_case(
        "DS-008",
        EXPLICIT_SUMMARY,
        "medium",
        ["summary", "pitch-deck"],
        "Summarize the uploaded pitch deck.",
    ),

    # ========================================================
    # Natural Language (DS-009 → DS-014)
    # ========================================================

    make_case(
        "DS-009",
        NATURAL_LANGUAGE,
        "easy",
        ["natural-language"],
        "What is this report about?",
    ),

    make_case(
        "DS-010",
        NATURAL_LANGUAGE,
        "easy",
        ["natural-language"],
        "Can you tell me what this document discusses?",
    ),

    make_case(
        "DS-011",
        NATURAL_LANGUAGE,
        "medium",
        ["natural-language"],
        "Walk me through the uploaded report.",
    ),

    make_case(
        "DS-012",
        NATURAL_LANGUAGE,
        "medium",
        ["natural-language"],
        "Explain what this PDF says.",
    ),

    make_case(
        "DS-013",
        NATURAL_LANGUAGE,
        "medium",
        ["natural-language"],
        "Tell me the main takeaway from the uploaded paper.",
    ),

    make_case(
        "DS-014",
        NATURAL_LANGUAGE,
        "hard",
        ["natural-language"],
        "Can you explain what I uploaded?",
    ),

    # ========================================================
    # Summary Synonyms (DS-015 → DS-020)
    # ========================================================

    make_case(
        "DS-015",
        SYNONYM,
        "easy",
        ["overview"],
        "Give me an overview of the uploaded report.",
    ),

    make_case(
        "DS-016",
        SYNONYM,
        "easy",
        ["highlights"],
        "What are the highlights of the uploaded document?",
    ),

    make_case(
        "DS-017",
        SYNONYM,
        "medium",
        ["key-points"],
        "List the key points from the uploaded report.",
    ),

    make_case(
        "DS-018",
        SYNONYM,
        "medium",
        ["executive-summary"],
        "Prepare an executive summary of the uploaded proposal.",
    ),

    make_case(
        "DS-019",
        SYNONYM,
        "medium",
        ["tldr"],
        "Give me a TL;DR of the uploaded document.",
    ),

    make_case(
        "DS-020",
        SYNONYM,
        "hard",
        ["abstract"],
        "Provide an abstract of the uploaded research paper.",
    ),

    # ========================================================
    # Multi Document (DS-021 → DS-024)
    # ========================================================

    make_case(
        "DS-021",
        MULTI_DOCUMENT,
        "easy",
        ["multiple-documents"],
        "Summarize all uploaded PDFs.",
    ),

    make_case(
        "DS-022",
        MULTI_DOCUMENT,
        "medium",
        ["multiple-documents"],
        "Summarize each uploaded report separately.",
    ),

    make_case(
        "DS-023",
        MULTI_DOCUMENT,
        "medium",
        ["multiple-documents"],
        "Summarize every uploaded document.",
    ),

    make_case(
        "DS-024",
        MULTI_DOCUMENT,
        "hard",
        ["multiple-documents"],
        "Create summaries for both uploaded files.",
    ),

    # ========================================================
    # Conversational (DS-025 → DS-030)
    # ========================================================

    make_case(
        "DS-025",
        CONVERSATIONAL,
        "easy",
        ["conversation"],
        "Can you summarize it?",
    ),

    make_case(
        "DS-026",
        CONVERSATIONAL,
        "easy",
        ["conversation"],
        "Please summarize this.",
    ),

    make_case(
        "DS-027",
        CONVERSATIONAL,
        "medium",
        ["conversation"],
        "Would you summarize that document for me?",
    ),

    make_case(
        "DS-028",
        CONVERSATIONAL,
        "medium",
        ["conversation"],
        "I uploaded something earlier. Can you summarize it?",
    ),

    make_case(
        "DS-029",
        CONVERSATIONAL,
        "hard",
        ["conversation"],
        "Could you go through the report?",
    ),

    make_case(
        "DS-030",
        CONVERSATIONAL,
        "hard",
        ["conversation"],
        "Can you tell me what it says?",
    ),

    # ========================================================
    # Implicit References (DS-031 → DS-035)
    # ========================================================

    make_case(
        "DS-031",
        IMPLICIT_REFERENCE,
        "easy",
        ["implicit"],
        "Read it.",
    ),

    make_case(
        "DS-032",
        IMPLICIT_REFERENCE,
        "easy",
        ["implicit"],
        "Review it.",
    ),

    make_case(
        "DS-033",
        IMPLICIT_REFERENCE,
        "medium",
        ["implicit"],
        "Explain it.",
    ),

    make_case(
        "DS-034",
        IMPLICIT_REFERENCE,
        "medium",
        ["implicit"],
        "Go through it.",
    ),

    make_case(
        "DS-035",
        IMPLICIT_REFERENCE,
        "hard",
        ["implicit"],
        "Summarize it.",
    ),

    # ========================================================
    # Document Type Variations (DS-036 → DS-040)
    # ========================================================

    make_case(
        "DS-036",
        DOCUMENT_VARIATION,
        "easy",
        ["contract"],
        "Summarize the uploaded contract.",
    ),

    make_case(
        "DS-037",
        DOCUMENT_VARIATION,
        "easy",
        ["invoice"],
        "Summarize the uploaded invoice.",
    ),

    make_case(
        "DS-038",
        DOCUMENT_VARIATION,
        "medium",
        ["thesis"],
        "Summarize the uploaded thesis.",
    ),

    make_case(
        "DS-039",
        DOCUMENT_VARIATION,
        "medium",
        ["resume"],
        "Summarize the uploaded resume.",
    ),

    make_case(
        "DS-040",
        DOCUMENT_VARIATION,
        "hard",
        ["financial-statement"],
        "Summarize the uploaded financial statement.",
    ),

]