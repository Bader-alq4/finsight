# FastAPI application entry point for the FinSight backend.
# Configures CORS for the React frontend, registers API routes,
# and preloads the BM25 index and cross-encoder reranker at startup
# so the first user query is fast.

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes.query import router as query_router
from backend.api.routes.companies import router as companies_router
from backend.core.retrieval.bm25_search import build_bm25_index
from backend.core.retrieval.reranker import get_reranker

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading BM25 index...")
    build_bm25_index()
    print("Loading reranker model...")
    get_reranker()
    print("FinSight API ready.")
    yield

app = FastAPI(
    title="FinSight API",
    description="Financial document intelligence platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router, prefix="/api")
app.include_router(companies_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)