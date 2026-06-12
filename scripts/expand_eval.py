import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import ast
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import DATABASE_URL
from backend.core.retrieval.pipeline import retrieve
from backend.core.evaluation.metrics import parse_chunk_ids

def expand():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    with open("data/finsight_eval.csv", "r") as f:
        reader = csv.DictReader(f)
        questions = list(reader)

    for i, q in enumerate(questions):
        relevant_ids = parse_chunk_ids(q["relevant_chunk_ids"])
        tickers = [t.strip() for t in q["tickers"].split(",")]
        filters = {"tickers": tickers} if tickers else None

        result = retrieve(q["question"], top_k=6, filters=filters)
        retrieved_ids = [c["id"] for c in result["chunks"]]

        # Find retrieved chunks NOT in your ground truth
        new_candidates = [cid for cid in retrieved_ids if cid not in relevant_ids]

        if new_candidates:
            print(f"\nQ{i+1}: {q['question'][:70]}")
            print(f"  Current relevant IDs: {relevant_ids}")
            print(f"  New candidates to verify: {new_candidates}")

            # Show content of new candidates
            for cid in new_candidates:
                cursor.execute(
                    "SELECT LEFT(content, 200) as preview FROM chunks WHERE id = %s",
                    (cid,)
                )
                row = cursor.fetchone()
                if row:
                    print(f"  Chunk {cid}: {row['preview']}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    expand()