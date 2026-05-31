'''
Takes the two 20 vector results and 20 B<25 results and merges them using Reciprocal Rank Fusion. 
Chunks appearing in both lists get a score boost. Vector results weighted 60%, 
BM25 weighted 40%. Returns top 20 combined candidates

'''

def hybrid_merge(vector_results, bm25_results, 
                  vector_weight=0.6, bm25_weight=0.4):
    
    combined = {}
    
    for rank, result in enumerate(vector_results):
        chunk_id = result["id"]
        rrf_score = 1 / (60 + rank + 1)
        combined[chunk_id] = {
            **result,
            "hybrid_score": vector_weight * rrf_score,
            "in_vector": True,
            "in_bm25": False
        }
    
    for rank, result in enumerate(bm25_results):
        chunk_id = result["id"]
        rrf_score = 1 / (60 + rank + 1)
        
        if chunk_id in combined:
            combined[chunk_id]["hybrid_score"] += bm25_weight * rrf_score
            combined[chunk_id]["in_bm25"] = True
        else:
            combined[chunk_id] = {
                **result,
                "hybrid_score": bm25_weight * rrf_score,
                "in_vector": False,
                "in_bm25": True
            }
    
    sorted_results = sorted(
        combined.values(),
        key=lambda x: x["hybrid_score"],
        reverse=True
    )
    
    return sorted_results[:20]