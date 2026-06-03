# Core query endpoint for FinSight: POST /api/query
# Accepts a question and optional company/year filters
# Runs the full retrieval pipeline (vector + BM25 + rerank) then streams
# the GPT-4o-mini response back via Server-Sent Events in three phases:
# sources (retrieved chunks) -> tokens (answer words) -> done (latency).

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from backend.core.retrieval.pipeline import retrieve
from backend.core.generation.generator import generate_answer_stream
import json
import time

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    tickers: Optional[List[str]] = None
    fiscal_year: Optional[int] = None

@router.post("/query")
async def query(request: QueryRequest):
    start = time.time()

    filters = {}
    if request.tickers:
        filters["tickers"] = request.tickers
    if request.fiscal_year:
        filters["fiscal_year"] = request.fiscal_year

    result = retrieve(request.question, filters=filters if filters else None)
    chunks = result["chunks"]

    async def stream():
        yield f"data: {json.dumps({'type': 'sources', 'sources': chunks})}\n\n"

        async for token in generate_answer_stream(request.question, chunks):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        latency = int((time.time() - start) * 1000)
        yield f"data: {json.dumps({'type': 'done', 'latency_ms': latency})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

@router.get("/health")
async def health():
    return {"status": "ok"}