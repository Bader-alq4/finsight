# REST endpoints for browsing the FinSight corpus
# GET /companies — returns all indexed companies with filing counts and year ranges
# GET /documents — returns all indexed filings with company metadata
# Used by the React frontend to populate filter dropdowns


from fastapi import APIRouter
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import DATABASE_URL

router = APIRouter()

@router.get("/companies")
def get_companies():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            co.id,
            co.name,
            co.ticker,
            COUNT(DISTINCT d.id) as filing_count,
            MIN(d.fiscal_year) as earliest_year,
            MAX(d.fiscal_year) as latest_year
        FROM companies co
        JOIN documents d ON co.id = d.company_id
        GROUP BY co.id, co.name, co.ticker
        ORDER BY co.ticker
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in results]

@router.get("/documents")
def get_documents():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            d.id,
            d.document_type,
            d.fiscal_year,
            d.status,
            co.name as company_name,
            co.ticker
        FROM documents d
        JOIN companies co ON d.company_id = co.id
        ORDER BY co.ticker, d.fiscal_year DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in results]