from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from retriever.hybrid_search import HybridSearcher

RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"

class Reranker:
    def __init__(self):
        self.hybrid_searcher = HybridSearcher()
        self.cross_encoder = CrossEncoder(RERANKER_MODEL_NAME)

    def retrieve_and_rerank(self, query: str, top_k_retrieve: int = 10, top_k_final: int = 5) -> List[Dict[str, Any]]:
        # 1. Retrieve candidates
        candidates = self.hybrid_searcher.search(query, top_k=top_k_retrieve)
        
        if not candidates:
            return []
            
        # 2. Prepare pairs for cross-encoder
        # CrossEncoder expects a list of [query, document] pairs
        pairs = [[query, candidate["content"]] for candidate in candidates]
        
        # 3. Score
        scores = self.cross_encoder.predict(pairs)
        
        # 4. Attach scores and sort
        for i, candidate in enumerate(candidates):
            candidate["rerank_score"] = float(scores[i])
            
        # Sort descending by rerank score
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # 5. Return top final
        return candidates[:top_k_final]
