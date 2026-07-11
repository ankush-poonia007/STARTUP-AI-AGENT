
import time
from src.rag.rag import (
    query_rag,
    ingest_pdf,
    embed_and_store,
)

from src.evaluation.ground_truth import (
    ALL_QUESTIONS,
    AGI_DATASET,
    CYBERSECURITY_DATASET,
    QUANTUM_DATASET,
    RENEWABLE_ENERGY_DATASET,
    CLIMATE_CHANGE_DATASET,
    HS_ALL_QUESTIONS,
    HS_AGI_DATASET,
    HS_RENEWABLE_ENERGY_DATASET,
    HS_CLIMATE_CHANGE_DATASET,
    HS_QUANTUM_DATASET,
    HS_CYBERSECURITY_DATASET,
    
)




def evaluate(dataset: list, dataset_name: str) :
    


    total = len(dataset)

    recall_at_1 = 0
    recall_at_3 = 0

    reciprocal_rank_sum = 0
    rank_sum = 0

    total_latency = 0

    failures = []
    ranking_issues = []

    print(f"\n{'=' * 70}")
    print(f"Evaluating: {dataset_name}")
    print(f"{'=' * 70}")

    for question in dataset:

        start = time.perf_counter()

        results = query_rag(
            question["question"],
            where={"file_name": question["correct_file"]}
        )

        latency = time.perf_counter() - start
        total_latency += latency

        found_rank = None
        retrieved_pages = []

        for rank, result in enumerate(results, start=1):

            metadata = result["metadata"]

            retrieved_pages.append(
                {
                    "rank": rank,
                    "page": metadata["page_number"],
                    "file": metadata["file_name"],
                    "distance": result["distance"],
                }
            )

            if (
                metadata["page_number"] == question["correct_page"]
                and metadata["file_name"] == question["correct_file"]
            ):
                found_rank = rank

        if found_rank is not None:

            recall_at_3 += 1

            if found_rank == 1:
                recall_at_1 += 1

            reciprocal_rank_sum += 1 / found_rank
            rank_sum += found_rank

            if found_rank > 1:
                ranking_issues.append(
                    {
                        "question": question["question"],
                        "expected_page": question["correct_page"],
                        "expected_file": question["correct_file"],
                        "correct_rank": found_rank,
                        "retrieved": retrieved_pages,
                    }
                )

        else:

            failures.append(
                {
                    "question": question["question"],
                    "expected_page": question["correct_page"],
                    "expected_file": question["correct_file"],
                    "retrieved": retrieved_pages,
                }
            )

    # ==========================================================
    # Metrics
    # ==========================================================

    recall1 = recall_at_1 / total
    recall3 = recall_at_3 / total

    mrr = reciprocal_rank_sum / total
    avg_rank = rank_sum / recall_at_3 if recall_at_3 else 0

    avg_latency = total_latency / total

    # ==========================================================
    # Report
    # ==========================================================

    print("\nRAG Evaluation Report")
    print("-" * 70)

    print(f"Questions           : {total}")
    print(f"Recall@1            : {recall1:.2%}")
    print(f"Recall@3            : {recall3:.2%}")
    print(f"MRR                 : {mrr:.4f}")
    print(f"Average Rank        : {avg_rank:.2f}")
    print(f"Average Latency     : {avg_latency:.3f} sec")
    print(f"Failures            : {len(failures)}")

    print("\nStatus:", "PASS ✅" if len(failures) == 0 else "FAIL ❌")

    # ==========================================================
    # Ranking Diagnostics
    # ==========================================================

    print("\n" + "=" * 70)
    print("RANKING DIAGNOSTICS")
    print("=" * 70)

    if not ranking_issues:
        print("✅ Every query retrieved the correct page at Rank #1.")

    else:

        for issue in ranking_issues:

            print(f"\nQuestion:")
            print(issue["question"])

            print(f"\nExpected File : {issue['expected_file']}")
            print(f"Expected Page : {issue['expected_page']}")
            print(f"Correct Rank  : {issue['correct_rank']}")

            print("\nRetrieved Order:")

            for item in issue["retrieved"]:

                marker = (
                    "✅"
                    if (
                        item["page"] == issue["expected_page"]
                        and item["file"] == issue["expected_file"]
                    )
                    else "❌"
                )

                print(
                    f"  Rank {item['rank']}"
                    f" -> Page {item['page']}"
                    f" ({item['file']})"
                    f" | Distance: {item['distance']:.4f}"
                    f" {marker}"
                )

            print("-" * 70)

    # ==========================================================
    # Failed Queries
    # ==========================================================

    if failures:

        print("\n" + "=" * 70)
        print("FAILED QUERIES")
        print("=" * 70)

        for failure in failures:

            print(f"\nQuestion:")
            print(failure["question"])

            print(f"\nExpected File : {failure['expected_file']}")
            print(f"Expected Page : {failure['expected_page']}")

            print("\nRetrieved:")

            for item in failure["retrieved"]:

                print(
                    f"  Rank {item['rank']} "
                    f"-> Page {item['page']} "
                    f"({item['file']})"
                )

            print("-" * 70)

    return {
        "Recall@1": recall1,
        "Recall@3": recall3,
        "MRR": mrr,
        "AverageRank": avg_rank,
        "AverageLatency": avg_latency,
        "Failures": len(failures),
    }


if __name__ == "__main__":

    FILE_LIST = [
        r'data\uploads\01_Artificial_General_Intelligence_Report.pdf',
        r'data\uploads\02_Cybersecurity_Threat_Intelligence_Report.pdf',
        r'data\uploads\03_Quantum_Computing_Research_Report.pdf',
        r'data\uploads\04_Renewable_Energy_Transition_Report.pdf',
        r'data\uploads\05_Climate_Change_Mitigation_Report.pdf',
    ]
    
    for file in FILE_LIST:
        chunks = ingest_pdf(file)
        embed_and_store(chunks)
    
    evaluate(AGI_DATASET, "AGI")
    evaluate(CYBERSECURITY_DATASET, "Cybersecurity")
    evaluate(QUANTUM_DATASET, "Quantum Computing")
    evaluate(RENEWABLE_ENERGY_DATASET, "Renewable Energy")
    evaluate(CLIMATE_CHANGE_DATASET, "Climate Change")

    
    print(f"\n{'=' * 60}")
    print("FULL CORPUS EVALUATION")
    print(f"{'=' * 60}")

    evaluate(ALL_QUESTIONS, "All Documents")
    
    print(f"\n{'=' * 60}")
    print("FULL CORPUS EVALUATION")
    print(f"{'=' * 60}")
    
    evaluate(HS_AGI_DATASET, "HS   AGI")
    evaluate(HS_CYBERSECURITY_DATASET, "HS Cybersecurity")
    evaluate(HS_QUANTUM_DATASET, "HS   Quantum Computing")
    evaluate(HS_RENEWABLE_ENERGY_DATASET, "HS Renewable Energy")
    evaluate(HS_CLIMATE_CHANGE_DATASET, "HS   Climate Change")

    
    print(f"\n{'=' * 60}")
    print("FULL CORPUS EVALUATION")
    print(f"{'=' * 60}")

    evaluate(HS_ALL_QUESTIONS, "HS All Documents")


    print(f"\n{'=' * 60}")
    print("FULL CORPUS EVALUATION")
    print(f"{'=' * 60}")