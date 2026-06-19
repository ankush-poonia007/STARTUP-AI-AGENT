from src.rag.rag import query_rag

questions = [
    {
        "question": "What accuracy does LegalAid AI claim for its case outcome prediction system?",
        "correct_page": 1,
        "correct_file": "LegalAid_AI.pdf"
    },
    {
        "question": "How much does the premium subscription tier cost per month?",
        "correct_page": 1,
        "correct_file": "LegalAid_AI.pdf"
    },
    {
        "question": "Which two Indian states are targeted for the initial NGO pilot deployment in Phase 1 of the go-to-market strategy?",
        "correct_page": 1,
        "correct_file": "LegalAid_AI.pdf"
    },
    {
        "question": "What makes LegalAid AI different from competitors according to the pitch deck?",
        "correct_page": 2,
        "correct_file": "LegalAid_AI.pdf"
    },
    {
        "question": "How will the company allocate the funds from its Rs 1.2 crore seed round?",
        "correct_page": 2,
        "correct_file": "LegalAid_AI.pdf"
    }
]

def evaluate():

    correct = 0
    total = len(questions)

    for question in questions:

        results = query_rag(
            question["question"],
            where={"file_name": question["correct_file"]}
        )

        found = False

        for result in results[:3]:

            metadata = result["metadata"]

            if (
                metadata["page_number"] == question["correct_page"]
                and metadata["file_name"] == question["correct_file"]
            ):
                found = True
                break

        if found:
            correct += 1

    recall_at_3 = correct / total

    print(f"Correct: {correct}/{total}")
    print(f"Recall@3: {recall_at_3:.2%}")
    
    
evaluate()
