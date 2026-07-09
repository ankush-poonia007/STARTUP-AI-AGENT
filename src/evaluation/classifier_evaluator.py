"""
============================================================
BizRadar AI
Document Classifier Evaluator
============================================================

Evaluates the document-routing classifier against the
ground-truth benchmark datasets.

Author
------
BizRadar AI
"""

# ============================================================
# Standard Library
# ============================================================

import time
import traceback

from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Optional

# ============================================================
# Ground Truth Benchmark
# ============================================================

from src.evaluation.classifier_ground_truth import (
    DOCUMENT_SEARCH_CASES,
    DOCUMENT_QA_CASES,
    DOCUMENT_SUMMARY_CASES,
    INFORMATION_EXTRACTION_CASES,
    DOCUMENT_COMPARISON_CASES,
    STARTUP_ANALYSIS_CASES,
    MVP_CASES,
    TECH_STACK_CASES,
    CODING_CASES,
    GENERAL_KNOWLEDGE_CASES,
    GREETING_CASES,
    STARTUP_DOCUMENT_CASES
)

BENCHMARKS = [
    ("Document Summary", DOCUMENT_SUMMARY_CASES),
    ("Document QA", DOCUMENT_QA_CASES),
    ("Document Search", DOCUMENT_SEARCH_CASES),
    ("Information Extraction", INFORMATION_EXTRACTION_CASES),
    ("Document Comparison", DOCUMENT_COMPARISON_CASES),
    ("Startup Analysis", STARTUP_ANALYSIS_CASES),
    ("MVP", MVP_CASES),
    ("Tech Stack", TECH_STACK_CASES),
    ("Coding", CODING_CASES),
    ("General Knowledge", GENERAL_KNOWLEDGE_CASES),
    ("Greetings", GREETING_CASES),
    ("Startup Document Queries",STARTUP_DOCUMENT_CASES)
]

# ============================================================
# Actual Classifier Under Test
# ============================================================

from src.rag.rag import (
    classify_document_relevance,
)

# ============================================================
# Configuration
# ============================================================

# Uploaded filenames supplied to the classifier during
# evaluation. The classifier only needs filenames, not the
# document contents.

TEST_FILENAMES = (
    "01_Artificial_General_Intelligence_Report.pdf "
    "02_Cybersecurity_Threat_Intelligence_Report.pdf "
    "03_Quantum_Computing_Research_Report.pdf "
    "04_Renewable_Energy_Transition_Report.pdf "
    "05_Climate_Change_Mitigation_Report.pdf"
)

DIVIDER = "=" * 80
SECTION_DIVIDER = "-" * 80

# ------------------------------------------------------------
# Console Behaviour
# ------------------------------------------------------------

VERBOSE = True

SHOW_FAILURE_DETAILS = True
SHOW_AMBIGUOUS_RESULTS = True
SHOW_ADVERSARIAL_RESULTS = True

ROUND_DIGITS = 4


# ============================================================
# Console Helpers
# ============================================================

def print_header(title: str) -> None:
    """
    Print a major section heading.
    """

    print()
    print(DIVIDER)
    print(title.upper())
    print(DIVIDER)


def print_subheader(title: str) -> None:
    """
    Print a subsection heading.
    """

    print()
    print(title)
    print(SECTION_DIVIDER)


def print_metric(label: str, value) -> None:
    """
    Print one aligned metric.
    """

    print(f"{label:<30}: {value}")


# ============================================================
# Evaluation Result
# ============================================================

@dataclass(slots=True)
class PredictionResult:
    """
    Stores the evaluation result of one benchmark case.
    """

    case_id: str

    category: str

    intent: str

    difficulty: str

    query: str

    expected: Optional[bool]

    predicted: Optional[bool]

    correct: bool

    latency: float

    error: Optional[str] = None


# ============================================================
# Benchmark Metrics
# ============================================================

@dataclass(slots=True)
class BenchmarkMetrics:
    """
    Stores benchmark statistics.
    """

    total_cases: int

    correct_predictions: int

    failed_cases: int

    true_positive: int

    true_negative: int

    false_positive: int

    false_negative: int

    accuracy: float

    precision: float

    recall: float

    f1_score: float

    average_latency: float
    
# ============================================================
# Single Case Evaluation
# ============================================================

def evaluate_case(
    case: Dict,
    filenames: str = TEST_FILENAMES,
) -> PredictionResult:
    """
    Evaluate a single benchmark case.

    Executes the real document classifier, measures latency,
    compares the prediction against the expected routing
    decision, and returns a structured result.
    """

    start_time = time.perf_counter()

    try:

        prediction = classify_document_relevance(
            user_input=case["query"],
            filenames=filenames,
        )

        latency = time.perf_counter() - start_time

        return PredictionResult(
            case_id=case["case_id"],
            category=case["category"],
            intent=case["intent"],
            difficulty=case["difficulty"],
            query=case["query"],
            expected=case["expected"],
            predicted=prediction,
            correct=(prediction == case["expected"]),
            latency=latency,
        )

    except Exception:

        latency = time.perf_counter() - start_time

        return PredictionResult(
            case_id=case["case_id"],
            category=case["category"],
            intent=case["intent"],
            difficulty=case["difficulty"],
            query=case["query"],
            expected=case["expected"],
            predicted=None,
            correct=False,
            latency=latency,
            error=traceback.format_exc(),
        )


# ============================================================
# Dataset Evaluation
# ============================================================

def evaluate_dataset(
    dataset: List[Dict],
    dataset_name: str,
    filenames: str = TEST_FILENAMES,
) -> List[PredictionResult]:
    """
    Evaluate an entire benchmark dataset.

    Parameters
    ----------
    dataset : List[Dict]
        Collection of benchmark cases.

    dataset_name : str
        Human-readable dataset name.

    filenames : str
        Uploaded filenames passed to the classifier.

    Returns
    -------
    List[PredictionResult]
        Evaluation results for every benchmark case.
    """

    print_header(f"Evaluating Dataset : {dataset_name}")

    total_cases = len(dataset)

    results: List[PredictionResult] = []

    successful = 0
    failed = 0

    dataset_start = time.perf_counter()

    for index, case in enumerate(dataset, start=1):

        if VERBOSE:

            print(
                f"[{index:>3}/{total_cases}] "
                f"{case['case_id']}...",
                end=" ",
                flush=True,
            )

        result = evaluate_case(
            case=case,
            filenames=filenames,
        )

        results.append(result)

        if result.correct:

            successful += 1

            if VERBOSE:
                print("✓")

        else:

            failed += 1

            if VERBOSE:
                print("✗")

    dataset_latency = time.perf_counter() - dataset_start

    print()

    print_subheader("Dataset Summary")

    print_metric(
        "Dataset",
        dataset_name,
    )

    print_metric(
        "Total Cases",
        total_cases,
    )

    print_metric(
        "Passed",
        successful,
    )

    print_metric(
        "Failed",
        failed,
    )

    print_metric(
        "Accuracy",
        f"{successful / total_cases:.2%}",
    )

    print_metric(
        "Execution Time",
        f"{dataset_latency:.2f} sec",
    )

    return results

# ============================================================
# Metrics Engine
# ============================================================

def compute_metrics(
    results: List[PredictionResult],
) -> BenchmarkMetrics:
    """
    Compute benchmark metrics from evaluation results.
    """

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    total_latency = 0.0

    failures = 0

    for result in results:

        total_latency += result.latency

        if result.error is not None:
            failures += 1

        if result.expected is True:

            if result.predicted is True:
                tp += 1
            else:
                fn += 1

        elif result.expected is False:

            if result.predicted is False:
                tn += 1
            else:
                fp += 1

    total_cases = len(results)

    correct_predictions = tp + tn

    accuracy = (
        correct_predictions / total_cases
        if total_cases
        else 0.0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    average_latency = (
        total_latency / total_cases
        if total_cases
        else 0.0
    )

    return BenchmarkMetrics(
        total_cases=total_cases,
        correct_predictions=correct_predictions,
        failed_cases=failures,
        true_positive=tp,
        true_negative=tn,
        false_positive=fp,
        false_negative=fn,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        average_latency=average_latency,
    )


# ============================================================
# Benchmark Summary
# ============================================================

def print_summary(
    metrics: BenchmarkMetrics,
) -> None:
    """
    Print the overall benchmark summary.
    """

    print_header("Benchmark Summary")

    print_metric(
        "Total Cases",
        metrics.total_cases,
    )

    print_metric(
        "Correct Predictions",
        metrics.correct_predictions,
    )

    print_metric(
        "Failed Cases",
        metrics.failed_cases,
    )

    print()

    print_metric(
        "Accuracy",
        f"{metrics.accuracy:.2%}",
    )

    print_metric(
        "Precision",
        f"{metrics.precision:.2%}",
    )

    print_metric(
        "Recall",
        f"{metrics.recall:.2%}",
    )

    print_metric(
        "F1 Score",
        f"{metrics.f1_score:.2%}",
    )

    print()

    print_metric(
        "True Positive",
        metrics.true_positive,
    )

    print_metric(
        "True Negative",
        metrics.true_negative,
    )

    print_metric(
        "False Positive",
        metrics.false_positive,
    )

    print_metric(
        "False Negative",
        metrics.false_negative,
    )

    print()

    print_metric(
        "Average Latency",
        f"{metrics.average_latency:.3f} sec",
    )

    print(DIVIDER)
    
# ============================================================
# Confusion Matrix
# ============================================================

def print_confusion_matrix(
    metrics: BenchmarkMetrics,
) -> None:
    """
    Print the confusion matrix.
    """

    print_header("Confusion Matrix")

    print(f"{'':>18} Predicted")
    print(f"{'':>14} True{'':>8}False")
    print()

    print(
        f"Actual True   "
        f"{metrics.true_positive:>8}"
        f"{metrics.false_negative:>10}"
    )

    print(
        f"Actual False  "
        f"{metrics.false_positive:>8}"
        f"{metrics.true_negative:>10}"
    )

    print()

    print_metric(
        "True Positive",
        metrics.true_positive,
    )

    print_metric(
        "True Negative",
        metrics.true_negative,
    )

    print_metric(
        "False Positive",
        metrics.false_positive,
    )

    print_metric(
        "False Negative",
        metrics.false_negative,
    )


# ============================================================
# Category Metrics
# ============================================================

def print_category_metrics(
    results: List[PredictionResult],
) -> None:
    """
    Print benchmark metrics grouped by category.
    """

    print_header("Category Metrics")

    grouped_results = defaultdict(list)

    for result in results:
        grouped_results[result.category].append(result)

    for category in sorted(grouped_results.keys()):

        metrics = compute_metrics(
            grouped_results[category]
        )

        print_subheader(category)

        print_metric(
            "Total Cases",
            metrics.total_cases,
        )

        print_metric(
            "Correct",
            metrics.correct_predictions,
        )

        print_metric(
            "Failures",
            metrics.failed_cases,
        )

        print_metric(
            "Accuracy",
            f"{metrics.accuracy:.2%}",
        )

        print_metric(
            "Precision",
            f"{metrics.precision:.2%}",
        )

        print_metric(
            "Recall",
            f"{metrics.recall:.2%}",
        )

        print_metric(
            "F1 Score",
            f"{metrics.f1_score:.2%}",
        )

        print_metric(
            "Average Latency",
            f"{metrics.average_latency:.3f} sec",
        )


# ============================================================
# Difficulty Metrics
# ============================================================

def print_difficulty_metrics(
    results: List[PredictionResult],
) -> None:
    """
    Print benchmark metrics grouped by difficulty.
    """

    print_header("Difficulty Metrics")

    grouped_results = defaultdict(list)

    for result in results:
        grouped_results[result.difficulty].append(result)

    difficulty_order = [
        "easy",
        "medium",
        "hard",
    ]

    for difficulty in difficulty_order:

        if difficulty not in grouped_results:
            continue

        metrics = compute_metrics(
            grouped_results[difficulty]
        )

        print_subheader(
            difficulty.capitalize()
        )

        print_metric(
            "Total Cases",
            metrics.total_cases,
        )

        print_metric(
            "Correct",
            metrics.correct_predictions,
        )

        print_metric(
            "Failures",
            metrics.failed_cases,
        )

        print_metric(
            "Accuracy",
            f"{metrics.accuracy:.2%}",
        )

        print_metric(
            "Precision",
            f"{metrics.precision:.2%}",
        )

        print_metric(
            "Recall",
            f"{metrics.recall:.2%}",
        )

        print_metric(
            "F1 Score",
            f"{metrics.f1_score:.2%}",
        )

        print_metric(
            "Average Latency",
            f"{metrics.average_latency:.3f} sec",
        )
        
# ============================================================
# False Positive Analysis
# ============================================================

def print_false_positives(
    results: List[PredictionResult],
) -> None:
    """
    Print all False Positive predictions.

    False Positive
    --------------
    Expected  : False
    Predicted : True
    """

    print_header("False Positive Analysis")

    false_positives = [

        result

        for result in results

        if (
            result.expected is False
            and
            result.predicted is True
        )

    ]

    false_positives.sort(
        key=lambda result: (
            result.category,
            result.case_id,
        )
    )

    print_metric(
        "False Positives",
        len(false_positives),
    )

    if not false_positives:

        print("\n✅ No false positives detected.")

        return

    for result in false_positives:

        print_subheader(result.case_id)

        print_metric(
            "Category",
            result.category,
        )

        print_metric(
            "Intent",
            result.intent,
        )

        print_metric(
            "Difficulty",
            result.difficulty.capitalize(),
        )

        print_metric(
            "Latency",
            f"{result.latency:.3f} sec",
        )

        print()

        print("Query")
        print("-----")
        print(result.query)

        if result.error:

            print()

            print("Exception")
            print("---------")
            print(result.error)


# ============================================================
# False Negative Analysis
# ============================================================

def print_false_negatives(
    results: List[PredictionResult],
) -> None:
    """
    Print all False Negative predictions.

    False Negative
    --------------
    Expected  : True
    Predicted : False
    """

    print_header("False Negative Analysis")

    false_negatives = [

        result

        for result in results

        if (
            result.expected is True
            and
            result.predicted is False
        )

    ]

    false_negatives.sort(
        key=lambda result: (
            result.category,
            result.case_id,
        )
    )

    print_metric(
        "False Negatives",
        len(false_negatives),
    )

    if not false_negatives:

        print("\n✅ No false negatives detected.")

        return

    for result in false_negatives:

        print_subheader(result.case_id)

        print_metric(
            "Category",
            result.category,
        )

        print_metric(
            "Intent",
            result.intent,
        )

        print_metric(
            "Difficulty",
            result.difficulty.capitalize(),
        )

        print_metric(
            "Latency",
            f"{result.latency:.3f} sec",
        )

        print()

        print("Query")
        print("-----")
        print(result.query)

        if result.error:

            print()

            print("Exception")
            print("---------")
            print(result.error)
            
# ============================================================
# Ambiguous Benchmark
# ============================================================

def evaluate_ambiguous(
    dataset: List[Dict],
    filenames: str = TEST_FILENAMES,
) -> None:
    """
    Evaluate ambiguous routing cases.

    These cases are NOT scored because there is no single
    objectively correct routing decision.

    The purpose is to inspect classifier consistency.
    """

    if not SHOW_AMBIGUOUS_RESULTS:
        return

    print_header("Ambiguous Benchmark")

    total_cases = len(dataset)

    true_count = 0
    false_count = 0
    errors = 0

    for index, case in enumerate(dataset, start=1):

        if VERBOSE:

            print(
                f"[{index:>3}/{total_cases}] "
                f"{case['case_id']}"
            )

        result = evaluate_case(
            case=case,
            filenames=filenames,
        )

        if result.error:

            errors += 1

            if VERBOSE:

                print_metric(
                    "Prediction",
                    "ERROR",
                )

                print_metric(
                    "Reason",
                    result.error.splitlines()[-1],
                )

                print()

            continue

        if result.predicted:
            true_count += 1
        else:
            false_count += 1

        if VERBOSE:

            print_metric(
                "Category",
                result.category,
            )

            print_metric(
                "Intent",
                result.intent,
            )

            print_metric(
                "Prediction",
                result.predicted,
            )

            print_metric(
                "Latency",
                f"{result.latency:.3f} sec",
            )

            print()

            print("Query")
            print("-----")
            print(result.query)
            print()

    print_subheader("Summary")

    print_metric(
        "Total Cases",
        total_cases,
    )

    print_metric(
        "Predicted TRUE",
        true_count,
    )

    print_metric(
        "Predicted FALSE",
        false_count,
    )

    print_metric(
        "Errors",
        errors,
    )


# ============================================================
# Adversarial Benchmark
# ============================================================

def evaluate_adversarial(
    dataset: List[Dict],
    filenames: str = TEST_FILENAMES,
) -> None:
    """
    Evaluate adversarial prompts.

    These cases are NOT included in benchmark metrics.

    Their purpose is to evaluate robustness against prompt
    injection and routing attacks.
    """

    if not SHOW_ADVERSARIAL_RESULTS:
        return

    print_header("Adversarial Benchmark")

    total_cases = len(dataset)

    true_count = 0
    false_count = 0
    errors = 0

    for index, case in enumerate(dataset, start=1):

        if VERBOSE:

            print(
                f"[{index:>3}/{total_cases}] "
                f"{case['case_id']}"
            )

        result = evaluate_case(
            case=case,
            filenames=filenames,
        )

        if result.error:

            errors += 1

            if VERBOSE:

                print_metric(
                    "Prediction",
                    "ERROR",
                )

                print_metric(
                    "Reason",
                    result.error.splitlines()[-1],
                )

                print()

            continue

        if result.predicted:
            true_count += 1
        else:
            false_count += 1

        if VERBOSE:

            print_metric(
                "Attack Type",
                result.intent,
            )

            print_metric(
                "Prediction",
                result.predicted,
            )

            print_metric(
                "Latency",
                f"{result.latency:.3f} sec",
            )

            print()

            print("Prompt")
            print("------")
            print(result.query)
            print()

    print_subheader("Summary")

    print_metric(
        "Total Cases",
        total_cases,
    )

    print_metric(
        "Predicted TRUE",
        true_count,
    )

    print_metric(
        "Predicted FALSE",
        false_count,
    )

    print_metric(
        "Errors",
        errors,
    )
    
    
# ============================================================
# Main
# ============================================================
def run_all_benchmarks() -> None:
    """
    Run every benchmark sequentially with a cooldown.
    """

    for index, (name, dataset) in enumerate(BENCHMARKS, start=1):

        print_header(
            f"Benchmark {index}/{len(BENCHMARKS)} : {name}"
        )

        results = evaluate_dataset(
            dataset=dataset,
            dataset_name=name,
        )

        metrics = compute_metrics(results)

        print_summary(metrics)

        print_confusion_matrix(metrics)

        print_category_metrics(results)

        print_difficulty_metrics(results)

        if SHOW_FAILURE_DETAILS:
            print_false_positives(results)
            print_false_negatives(results)

        if index != len(BENCHMARKS):
            print(f"\nSleeping 60 seconds before next benchmark...\n")
            time.sleep(60)
            
            
def main() -> None:
    """
    Execute the complete document classifier benchmark.
    """

    benchmark_start = time.perf_counter()

    print_header(
        "BizRadar AI Document Classifier Evaluation"
    )

    # --------------------------------------------------------
    # Deterministic Benchmark
    # --------------------------------------------------------

    run_all_benchmarks()

    # metrics = compute_metrics(results)

    # --------------------------------------------------------
    # Overall Summary
    # --------------------------------------------------------

    # print_summary(metrics)

    # --------------------------------------------------------
    # Reports
    # --------------------------------------------------------

    # print_confusion_matrix(metrics)
# 
    # print_category_metrics(results)
# 
    # print_difficulty_metrics(results)
# 
    # if SHOW_FAILURE_DETAILS:
# 
        # print_false_positives(results)
# 
        # print_false_negatives(results)

    # --------------------------------------------------------
    # Analysis Benchmarks
    # --------------------------------------------------------

    # evaluate_ambiguous(
    #     dataset=AMBIGUOUS_TEST_CASES,
    # )

    # evaluate_adversarial(
    #     dataset=ADVERSARIAL_TEST_CASES,
    # )

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------

    benchmark_time = (
        time.perf_counter()
        - benchmark_start
    )

    print_header("Evaluation Complete")

    print_metric(
        "Total Runtime",
        f"{benchmark_time:.2f} sec",
    )

    print()

    print("✅ Benchmark completed successfully.")


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    main()