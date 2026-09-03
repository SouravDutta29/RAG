import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
CHUNKS_DIR = Path(__file__).parent.parent / "data" / "chunks"

def ensure_chunks_dir():
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

def generate_chunks_for_fund(scheme: Dict[str, Any]) -> List[Dict[str, Any]]:
    slug = scheme.get("scheme_slug", "unknown")
    fund_name = scheme.get("scheme_name", "Unknown Fund")
    fund_house = "HDFC Mutual Fund"
    category = scheme.get("category", "Unknown Category")
    
    base_metadata = {
        "scheme_slug": slug,
        "scheme_name": fund_name,
        "fund_house": fund_house,
        "category": category,
        "source_url": f"https://groww.in/mutual-funds/{slug}",
        "scraped_at": datetime.utcnow().isoformat() + "Z"
    }

    chunks = []

    # 1. Scheme Overview
    overview_text = (
        f"Fund Name: {fund_name}\n"
        f"Fund House: {fund_house}\n"
        f"Category: {category}\n"
        f"Risk Label: {scheme.get('risk_label', 'Unknown')}\n"
        f"Rating: {scheme.get('rating_stars', 'N/A')} Stars"
    )
    chunks.append({
        "chunk_id": f"{slug}_overview",
        "section": "scheme_overview",
        "content": overview_text,
        "metadata": {
            **base_metadata,
            "section": "scheme_overview",
            "rating": scheme.get("rating_stars"),
            "risk": scheme.get("risk_label")
        }
    })

    # 2. Key Financial Indicators
    kfi_text = (
        f"{fund_name} Key Financial Indicators:\n"
        f"NAV: ₹{scheme.get('nav', 0.0)} (as of {scheme.get('nav_date', '')})\n"
        f"AUM: ₹{scheme.get('aum_cr', 0.0)} Cr\n"
        f"Expense Ratio: {scheme.get('expense_ratio_pct', 0.0)}%\n"
        f"Minimum SIP: ₹{scheme.get('min_sip', 0.0)}"
    )
    chunks.append({
        "chunk_id": f"{slug}_kfi",
        "section": "key_financial_indicators",
        "content": kfi_text,
        "metadata": {
            **base_metadata,
            "section": "key_financial_indicators",
            "nav": scheme.get("nav"),
            "aum_cr": scheme.get("aum_cr"),
            "expense_ratio_pct": scheme.get("expense_ratio_pct"),
            "min_sip": scheme.get("min_sip")
        }
    })

    # 3. Historical Returns
    returns_text = (
        f"{fund_name} Historical Returns:\n"
        f"1-Day Return: {scheme.get('return_1d_pct')}%\n"
        f"1-Year Return: {scheme.get('return_1y_pct')}%\n"
        f"3-Year Return: {scheme.get('return_3y_pct')}%\n"
        f"5-Year Return: {scheme.get('return_5y_pct')}%"
    )
    chunks.append({
        "chunk_id": f"{slug}_returns",
        "section": "historical_returns",
        "content": returns_text,
        "metadata": {
            **base_metadata,
            "section": "historical_returns"
        }
    })

    # 4. Portfolio Allocation
    holdings_str = ", ".join([f"{h['stock']} ({h['weight_pct']}%)" for h in scheme.get("top_holdings", [])])
    sectors_str = ", ".join([f"{s['sector']} ({s['weight_pct']}%)" for s in scheme.get("sector_allocation", [])])
    
    portfolio_text = (
        f"{fund_name} Portfolio Allocation:\n"
        f"Top Holdings: {holdings_str}\n"
        f"Sector Allocation: {sectors_str}"
    )
    chunks.append({
        "chunk_id": f"{slug}_portfolio",
        "section": "portfolio_allocation",
        "content": portfolio_text,
        "metadata": {
            **base_metadata,
            "section": "portfolio_allocation"
        }
    })

    # 5. Scheme Rules
    rules_text = (
        f"{fund_name} Scheme Rules:\n"
        f"Exit Load: {scheme.get('exit_load_rule', 'N/A')}\n"
        f"Benchmark Index: {scheme.get('benchmark_index', 'N/A')}\n"
        f"Fund Manager: {scheme.get('fund_manager', 'N/A')}"
    )
    chunks.append({
        "chunk_id": f"{slug}_rules",
        "section": "scheme_rules",
        "content": rules_text,
        "metadata": {
            **base_metadata,
            "section": "scheme_rules"
        }
    })

    return chunks

def process_all_raw_files():
    ensure_chunks_dir()
    raw_files = list(RAW_DIR.glob("*.json"))
    
    # Filter out files ending with _raw.json to only process the normalized files
    normalized_files = [f for f in raw_files if not f.name.endswith("_raw.json")]
    
    if not normalized_files:
        logging.warning(f"No normalized JSON files found in {RAW_DIR}")
        return

    all_chunks = []
    
    for raw_file in normalized_files:
        try:
            with open(raw_file, "r", encoding="utf-8") as f:
                scheme = json.load(f)
            
            chunks = generate_chunks_for_fund(scheme)
            all_chunks.extend(chunks)
            logging.info(f"Generated {len(chunks)} chunks for {scheme.get('scheme_slug', 'unknown')}")
        except Exception as e:
            logging.error(f"Failed to chunk {raw_file.name}: {e}")

    out_path = CHUNKS_DIR / "all_chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)
    
    logging.info(f"Successfully saved {len(all_chunks)} chunks to {out_path}")

if __name__ == "__main__":
    process_all_raw_files()
