import json
from pathlib import Path
import pytest
from indexer.chunker import CHUNKS_DIR, process_all_raw_files

@pytest.fixture(scope="module", autouse=True)
def setup_chunks():
    # Ensure chunks are generated before testing
    process_all_raw_files()

def test_all_chunks_exist():
    out_path = CHUNKS_DIR / "all_chunks.json"
    assert out_path.exists(), f"Expected {out_path} to exist"

def test_chunk_count_and_structure():
    out_path = CHUNKS_DIR / "all_chunks.json"
    with open(out_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # 5 funds * 5 sections = 25 chunks
    assert len(chunks) == 25, f"Expected 25 chunks, got {len(chunks)}"

    expected_sections = {
        "scheme_overview",
        "key_financial_indicators",
        "historical_returns",
        "portfolio_allocation",
        "scheme_rules"
    }

    found_sections = set()
    funds_seen = set()

    for chunk in chunks:
        assert "chunk_id" in chunk
        assert "section" in chunk
        assert "content" in chunk
        assert "metadata" in chunk
        
        found_sections.add(chunk["section"])
        funds_seen.add(chunk["metadata"]["scheme_slug"])

        # Check metadata consistency
        assert chunk["metadata"]["section"] == chunk["section"]
        assert "fund_house" in chunk["metadata"]
        assert chunk["metadata"]["fund_house"] == "HDFC Mutual Fund"

    assert len(funds_seen) == 5, f"Expected 5 distinct funds, got {len(funds_seen)}"
    assert found_sections == expected_sections, f"Missing sections. Found: {found_sections}"

def test_specific_metadata():
    out_path = CHUNKS_DIR / "all_chunks.json"
    with open(out_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Find the KFI chunk for Mid Cap
    mid_cap_kfi = next((c for c in chunks if c["metadata"]["scheme_slug"] == "hdfc-mid-cap-fund-direct-growth" and c["section"] == "key_financial_indicators"), None)
    
    assert mid_cap_kfi is not None, "Could not find KFI chunk for HDFC Mid Cap"
    assert "nav" in mid_cap_kfi["metadata"]
    assert "aum_cr" in mid_cap_kfi["metadata"]
    assert "expense_ratio_pct" in mid_cap_kfi["metadata"]
