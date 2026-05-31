'''
Loads a cross-encoder model and for each of the 20 candidates from hybird, 
it reads the query AND the chunk together as a pair and outputs a relevance score.
'''

from sentence_transformers import CrossEncoder

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        print("Loading reranker model...")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        print("Reranker loaded.")
    return _reranker

def rerank(query, candidates, top_k=6):
    if not candidates:
        return []
    
    reranker = get_reranker()
    
    pairs = [[query, candidate["content"]] for candidate in candidates]
    scores = reranker.predict(pairs)
    
    for i, candidate in enumerate(candidates):
        candidate["rerank_score"] = float(scores[i])
    
    reranked = sorted(
        candidates,
        key=lambda x: x["rerank_score"],
        reverse=True
    )
    
    return reranked[:top_k]