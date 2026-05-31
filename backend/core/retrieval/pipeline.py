'''
Wire all four workfloes together into one function call.

'''

from backend.core.retrieval.vector_search import vector_search
from backend.core.retrieval.bm25_search import bm25_search
from backend.core.retrieval.hybrid import hybrid_merge
from backend.core.retrieval.reranker import rerank
import time

def retrieve(query, top_k=6, filters=None):
    start = time.time()
    
    # Run both searches in parallel
    vector_results = vector_search(query, top_k=20, filters=filters)
    bm25_results = bm25_search(query, top_k=20, filters=filters)
    
    # Merge with RRF
    merged = hybrid_merge(vector_results, bm25_results)
    
    # Rerank top 20 down to top 6
    final = rerank(query, merged, top_k=top_k)
    
    elapsed = int((time.time() - start) * 1000)
    
    return {
        "chunks": final,
        "latency_ms": elapsed,
        "vector_count": len(vector_results),
        "bm25_count": len(bm25_results),
        "merged_count": len(merged)
    }