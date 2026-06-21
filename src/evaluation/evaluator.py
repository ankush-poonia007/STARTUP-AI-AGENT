# ============================================================
#  evaluator.py — Offline RAG Retrieval Evaluation Tool
# ============================================================
#
#  What this file does:
#  Standalone, offline measurement of RAG retrieval quality against the
#  hand-written ground-truth benchmark in ground_truth.py. Calls query_rag()
#  directly — bypassing the LLM/orchestrator entirely — to isolate whether
#  retrieval itself is working, independent of how the LLM later phrases
#  an answer from whatever chunks come back.
#
#  What this file does NOT handle:
#  Does not call the LLM, the orchestrator, or any tool-calling logic —
#  this measures the RAG layer in isolation.
#  Does not generate ground-truth questions — those are human-written in
#  ground_truth.py and must stay that way (see that file's header).
#  Does not run automatically as part of the app — this is a manual,
#  on-demand diagnostic tool run by a developer after a chunking, embedding,
#  or retrieval-parameter change, to confirm the change didn't regress quality.
#
#  Metric — Recall@K:
#  For each ground-truth question, query_rag() is called with the question
#  and a where={"file_name": correct_file} filter — the exact same filtering
#  mechanism Stage 4's search_documents() uses in production. The question
#  is counted "correct" if ANY of the top-K returned chunks has metadata
#  matching both the expected page_number AND file_name. Recall@K is the
#  fraction of questions answered correctly out of the total.
#
#  Why where={"file_name": ...} is included even for single-document tests:
#  This evaluator was specifically built during Phase 4's multi-document
#  work — proving the where-filter correctly isolates one document's chunks
#  is the actual point of the test, not just whether retrieval works at all.
#
#  Purpose — re-run this after changing:
#  - Chunking strategy (paragraph size, overlap, fixed-token vs semantic)
#  - Embedding model
#  - Retrieval parameters (n_results / TOP_K, where-clause logic)
#  - Document ingestion pipeline
#
#  Verified result (Phase 4, post-chunking-improvement):
#  100% recall@3 across 5 documents, 25 questions, full corpus — zero
#  cross-document contamination.
#
#  Used by:
#  - Developer, manually: `python -m src.evaluation.evaluator`
#
#  Imports from:
#  - rag.py          → query_rag()
#  - ground_truth.py → all 5 per-document datasets + ALL_QUESTIONS
# ============================================================

from src.rag.rag import query_rag
from src.evaluation.ground_truth import (
    ALL_QUESTIONS,
    AGI_DATASET,
    CYBERSECURITY_DATASET,
    QUANTUM_DATASET,
    RENEWABLE_ENERGY_DATASET,
    CLIMATE_CHANGE_DATASET,
)

# Top-K cutoff for the recall@K metric. 3 matches the n_results value used
# by search_documents() in production (rag.py) — the evaluator must use the
# same K the real system uses, or a "pass" here wouldn't reflect what
# actually happens at runtime.
TOP_K = 3


def evaluate(dataset: list, dataset_name: str) -> float:
    """Runs recall@K evaluation for one dataset and prints a pass/fail report.

    For every question in the dataset, calls query_rag() scoped to that
    question's correct_file, then checks whether the expected
    (correct_page, correct_file) pair appears anywhere in the top-K results.
    Failures are printed immediately with the expected location, so a
    developer can see exactly which questions are missing without having
    to re-run anything.

    Parameters:
        dataset      (list) → list of {"question", "correct_page", "correct_file"}
                              dicts, e.g. AGI_DATASET or ALL_QUESTIONS
        dataset_name (str)  → human-readable label printed in the report header

    Returns:
        float → recall@K as a fraction between 0.0 and 1.0
                (correct questions / total questions)

    Why "found" breaks on first match, not best match:
        Recall@K only asks whether the correct chunk is present somewhere in
        the top-K results — not whether it's ranked first. A correct chunk
        anywhere in the top-K is still retrievable by the LLM, so the exact
        rank position within K doesn't matter for this metric.

    Why metadata match requires BOTH page_number AND file_name:
        Matching only page_number could produce a false positive if two
        different uploaded PDFs happen to both have content on, say, page 2.
        Matching both fields confirms the retrieved chunk is genuinely from
        the expected source, not a coincidental page-number collision.
    """

    correct = 0
    total = len(dataset)

    print(f"\n{'=' * 60}")
    print(f"Evaluating: {dataset_name}")
    print(f"{'=' * 60}")

    for question in dataset:

        # Same where-filter mechanism used by search_documents() in
        # production — this evaluator proves that filter actually isolates
        # the correct document, not just that retrieval works in general.
        results = query_rag(
            question["question"],
            where={"file_name": question["correct_file"]}
        )

        found = False

        for result in results[:TOP_K]:

            metadata = result["metadata"]

            if (
                metadata["page_number"] == question["correct_page"]
                and metadata["file_name"] == question["correct_file"]
            ):
                found = True
                break

        if found:
            correct += 1
        else:
            # Print failures immediately and individually — a silent
            # aggregate score alone wouldn't show WHICH questions are
            # failing, which is the actually useful diagnostic signal here.
            print(f"\nFAILED:")
            print(f"Question: {question['question']}")
            print(f"Expected Page: {question['correct_page']}")
            print(f"Expected File: {question['correct_file']}")

    recall = correct / total

    print(f"\nCorrect: {correct}/{total}")
    print(f"Recall@{TOP_K}: {recall:.2%}")

    return recall


if __name__ == "__main__":

    # Per-document evaluation — isolates whether a regression is specific
    # to one document's content/chunking, or systemic across all of them.
    evaluate(AGI_DATASET, "AGI")
    evaluate(CYBERSECURITY_DATASET, "Cybersecurity")
    evaluate(QUANTUM_DATASET, "Quantum Computing")
    evaluate(RENEWABLE_ENERGY_DATASET, "Renewable Energy")
    evaluate(CLIMATE_CHANGE_DATASET, "Climate Change")

    # Full-corpus evaluation — runs every question across the entire
    # collection. A passing full-corpus score with all 5 individual
    # documents also passing is the strongest evidence that cross-document
    # isolation (the where-filter) is working correctly at scale, not just
    # in isolated single-document tests.
    print(f"\n{'=' * 60}")
    print("FULL CORPUS EVALUATION")
    print(f"{'=' * 60}")

    evaluate(ALL_QUESTIONS, "All Documents")


"""
Future Improvements:

* Recall@1 and Recall@5 — current TOP_K=3 only; comparing across K values
  would show how sensitive retrieval quality is to the cutoff.
* MRR (Mean Reciprocal Rank) — recall@K treats any position in the top-K
  as equally good; MRR would reward chunks ranked higher within the top-K.
* Precision@K — recall@K doesn't penalize irrelevant chunks also being
  retrieved alongside the correct one; precision would catch retrieval
  that's "correct but noisy."
* File-level accuracy — does retrieval ever return chunks from the WRONG
  file even when where-filtering is applied correctly? Currently only
  checked implicitly via the metadata match above, not reported separately.
* Page-level accuracy — same idea, isolated to page_number mismatches only.
* Automatic benchmark reports — write results to a timestamped file instead
  of only printing to stdout, so historical runs can be compared over time.
"""