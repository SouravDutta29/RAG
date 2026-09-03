import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add root directory to sys.path so 'python api/main.py' works directly
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from indexer import chunker
from indexer import vector_store
from indexer import bm25_index
from retriever.reranker import Reranker
from generator.guardrail import PromptGuard
from generator.prompt_builder import PromptBuilder
from generator.llm_engine import LLMEngine
from generator.verifier import FactVerifier
from generator.citation_injector import CitationInjector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HDFC RAG API", version="1.0.0")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons lazily or on startup to save memory
class RAGState:
    reranker: Optional[Reranker] = None
    guard: Optional[PromptGuard] = None
    prompt_builder: Optional[PromptBuilder] = None
    llm: Optional[LLMEngine] = None
    verifier: Optional[FactVerifier] = None
    citation: Optional[CitationInjector] = None

state = RAGState()

@app.on_event("startup")
async def startup_event():
    # Only load models on startup if the chunks exist.
    # If not ingested yet, we'll load them lazily after ingest.
    chunks_path = chunker.CHUNKS_DIR / "all_chunks.json"
    if chunks_path.exists():
        _init_rag_components()

def _init_rag_components():
    logger.info("Initializing RAG components...")
    if not state.reranker: state.reranker = Reranker()
    if not state.guard: state.guard = PromptGuard()
    if not state.prompt_builder: state.prompt_builder = PromptBuilder()
    if not state.llm: state.llm = LLMEngine()
    if not state.verifier: state.verifier = FactVerifier()
    if not state.citation: state.citation = CitationInjector()

# --- Models ---
class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

class CompareRequest(BaseModel):
    slug_1: str
    slug_2: str

class HealthResponse(BaseModel):
    status: str
    chroma_chunks: int
    api_key_set: bool

class FundItem(BaseModel):
    scheme_name: str
    category: str
    nav: str
    aum_cr: str
    source_url: str

class FundsResponse(BaseModel):
    funds: List[FundItem]

class IngestResponse(BaseModel):
    status: str
    message: str

# --- Endpoints ---

@app.get("/api/v1/health", response_model=HealthResponse)
def health_check():
    # Check chroma count
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(vector_store.CHROMA_DB_PATH))
        col = client.get_collection(vector_store.COLLECTION_NAME)
        chroma_count = col.count()
    except Exception:
        chroma_count = 0
        
    return {
        "status": "ok",
        "chroma_chunks": chroma_count,
        "api_key_set": bool(os.environ.get("GROQ_API_KEY"))
    }

@app.get("/api/v1/funds", response_model=FundsResponse)
def get_funds():
    chunks_path = chunker.CHUNKS_DIR / "all_chunks.json"
    if not chunks_path.exists():
        return {"funds": []}
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    funds = {}
    for c in chunks:
        meta = c["metadata"]
        slug = meta["scheme_slug"]
        if slug not in funds:
            funds[slug] = {
                "scheme_name": meta["scheme_name"],
                "category": meta["category"],
                "nav": meta.get("nav", "N/A"),
                "aum_cr": meta.get("aum_cr", "N/A"),
                "source_url": meta["source_url"]
            }
            
    return {"funds": list(funds.values())}

@app.post("/api/v1/ingest", response_model=IngestResponse)
def ingest_data():
    try:
        logger.info("Running chunker...")
        chunker.main()
        logger.info("Building ChromaDB...")
        vector_store.build_vector_store()
        logger.info("Building BM25...")
        bm25_index.build_bm25_index()
        
        # Re-initialize components with new data
        _init_rag_components()
        return {"status": "success", "message": "Data ingested and indexed successfully"}
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat")
async def chat_endpoint(req: ChatRequest):
    _init_rag_components()
    
    # 1. Guardrail Check
    if not state.guard.check_safety(req.query):
        async def unsafe_stream():
            yield "I cannot fulfill this request as it violates safety guidelines."
        return StreamingResponse(unsafe_stream(), media_type="text/event-stream")
        
    # 2. Retrieve & Rerank
    top_chunks = state.reranker.retrieve_and_rerank(req.query)
    
    # 3. Build Prompt
    prompt = state.prompt_builder.build_prompt(req.query, top_chunks)
    
    # 4. Stream response
    async def response_generator():
        full_response = ""
        # The LLM engine yields chunks synchronously. We wrap it in a generator.
        # Since it's blocking, in a true high-concurrency app we'd use async Groq,
        # but for this PoC `yield` works.
        try:
            for token in state.llm.generate_response_stream(prompt):
                full_response += token
                yield token
                # Small sleep to yield to event loop if needed
                await asyncio.sleep(0.001)
                
            # 5. Output Verification
            verified_text = state.verifier.verify(full_response, top_chunks)
            if verified_text != full_response:
                yield "\n\n[Correction: Verified data not available in the knowledge base for this figure.]"
                full_response = verified_text
                
            # 6. Citations
            citations = state.citation.inject_citations("", top_chunks)
            yield citations
            
        except Exception as e:
            yield f"\n[Error: {str(e)}]"
            
    return StreamingResponse(response_generator(), media_type="text/event-stream")

@app.post("/api/v1/compare")
async def compare_funds(req: CompareRequest):
    query = f"Compare {req.slug_1} and {req.slug_2} side-by-side using a markdown table across all metrics."
    chat_req = ChatRequest(query=query, history=[])
    return await chat_endpoint(chat_req)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
