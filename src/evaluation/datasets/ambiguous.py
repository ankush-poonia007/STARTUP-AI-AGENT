"""
============================================================
BizRadar AI
Ambiguous Benchmark Dataset
============================================================

Purpose
-------
Borderline routing cases used for qualitative analysis.
These cases are NOT scored because reasonable routing
strategies may disagree.

Expected Routing
----------------
None (analysis only)
"""

from typing import Dict, List

CATEGORY = "Ambiguous"

DOCUMENT_CONTEXT = "Document Context"
MIXED_REQUEST = "Mixed Request"
IMPLICIT_REFERENCE = "Implicit Reference"
FOLLOW_UP = "Follow Up"
EDGE_CASE = "Edge Case"


def make_case(case_id: str, intent: str, difficulty: str,
              tags: List[str], query: str) -> Dict:
    return {
        "case_id": case_id,
        "category": CATEGORY,
        "intent": intent,
        "difficulty": difficulty,
        "tags": tags,
        "query": query,
        "expected": None,
    }


AMBIGUOUS_CASES: List[Dict] = [

    # Document Context (AMB-001 → AMB-006)
    make_case("AMB-001", DOCUMENT_CONTEXT, "easy",
              ["context"], "Analyze my startup idea using the uploaded report if it's helpful."),
    make_case("AMB-002", DOCUMENT_CONTEXT, "medium",
              ["context"], "Recommend a strategy based on my uploaded documents."),
    make_case("AMB-003", DOCUMENT_CONTEXT, "medium",
              ["context"], "Use the uploaded report to improve your answer."),
    make_case("AMB-004", DOCUMENT_CONTEXT, "hard",
              ["context"], "Take my uploaded research into account when answering."),
    make_case("AMB-005", DOCUMENT_CONTEXT, "hard",
              ["context"], "If relevant, refer to the uploaded files."),
    make_case("AMB-006", DOCUMENT_CONTEXT, "hard",
              ["context"], "Use my documents only if necessary."),

    # Mixed Requests (AMB-007 → AMB-012)
    make_case("AMB-007", MIXED_REQUEST, "medium",
              ["mixed"], "Summarize the report and recommend an MVP."),
    make_case("AMB-008", MIXED_REQUEST, "medium",
              ["mixed"], "Compare the uploaded reports and suggest a business strategy."),
    make_case("AMB-009", MIXED_REQUEST, "hard",
              ["mixed"], "Extract the risks and tell me how to mitigate them."),
    make_case("AMB-010", MIXED_REQUEST, "hard",
              ["mixed"], "Read the report, then suggest improvements."),
    make_case("AMB-011", MIXED_REQUEST, "hard",
              ["mixed"], "What does the report say, and what should I do next?"),
    make_case("AMB-012", MIXED_REQUEST, "hard",
              ["mixed"], "Use the uploaded paper to answer and provide recommendations."),

    # Implicit References (AMB-013 → AMB-018)
    make_case("AMB-013", IMPLICIT_REFERENCE, "medium",
              ["implicit"], "Can you use it?"),
    make_case("AMB-014", IMPLICIT_REFERENCE, "medium",
              ["implicit"], "Does that mention security?"),
    make_case("AMB-015", IMPLICIT_REFERENCE, "hard",
              ["implicit"], "What does it recommend?"),
    make_case("AMB-016", IMPLICIT_REFERENCE, "hard",
              ["implicit"], "Is anything important missing?"),
    make_case("AMB-017", IMPLICIT_REFERENCE, "hard",
              ["implicit"], "Can you build on that?"),
    make_case("AMB-018", IMPLICIT_REFERENCE, "hard",
              ["implicit"], "Should we follow its advice?"),

    # Follow-up (AMB-019 → AMB-024)
    make_case("AMB-019", FOLLOW_UP, "medium",
              ["follow-up"], "Can you explain that further?"),
    make_case("AMB-020", FOLLOW_UP, "medium",
              ["follow-up"], "What about the second point?"),
    make_case("AMB-021", FOLLOW_UP, "hard",
              ["follow-up"], "Can you expand on it?"),
    make_case("AMB-022", FOLLOW_UP, "hard",
              ["follow-up"], "Does the same apply here?"),
    make_case("AMB-023", FOLLOW_UP, "hard",
              ["follow-up"], "What should I do next?"),
    make_case("AMB-024", FOLLOW_UP, "hard",
              ["follow-up"], "Can you clarify that?"),

    # Edge Cases (AMB-025 → AMB-030)
    make_case("AMB-025", EDGE_CASE, "hard",
              ["edge"], "Review everything."),
    make_case("AMB-026", EDGE_CASE, "hard",
              ["edge"], "Help me with this."),
    make_case("AMB-027", EDGE_CASE, "hard",
              ["edge"], "Can you analyze it?"),
    make_case("AMB-028", EDGE_CASE, "hard",
              ["edge"], "What do you think?"),
    make_case("AMB-029", EDGE_CASE, "hard",
              ["edge"], "Give me your opinion."),
    make_case("AMB-030", EDGE_CASE, "hard",
              ["edge"], "Let's continue from there."),
]
