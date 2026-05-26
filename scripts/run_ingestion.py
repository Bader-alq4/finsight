# Takes files from data/raw/, runs them through parse -> chunk -> embed -> store in sequence
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from backend.config import DATABASE_URL
from backend.core.ingestion.parser import parse_html
from backend.core.ingestion.chunker import chunk_sections
from backend.core.ingestion.embedder import embed_chunks
from backend.core.ingestion.storage import (
    get_or_create_company,
    create_document,
    store_chunks
)

COMPANIES = {
    "AAPL": {"name": "Apple Inc.", "cik": "0000320193"},
    "MSFT": {"name": "Microsoft Corporation", "cik": "0000789019"},
    "NVDA": {"name": "NVIDIA Corporation", "cik": "0001045810"},
    "GOOGL": {"name": "Alphabet Inc.", "cik": "0001652044"},
    "AMZN": {"name": "Amazon.com Inc.", "cik": "0001018724"},
    "META": {"name": "Meta Platforms Inc.", "cik": "0001326801"},
    "TSLA": {"name": "Tesla Inc.", "cik": "0001318605"},
    "JPM":  {"name": "JPMorgan Chase & Co.", "cik": "0000019617"},
    "BRK":  {"name": "Berkshire Hathaway Inc.", "cik": "0001067983"},
    "JNJ":  {"name": "Johnson & Johnson", "cik": "0000200406"},
}

def ingest_file(file_path, ticker, filing_type, fiscal_year):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        info = COMPANIES[ticker]

        print(f"\nIngesting {ticker} {filing_type} {fiscal_year}...")

        # Get or create company
        company_id = get_or_create_company(
            cursor, ticker, info["name"], info["cik"]
        )
        conn.commit()

        # Check if already ingested
        cursor.execute("""
            SELECT id FROM documents
            WHERE company_id = %s 
            AND document_type = %s 
            AND fiscal_year = %s
        """, (company_id, filing_type, fiscal_year))

        if cursor.fetchone():
            print(f"  Already ingested — skipping")
            return

        # Parse
        print(f"  Parsing {file_path}...")
        sections = parse_html(file_path)
        print(f"  Found {len(sections)} sections")

        # Chunk
        chunks = chunk_sections(sections)
        print(f"  Created {len(chunks)} chunks")

        # Embed
        embeddings = embed_chunks(chunks)
        print(f"  Embedded {len(embeddings)} chunks")

        # Store document
        document_id = create_document(
            cursor, company_id, filing_type,
            fiscal_year, file_path, None
        )

        # Store chunks
        store_chunks(cursor, chunks, embeddings, document_id, company_id)
        conn.commit()

        print(f"  Done — {len(chunks)} chunks stored")

    except Exception as e:
        conn.rollback()
        print(f"  Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    raw_dir = "data/raw"
    files = os.listdir(raw_dir)

    for filename in sorted(files):
        if not (filename.endswith(".htm") or
                filename.endswith(".html") or
                filename.endswith(".xml")):
            continue

        parts = filename.replace(".htm", "").replace(".html", "").replace(".xml", "").split("_")
        if len(parts) < 3:
            continue

        ticker = parts[0]
        filing_type = parts[1]
        fiscal_year = int(parts[2])

        if ticker not in COMPANIES:
            print(f"Unknown ticker {ticker} — skipping {filename}")
            continue

        file_path = os.path.join(raw_dir, filename)
        ingest_file(file_path, ticker, filing_type, fiscal_year)

if __name__ == "__main__":
    main()