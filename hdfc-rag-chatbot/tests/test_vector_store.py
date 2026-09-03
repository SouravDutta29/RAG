import pytest
import chromadb
from indexer.vector_store import CHROMA_DB_PATH, COLLECTION_NAME, build_vector_store
from indexer.embedder import BGEEmbedder

@pytest.fixture(scope="module", autouse=True)
def setup_vector_store():
    # Build vector store before running tests
    build_vector_store()

def test_vector_store_query():
    assert CHROMA_DB_PATH.exists(), f"Chroma DB path {CHROMA_DB_PATH} does not exist"
    
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)
    
    # Check count
    count = collection.count()
    assert count == 25, f"Expected 25 documents, found {count}"
    
    embedder = BGEEmbedder()
    query = "HDFC Mid Cap expense ratio"
    query_embedding = embedder.embed_text(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )
    
    # At least 1 relevant chunk should be in Top-5
    metadatas = results["metadatas"][0]
    slugs = [m.get("scheme_slug") for m in metadatas]
    
    assert "hdfc-mid-cap-fund-direct-growth" in slugs, "Mid Cap fund not found in Top-5 for query"
