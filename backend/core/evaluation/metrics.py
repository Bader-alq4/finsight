# Computes retrieval evaluation metrics for FinSight
# Implements Precision@K, Recall@K, and Mean Reciprocal Rank (MRR)
# against hand-labeled ground truth chunk IDs

import ast

def parse_chunk_ids(chunk_id_string):
    try:
        return ast.literal_eval(chunk_id_string)
    except:
        return []

def precision_at_k(retrieved_ids, relevant_ids, k=5):
    if not relevant_ids:
        return 0.0
    retrieved_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    hits = sum(1 for cid in retrieved_k if cid in relevant_set)
    return hits / k

def recall_at_k(retrieved_ids, relevant_ids, k=5):
    if not relevant_ids:
        return 0.0
    retrieved_k = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)
    hits = len(retrieved_k & relevant_set)
    return hits / len(relevant_set)

def mean_reciprocal_rank(retrieved_ids, relevant_ids):
    if not relevant_ids:
        return 0.0
    relevant_set = set(relevant_ids)
    for rank, cid in enumerate(retrieved_ids, 1):
        if cid in relevant_set:
            return 1.0 / rank
    return 0.0

def compute_all_metrics(retrieved_ids, relevant_ids, k=5):
    return {
        "precision_at_k": precision_at_k(retrieved_ids, relevant_ids, k),
        "recall_at_k": recall_at_k(retrieved_ids, relevant_ids, k),
        "mrr": mean_reciprocal_rank(retrieved_ids, relevant_ids)
    }