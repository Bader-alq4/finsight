# Writes companies, documents, and chunks to your PostgreSQL database

import psycopg2
from backend.config import DATABASE_URL

# checks if the company already exists in the companies table, 
# if it exists, it returns the existing ID instead of creating a duplicate
def get_or_create_company(cursor, ticker, name, cik):
    cursor.execute(
        "SELECT id FROM companies WHERE ticker = %s", (ticker,)
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO companies (name, ticker, cik)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (name, ticker, cik))
    return cursor.fetchone()[0]

# inserts one row into the documents table for this filing (company ID, filing type, fiscal year, file path, status)
def create_document(cursor, company_id, doc_type, fiscal_year, file_path, source_url):
    cursor.execute("""
        INSERT INTO documents 
        (company_id, document_type, fiscal_year, file_path, source_url, status)
        VALUES (%s, %s, %s, %s, %s, 'complete')
        RETURNING id
    """, (company_id, doc_type, fiscal_year, file_path, source_url))
    return cursor.fetchone()[0]

# loops through all chunks and their embeddings together and inserts one row per chunk into the chunks table
# Every chunk gets linked to its document and company via foreign keys
def store_chunks(cursor, chunks, embeddings, document_id, company_id):
    for chunk, embedding in zip(chunks, embeddings):
        cursor.execute("""
            INSERT INTO chunks
            (document_id, company_id, content, embedding, 
             section_label, chunk_index, token_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            document_id,
            company_id,
            chunk["content"],
            embedding,
            chunk["section_label"],
            chunk["chunk_index"],
            chunk["token_count"]
        ))