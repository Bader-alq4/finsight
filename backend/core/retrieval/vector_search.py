# Find chunks that are semantically similar to the question. 
# Embeds the query, runs pgvector cosine similarity search across all chunks, 
# joins with documents and companies tables so every result carries company name, ticker, fiscal year, and section label.

import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import DATABASE_URL, OPENAI_API_KEY
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def embed_query(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def vector_search(query, top_k=20, filters=None):
    query_embedding = embed_query(query)

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    extra_where = ""
    extra_params = []

    if filters:
        if filters.get("tickers"):
            extra_where += " AND co.ticker = ANY(%s)"
            extra_params.append(filters["tickers"])
        if filters.get("fiscal_year"):
            extra_where += " AND d.fiscal_year = %s"
            extra_params.append(filters["fiscal_year"])

    sql = f"""
        SELECT
            c.id,
            c.content,
            c.section_label,
            c.chunk_index,
            c.token_count,
            co.name as company_name,
            co.ticker,
            d.fiscal_year,
            d.document_type,
            1 - (c.embedding <=> %s::vector) AS similarity
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        JOIN companies co ON c.company_id = co.id
        WHERE c.section_label NOT IN (
            'Front Matter',
            'Item 8. Financial Statements',
            'Item 10. Directors and Officers',
            'Item 11. Executive Compensation',
            'Item 14. Accountant Fees',
            'Item 15. Exhibits',
            'Item 16. Summary'
        )
        {extra_where}
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
    """

    params = [query_embedding] + extra_params + [query_embedding, top_k]

    cursor.execute(sql, params)

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in results]