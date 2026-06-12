# Runs the full evaluation suite across three retrieval strategies:
# naive vector-only, hybrid search, and hybrid + reranking
# Stores all results in the eval_results table for dashboard display

import csv
import ast
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import DATABASE_URL
from backend.core.retrieval.pipeline import retrieve
from backend.core.retrieval.vector_search import vector_search
from backend.core.generation.generator import generate_answer
from backend.core.evaluation.metrics import compute_all_metrics, parse_chunk_ids

def load_eval_questions(csv_path):
    questions = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickers = [t.strip() for t in row["tickers"].split(",")]
            questions.append({
                "question": row["question"],
                "expected_answer": row["expected_answer"],
                "relevant_chunk_ids": parse_chunk_ids(row["relevant_chunk_ids"]),
                "query_type": row["query_type"],
                "difficulty": row["difficulty"],
                "tickers": tickers
            })
    return questions

def run_strategy(question_data, strategy):
    question = question_data["question"]
    tickers = question_data["tickers"]

    filters = {"tickers": tickers} if tickers and tickers[0] else None

    start = time.time()

    if strategy == "naive_rag":
        results = vector_search(question, top_k=5, filters=filters)
        chunks = results
        retrieved_ids = [c["id"] for c in chunks]
    else:
        result = retrieve(question, top_k=6, filters=filters)
        chunks = result["chunks"]
        retrieved_ids = [c["id"] for c in chunks]

    latency_ms = int((time.time() - start) * 1000)

    answer = generate_answer(question, chunks)

    metrics = compute_all_metrics(
        retrieved_ids,
        question_data["relevant_chunk_ids"],
        k=5
    )

    return {
        "retrieved_ids": retrieved_ids,
        "answer": answer,
        "metrics": metrics,
        "latency_ms": latency_ms,
        "chunks": chunks
    }

def store_result(cursor, question_id, strategy, result):
    cursor.execute("""
        INSERT INTO eval_results
        (question_id, retrieval_strategy, retrieved_chunk_ids,
         generated_answer, precision_at_5, recall_at_5, mrr,
         latency_ms)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        question_id,
        strategy,
        result["retrieved_ids"],
        result["answer"],
        result["metrics"]["precision_at_k"],
        result["metrics"]["recall_at_k"],
        result["metrics"]["mrr"],
        result["latency_ms"]
    ))

def run_evaluation(csv_path="data/finsight_eval.csv"):
    questions = load_eval_questions(csv_path)
    strategies = ["naive_rag", "hybrid_rerank"]

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    print(f"Running evaluation on {len(questions)} questions...")
    print(f"Strategies: {strategies}\n")

    all_results = {strategy: [] for strategy in strategies}

    for i, q in enumerate(questions):
        print(f"Question {i+1}/{len(questions)}: {q['question'][:60]}...")

        cursor.execute("""
            INSERT INTO eval_questions
            (question, expected_answer, relevant_chunk_ids,
             query_type, difficulty)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (
            q["question"],
            q["expected_answer"],
            q["relevant_chunk_ids"],
            q["query_type"],
            q["difficulty"]
        ))

        result = cursor.fetchone()
        if result:
            question_id = result["id"]
        else:
            cursor.execute(
                "SELECT id FROM eval_questions WHERE question = %s",
                (q["question"],)
            )
            question_id = cursor.fetchone()["id"]

        for strategy in strategies:
            print(f"  Running {strategy}...")
            result = run_strategy(q, strategy)
            store_result(cursor, question_id, strategy, result)
            all_results[strategy].append(result["metrics"])

        conn.commit()

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)

    for strategy in strategies:
        metrics_list = all_results[strategy]
        avg_precision = sum(m["precision_at_k"] for m in metrics_list) / len(metrics_list)
        avg_recall = sum(m["recall_at_k"] for m in metrics_list) / len(metrics_list)
        avg_mrr = sum(m["mrr"] for m in metrics_list) / len(metrics_list)

        print(f"\n{strategy}:")
        print(f"  Avg Precision@5: {avg_precision:.3f}")
        print(f"  Avg Recall@5:    {avg_recall:.3f}")
        print(f"  Avg MRR:         {avg_mrr:.3f}")

    cursor.close()
    conn.close()

    return all_results