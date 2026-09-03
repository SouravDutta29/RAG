import pytest
from retriever.reranker import Reranker
from retriever.router import QueryIntent

@pytest.fixture(scope="module")
def reranker():
    # Will load BGE reranker base, and ChromaDB, BM25, and BGE embedder
    return Reranker()

def test_direct_lookup_intent(reranker):
    query = "What is the NAV of HDFC Small Cap Fund?"
    results = reranker.retrieve_and_rerank(query, top_k_retrieve=10, top_k_final=5)
    
    assert len(results) > 0, "No results returned"
    top_chunk = results[0]
    
    # Intent should be DIRECT_LOOKUP because it contains NAV
    assert top_chunk["intent_classified"] == QueryIntent.DIRECT_LOOKUP.name
    
    # Should fetch the kfi (key financial indicators) section for HDFC Small Cap
    assert top_chunk["metadata"]["scheme_slug"] == "hdfc-small-cap-fund-direct-growth"
    assert top_chunk["metadata"]["section"] == "key_financial_indicators"

def test_comparative_intent(reranker):
    query = "Compare AUM of HDFC Mid Cap vs Multi Cap"
    results = reranker.retrieve_and_rerank(query, top_k_retrieve=10, top_k_final=5)
    
    assert len(results) > 0, "No results returned"
    
    # Intent should be COMPARATIVE because it contains "compare" and "vs"
    assert results[0]["intent_classified"] == QueryIntent.COMPARATIVE.name
    
    # Should retrieve KFI for at least one of them in top results
    slugs_in_top_5 = [c["metadata"]["scheme_slug"] for c in results]
    assert "hdfc-mid-cap-fund-direct-growth" in slugs_in_top_5 or "hdfc-multi-cap-fund-direct-growth" in slugs_in_top_5

def test_portfolio_holding_intent(reranker):
    query = "Does HDFC Large Cap Fund hold HDFC Bank?"
    results = reranker.retrieve_and_rerank(query, top_k_retrieve=10, top_k_final=5)
    
    assert len(results) > 0, "No results returned"
    
    # Intent should be PORTFOLIO_HOLDING because it contains "hold"
    assert results[0]["intent_classified"] == QueryIntent.PORTFOLIO_HOLDING.name
    
    top_chunk = results[0]
    # Should fetch portfolio_allocation section for HDFC Large Cap
    assert top_chunk["metadata"]["scheme_slug"] == "hdfc-large-cap-fund-direct-growth" # large cap fund slug
    assert top_chunk["metadata"]["section"] == "portfolio_allocation"

def test_guidance_intent(reranker):
    query = "Explain the exit load of HDFC Gold FoF"
    results = reranker.retrieve_and_rerank(query, top_k_retrieve=10, top_k_final=5)
    
    assert len(results) > 0, "No results returned"
    
    # Exit load might not trigger specific intent unless explicitly coded, so GUIDANCE is expected
    # Note: "exit load" doesn't hit the direct_lookup regex unless we put "load" in there. 
    # Current regex: (nav|aum|expense ratio|sip|minimum sip|rating|returns|return|%)
    # Let's see what it classifies as.
    assert results[0]["intent_classified"] == QueryIntent.GUIDANCE.name
    
    top_chunk = results[0]
    # Should fetch scheme_rules section for HDFC Gold ETF
    assert top_chunk["metadata"]["scheme_slug"] == "hdfc-gold-etf-fund-of-fund-direct-plan-growth"
    assert top_chunk["metadata"]["section"] == "scheme_rules"
