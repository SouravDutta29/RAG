import json
import pickle
import pytest
from pathlib import Path
from indexer.bm25_index import BM25_DIR, build_bm25_index, tokenize

@pytest.fixture(scope="module", autouse=True)
def setup_bm25_index():
    # Build BM25 index before running tests
    build_bm25_index()

def test_bm25_query():
    index_path = BM25_DIR / "bm25_index.pkl"
    chunks_meta_path = BM25_DIR / "bm25_chunks.json"
    
    assert index_path.exists(), f"BM25 index path {index_path} does not exist"
    assert chunks_meta_path.exists(), f"BM25 chunks path {chunks_meta_path} does not exist"
    
    with open(index_path, "rb") as f:
        bm25 = pickle.load(f)
        
    with open(chunks_meta_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    assert len(chunks) == 25, f"Expected 25 documents, found {len(chunks)}"
    
    query = "HDFC Small Cap expense ratio"
    tokenized_query = tokenize(query)
    
    # Get top 1 result
    top_chunks = bm25.get_top_n(tokenized_query, chunks, n=1)
    
    assert len(top_chunks) > 0, "No results returned"
    
    top_chunk = top_chunks[0]
    slug = top_chunk["metadata"].get("scheme_slug")
    
    assert slug == "hdfc-small-cap-fund-direct-growth", f"Expected small cap chunk, got {slug}"
