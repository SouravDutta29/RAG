import json
import logging
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi
from indexer.chunker import CHUNKS_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BM25_DIR = Path(__file__).parent.parent / "data" / "bm25"

def ensure_bm25_dir():
    BM25_DIR.mkdir(parents=True, exist_ok=True)

def tokenize(text: str) -> list[str]:
    # Using simple split tokenizer for robustness, could use nltk but simple split avoids downloading corpus
    import string
    text = text.lower()
    for p in string.punctuation:
        text = text.replace(p, " ")
    return text.split()

def build_bm25_index():
    chunks_path = CHUNKS_DIR / "all_chunks.json"
    if not chunks_path.exists():
        logging.error(f"Chunks file not found at {chunks_path}. Run chunker.py first.")
        return
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    if not chunks:
        logging.warning("No chunks found in all_chunks.json")
        return
        
    ensure_bm25_dir()
    
    logging.info(f"Tokenizing and building BM25 index for {len(chunks)} chunks...")
    tokenized_corpus = [tokenize(c["content"]) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    
    index_path = BM25_DIR / "bm25_index.pkl"
    with open(index_path, "wb") as f:
        pickle.dump(bm25, f)
        
    chunks_meta_path = BM25_DIR / "bm25_chunks.json"
    with open(chunks_meta_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
        
    logging.info(f"Successfully saved BM25 index to {index_path}")

if __name__ == "__main__":
    build_bm25_index()
