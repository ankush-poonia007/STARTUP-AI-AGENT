"""
============================================================
BizRadar AI

Startup Document Queries Benchmark

Purpose
-------
Evaluates whether the document-routing classifier correctly
recognizes BizRadar-specific startup documents while
distinguishing them from startup advice, content generation,
and general knowledge requests.

This benchmark specifically validates:

• Startup document vocabulary
• Explicit document references
• Small set of implicit document references
============================================================
"""

STARTUP_DOCUMENT_CASES = [

# ==========================================================
# TRUE CASES (Explicit Document References)
# ==========================================================

{
    "id": "SD-001",
    "query": "Summarize the uploaded pitch deck.",
    "expected": True,
    "intent": "Document Summary",
    "difficulty": "Easy",
},

{
    "id": "SD-002",
    "query": "What problem statement is described in the uploaded business plan?",
    "expected": True,
    "intent": "Document QA",
    "difficulty": "Easy",
},

{
    "id": "SD-003",
    "query": "Extract the valuation from the uploaded term sheet.",
    "expected": True,
    "intent": "Information Extraction",
    "difficulty": "Medium",
},

{
    "id": "SD-004",
    "query": "Compare the uploaded investor decks.",
    "expected": True,
    "intent": "Document Comparison",
    "difficulty": "Medium",
},

{
    "id": "SD-005",
    "query": "Summarize the uploaded market research report.",
    "expected": True,
    "intent": "Document Summary",
    "difficulty": "Easy",
},

{
    "id": "SD-006",
    "query": "What customer personas are described in the uploaded user research document?",
    "expected": True,
    "intent": "Document QA",
    "difficulty": "Medium",
},

{
    "id": "SD-007",
    "query": "Explain the go-to-market strategy mentioned in the uploaded presentation.",
    "expected": True,
    "intent": "Document QA",
    "difficulty": "Medium",
},

{
    "id": "SD-008",
    "query": "What does the uploaded financial model predict?",
    "expected": True,
    "intent": "Financial QA",
    "difficulty": "Medium",
},

{
    "id": "SD-009",
    "query": "Extract all action items from the uploaded PRD.",
    "expected": True,
    "intent": "Information Extraction",
    "difficulty": "Hard",
},

{
    "id": "SD-010",
    "query": "Compare the uploaded PRD and technical design document.",
    "expected": True,
    "intent": "Document Comparison",
    "difficulty": "Hard",
},

# ==========================================================
# TRUE CASES (Implicit Document References)
# ==========================================================

{
    "id": "SD-011",
    "query": "What does the methodology section describe?",
    "expected": True,
    "intent": "Implicit Document QA",
    "difficulty": "Medium",
},

{
    "id": "SD-012",
    "query": "Compare the introduction and conclusion.",
    "expected": True,
    "intent": "Implicit Document Comparison",
    "difficulty": "Hard",
},

# ==========================================================
# FALSE CASES
# ==========================================================

{
    "id": "SD-013",
    "query": "Create a pitch deck.",
    "expected": False,
    "intent": "Content Generation",
    "difficulty": "Easy",
},

{
    "id": "SD-014",
    "query": "Write a business plan.",
    "expected": False,
    "intent": "Content Generation",
    "difficulty": "Easy",
},

{
    "id": "SD-015",
    "query": "Draft a term sheet.",
    "expected": False,
    "intent": "Content Generation",
    "difficulty": "Medium",
},

{
    "id": "SD-016",
    "query": "Create an investor deck.",
    "expected": False,
    "intent": "Content Generation",
    "difficulty": "Medium",
},

{
    "id": "SD-017",
    "query": "Design a go-to-market strategy.",
    "expected": False,
    "intent": "Startup Advice",
    "difficulty": "Medium",
},

{
    "id": "SD-018",
    "query": "Build a financial model.",
    "expected": False,
    "intent": "Content Generation",
    "difficulty": "Medium",
},

{
    "id": "SD-019",
    "query": "Generate customer personas for my startup.",
    "expected": False,
    "intent": "Startup Advice",
    "difficulty": "Medium",
},

{
    "id": "SD-020",
    "query": "Perform a competitive analysis for my startup.",
    "expected": False,
    "intent": "Startup Advice",
    "difficulty": "Medium",
},

{
    "id": "SD-021",
    "query": "What is a methodology?",
    "expected": False,
    "intent": "General Knowledge",
    "difficulty": "Easy",
},

{
    "id": "SD-022",
    "query": "What is a term sheet?",
    "expected": False,
    "intent": "General Knowledge",
    "difficulty": "Easy",
},

{
    "id": "SD-023",
    "query": "Explain what a financial model is.",
    "expected": False,
    "intent": "General Knowledge",
    "difficulty": "Easy",
},

{
    "id": "SD-024",
    "query": "What is a pitch deck?",
    "expected": False,
    "intent": "General Knowledge",
    "difficulty": "Easy",
},

]