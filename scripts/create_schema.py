import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import DATABASE_URL

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

schema = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    cik VARCHAR(20) UNIQUE NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    document_type VARCHAR(50),
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    filing_date DATE,
    source_url TEXT,
    file_path TEXT,
    status VARCHAR(50) DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    company_id INTEGER REFERENCES companies(id),
    content TEXT NOT NULL,
    embedding vector(1536),
    section_label VARCHAR(255),
    chunk_index INTEGER,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS chunks_company_idx
ON chunks (company_id);

CREATE INDEX IF NOT EXISTS chunks_section_idx
ON chunks (section_label);

CREATE TABLE IF NOT EXISTS eval_questions (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    expected_answer TEXT,
    relevant_chunk_ids INTEGER[],
    query_type VARCHAR(50),
    difficulty VARCHAR(20),
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eval_results (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES eval_questions(id),
    retrieval_strategy VARCHAR(50),
    retrieved_chunk_ids INTEGER[],
    generated_answer TEXT,
    precision_at_5 FLOAT,
    recall_at_5 FLOAT,
    mrr FLOAT,
    faithfulness_score FLOAT,
    answer_relevance_score FLOAT,
    latency_ms INTEGER,
    run_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS queries (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT,
    retrieved_chunk_ids INTEGER[],
    retrieval_strategy VARCHAR(50),
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

print("Creating schema...")
cursor.execute(schema)
conn.commit()
print("Done.")

cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
tables = cursor.fetchall()
print(f"\nTables created:")
for table in tables:
    print(f"  {table[0]}")

cursor.close()
conn.close()