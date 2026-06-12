import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import DATABASE_URL
from backend.core.evaluation.ragas_eval import evaluate_with_ragas

def run_ragas():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    for strategy in ["naive_rag", "hybrid_rerank"]:
        print(f"\nRunning RAGAS for {strategy}...")

        cursor.execute("""
            SELECT 
                eq.question,
                er.generated_answer,
                er.retrieved_chunk_ids
            FROM eval_results er
            JOIN eval_questions eq ON er.question_id = eq.id
            WHERE er.retrieval_strategy = %s
            AND er.generated_answer IS NOT NULL
            LIMIT 20
        """, (strategy,))

        rows = cursor.fetchall()

        questions = []
        answers = []
        contexts = []

        for row in rows:
            chunk_ids = row["retrieved_chunk_ids"]
            if not chunk_ids:
                continue

            cursor.execute("""
                SELECT content FROM chunks 
                WHERE id = ANY(%s)
            """, (chunk_ids,))

            chunk_rows = cursor.fetchall()
            chunk_texts = [r["content"] for r in chunk_rows]

            questions.append(row["question"])
            answers.append(row["generated_answer"])
            contexts.append(chunk_texts)

        if not questions:
            print(f"  No results found for {strategy}")
            continue

        print(f"  Evaluating {len(questions)} questions...")
        results = evaluate_with_ragas(questions, answers, contexts)
        print(f"  Results: {results}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_ragas()