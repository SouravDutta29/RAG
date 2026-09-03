import chromadb
import pickle
import json
from typing import List, Dict, Any
from pathlib import Path
from indexer.vector_store import CHROMA_DB_PATH, COLLECTION_NAME
from indexer.bm25_index import BM25_DIR, tokenize
from indexer.embedder import BGEEmbedder
from retriever.router import QueryRouter

class HybridSearcher:
    def __init__(self):
        # Initialize router
        self.router = QueryRouter()
        
        # Initialize Dense Store (ChromaDB)
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
        self.embedder = BGEEmbedder()
        
        # Initialize Sparse Store (BM25)
        bm25_index_path = BM25_DIR / "bm25_index.pkl"
        chunks_meta_path = BM25_DIR / "bm25_chunks.json"
        
        with open(bm25_index_path, "rb") as f:
            self.bm25 = pickle.load(f)
            
        with open(chunks_meta_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
            
        # Create a fast lookup for chunk data by chunk_id
        self.chunk_lookup = {c["chunk_id"]: c for c in self.chunks}

    def _rrf_score(self, rank_dense: int, rank_sparse: int, weight_dense: float, weight_sparse: float, k: int = 60) -> float:
        dense_score = (weight_dense / (k + rank_dense)) if rank_dense > 0 else 0
        sparse_score = (weight_sparse / (k + rank_sparse)) if rank_sparse > 0 else 0
        return dense_score + sparse_score

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        # 1. Route Query & Get Weights
        intent = self.router.classify_intent(query)
        weight_dense, weight_sparse = self.router.get_weights(intent)
        
        # 2. Dense Search (ChromaDB)
        query_embedding = self.embedder.embed_text(query)
        dense_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        dense_rankings = {}
        # Chroma returns [[id1, id2, ...]]
        if dense_results and dense_results["ids"]:
            for i, chunk_id in enumerate(dense_results["ids"][0]):
                # rank is 1-indexed
                dense_rankings[chunk_id] = i + 1
                
        # 3. Sparse Search (BM25)
        tokenized_query = tokenize(query)
        # get_top_n returns the actual chunk dicts
        sparse_results = self.bm25.get_top_n(tokenized_query, self.chunks, n=top_k)
        
        sparse_rankings = {}
        for i, chunk in enumerate(sparse_results):
            chunk_id = chunk["chunk_id"]
            sparse_rankings[chunk_id] = i + 1
            
        # 4. Apply Intent-Weighted RRF Fusion
        all_chunk_ids = set(dense_rankings.keys()).union(set(sparse_rankings.keys()))
        rrf_scores = []
        
        for chunk_id in all_chunk_ids:
            r_dense = dense_rankings.get(chunk_id, 0)
            r_sparse = sparse_rankings.get(chunk_id, 0)
            score = self._rrf_score(r_dense, r_sparse, weight_dense, weight_sparse)
            rrf_scores.append((chunk_id, score))
            
        # Sort by RRF score descending
        rrf_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 5. Return Top-K Candidates
        final_candidates = []
        for chunk_id, score in rrf_scores[:top_k]:
            chunk_data = self.chunk_lookup[chunk_id]
            final_candidates.append({
                "chunk_id": chunk_id,
                "content": chunk_data["content"],
                "metadata": chunk_data["metadata"],
                "rrf_score": score,
                "intent_classified": intent.name
            })
            
        return final_candidates
