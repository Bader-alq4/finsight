# Integrates RAGAS library to measure answer faithfulness and relevance
# Faithfulness measures whether every claim in the answer is grounded
# in the retrieved context. Answer relevance measures whether the
# answer actually addresses the question asked

from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset

def evaluate_with_ragas(questions, answers, contexts):
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts
    }
    dataset = Dataset.from_dict(data)

    results = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy]
    )

    return results