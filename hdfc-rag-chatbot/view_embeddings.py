import chromadb
from pathlib import Path

CHROMA_DB_PATH = Path(__file__).parent / "data" / "chroma"
COLLECTION_NAME = "hdfc_mf_corpus"

def view_embeddings():
    if not CHROMA_DB_PATH.exists():
        print(f"Chroma DB not found at {CHROMA_DB_PATH}. Run indexer first.")
        return
        
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Failed to get collection: {e}")
        return
        
    count = collection.count()
    print(f"Total chunks in Vector Store: {count}\n")
    
    # Fetch 2 chunks with their embeddings
    results = collection.get(
        include=["embeddings", "documents", "metadatas"],
        limit=5
    )
    
    if not results or not results['ids']:
        print("No chunks found in collection.")
        return
        
    for i in range(len(results['ids'])):
        chunk_id = results['ids'][i]
        doc = results['documents'][i]
        metadata = results['metadatas'][i]
        embedding = results['embeddings'][i]
        
        print("="*60)
        print(f"Chunk ID : {chunk_id}")
        print(f"Scheme   : {metadata.get('scheme_name')}")
        print(f"Section  : {metadata.get('section')}")
        print("-"*60)
        print("Content:")
        print(doc.encode('ascii', 'ignore').decode('ascii'))
        print("-"*60)
        print(f"Embedding Vector (showing first 10 dimensions out of {len(embedding)}):")
        # Print first 10 dimensions nicely formatted
        formatted_emb = [f"{val:.4f}" for val in embedding[:10]]
        print(f"[{', '.join(formatted_emb)}, ...]")
        print("="*60)
        print("\n")

if __name__ == "__main__":
    view_embeddings()
