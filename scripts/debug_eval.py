# scripts/debug_eval.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import ast
from backend.core.retrieval.pipeline import retrieve
from backend.core.evaluation.metrics import parse_chunk_ids

def debug():
    with open("data/finsight_eval.csv", "r") as f:
        reader = csv.DictReader(f)
        questions = list(reader)

    # Test first 5 questions
    for i, q in enumerate(questions[:5]):
        relevant_ids = parse_chunk_ids(q["relevant_chunk_ids"])
        tickers = [t.strip() for t in q["tickers"].split(",")]
        filters = {"tickers": tickers} if tickers else None

        result = retrieve(q["question"], top_k=6, filters=filters)
        retrieved_ids = [c["id"] for c in result["chunks"]]

        hits = [cid for cid in retrieved_ids if cid in relevant_ids]

        print(f"\nQ{i+1}: {q['question'][:60]}")
        print(f"  Relevant IDs:  {relevant_ids}")
        print(f"  Retrieved IDs: {retrieved_ids}")
        print(f"  Hits:          {hits}")
        print(f"  Precision@5:   {len(hits)/5:.2f}")

if __name__ == "__main__":
    debug()