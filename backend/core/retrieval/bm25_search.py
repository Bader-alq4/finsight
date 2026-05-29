# Loads all chunks from the database into memory at startup and builds a BM25 index. S
# Find chunks that contain the exact keywords from the question.

import psycopg2
from psycopg2.extras import RealDictCursor
from rank_bm25 import BM25Okapi
from backend.config import DATABASE_URL

_bm25_index = None
_chunk_data = []

EXCLUDED_SECTIONS = {
    'front matter',
    'item 8. financial statements',
    'item 10. directors and officers',
    'item 11. executive compensation',
    'item 14. accountant fees',
    'item 15. exhibits',
    'item 16. summary'
}

def build_bm25_index():
    global _bm25_index, _chunk_data

    print("Building BM25 index...")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            c.content,
            c.section_label,
            c.chunk_index,
            c.token_count,
            co.name as company_name,
            co.ticker,
            co.id as company_id,
            d.fiscal_year,
            d.document_type
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        JOIN companies co ON c.company_id = co.id
        ORDER BY c.id
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    _chunk_data = [dict(r) for r in rows]
    tokenized = [chunk["content"].lower().split() for chunk in _chunk_data]
    _bm25_index = BM25Okapi(tokenized)

    print(f"BM25 index built over {len(_chunk_data)} chunks")

def bm25_search(query, top_k=20, filters=None):
    global _bm25_index, _chunk_data

    if _bm25_index is None:
        build_bm25_index()

    tokens = query.lower().split()
    scores = _bm25_index.get_scores(tokens)

    for i, chunk in enumerate(_chunk_data):
        if chunk["section_label"].lower().strip() in EXCLUDED_SECTIONS:
            scores[i] = 0
            continue

        if filters:
            if filters.get("tickers"):
                if chunk["ticker"] not in filters["tickers"]:
                    scores[i] = 0
                    continue
            if filters.get("fiscal_year"):
                if chunk["fiscal_year"] != filters["fiscal_year"]:
                    scores[i] = 0
                    continue

    top_indices = scores.argsort()[-top_k:][::-1]

    results = []
    for i in top_indices:
        if scores[i] > 0:
            result = dict(_chunk_data[i])
            result["bm25_score"] = float(scores[i])
            results.append(result)

    return results