# ============================================================
#  debug_agi.py — One-Off RAG Retrieval Inspection Script
# ============================================================
#
#  What this file does:
#  Manual, single-question diagnostic tool for inspecting exactly what
#  query_rag() returns for one specific question against one specific
#  document — full metadata and full (untruncated) chunk text, printed
#  in a readable format.
#
#  What this file does NOT handle:
#  Does not run any pass/fail check — that belongs to evaluator.py.
#  Does not test multiple questions or documents — single hardcoded
#  question and file_name only, intentionally.
#  Not used by any other part of the app — this is a developer-only
#  debugging script, run manually and read by eye.
#
#  Why this exists alongside evaluator.py:
#  evaluator.py gives a pass/fail signal and prints only the expected
#  page/file on failure — useful for catching regressions, but it doesn't
#  show what was actually retrieved. When a question fails in evaluator.py,
#  this script (or a copy of it with the failing question swapped in) is
#  how you actually see the real chunk text and metadata that came back,
#  to diagnose WHY retrieval missed — wrong chunk boundary, wrong page,
#  embedding similarity miss, etc.
#
#  Usage:
#  Edit QUESTION below to whatever you're currently debugging, then run:
#  python -m src.evaluation.debug_agi
#
#  Imports from:
#  - rag.py → query_rag()
# ============================================================

from src.rag.rag import query_rag

# Hardcoded question + target file for this debugging pass.
# Swap these out per investigation — this script is meant to be edited,
# not parameterized, since it's a one-off inspection tool, not a reusable
# test case (those live in ground_truth.py / evaluator.py instead).
QUESTION = (
    "According to the AGI report, what are the three layers "
    "of the AGI architecture framework?"
)

results = query_rag(
    QUESTION,
    where={"file_name": "01_Artificial_General_Intelligence_Report.pdf"}
)

print("\n" + "=" * 60)
print("RETRIEVAL RESULTS")
print("=" * 60)

# Full, untruncated text and metadata — unlike search_documents() in
# production (which truncates chunks to 300 chars to protect the LLM's
# context window), this script prints everything, since a human reading
# the output needs the complete chunk to judge whether it actually
# answers the question.
for idx, result in enumerate(results, start=1):

    print(f"\nResult #{idx}")

    print("\nMetadata:")
    print(result["metadata"])

    print("\nChunk Text:")
    print(result["text"])

    print("\n" + "-" * 60)