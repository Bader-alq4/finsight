import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.retrieval.pipeline import retrieve

# Quick sanity check — print unique sections in results
def print_results(result):
    print(f"Latency: {result['latency_ms']}ms")
    print(f"Vector: {result['vector_count']} | BM25: {result['bm25_count']} | Merged: {result['merged_count']}")
    print(f"\nTop 6 chunks:")
    for i, chunk in enumerate(result["chunks"]):
        print(f"  [{i+1}] {chunk['ticker']} {chunk['fiscal_year']} | {chunk['section_label'][:40]} | score: {chunk['rerank_score']:.3f}")
        print(f"       {chunk['content'][:100]}...")

queries = [
    ("What are Apple's main supply chain risks?", {"tickers": ["AAPL"]}),
    ("How did NVIDIA describe AI demand?", {"tickers": ["NVDA"]}),
    ("What cybersecurity threats does Microsoft face?", {"tickers": ["MSFT"]}),
    ("How has AWS cloud revenue grown?", {"tickers": ["AMZN"]}),
]

for query, filters in queries:
    print(f"\nQuery: {query}")
    print("-" * 60)
    result = retrieve(query, filters=filters)
    print(f"Latency: {result['latency_ms']}ms")
    print(f"Vector: {result['vector_count']} | BM25: {result['bm25_count']} | Merged: {result['merged_count']}")
    print(f"\nTop 6 chunks:")
    for i, chunk in enumerate(result["chunks"]):
        print(f"  [{i+1}] {chunk['ticker']} {chunk['fiscal_year']} | {chunk['section_label'][:40]} | score: {chunk['rerank_score']:.3f}")
        print(f"       {chunk['content'][:100]}...")