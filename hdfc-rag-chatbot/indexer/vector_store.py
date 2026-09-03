import json
import logging
from pathlib import Path
import chromadb
from indexer.chunker import CHUNKS_DIR
from indexer.embedder import BGEEmbedder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHROMA_DB_PATH = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "hdfc_mf_corpus"

def build_vector_store():
    # 1. Load chunks
    chunks_path = CHUNKS_DIR / "all_chunks.json"
    if not chunks_path.exists():
        logging.error(f"Chunks file not found at {chunks_path}. Run chunker.py first.")
        return
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    if not chunks:
        logging.warning("No chunks found in all_chunks.json")
        return
        
    # 2. Generate Embeddings
    logging.info(f"Generating embeddings for {len(chunks)} chunks using BGE-small...")
    embedder = BGEEmbedder()
    texts = [c["content"] for c in chunks]
    embeddings = embedder.embed_batch(texts)
    
    # 3. Initialize ChromaDB
    logging.info(f"Initializing ChromaDB at {CHROMA_DB_PATH}")
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    
    # Recreate collection to ensure a fresh index
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass # Doesn't exist yet
        
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # 4. Upsert
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    
    # Chroma metadata doesn't support nested dicts well, sanitize
    sanitized_metadatas = []
    for meta in metadatas:
        sanitized = {}
        for k, v in meta.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            else:
                sanitized[k] = str(v)
        sanitized_metadatas.append(sanitized)
    
    logging.info(f"Upserting into ChromaDB collection '{COLLECTION_NAME}'...")
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=sanitized_metadatas,
        documents=texts
    )
    logging.info("Vector store build complete.")

if __name__ == "__main__":
    build_vector_store()
