import json
import logging
from pathlib import Path
from collections import defaultdict
from models import FundScheme, Holding, SectorAllocation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

def parse_and_normalize(raw_file: Path) -> FundScheme:
    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    slug = data["source_url"].split('/')[-1]
    
    # All our needed data is conveniently in the Next.js props
    server_data = data["next_data"]["props"]["pageProps"]["mfServerSideData"]
    
    # Return stats is a list, typically the first element has the core stats
    stats = server_data.get("return_stats", [{}])[0]
    
    # Process Holdings
    raw_holdings = server_data.get("holdings", [])
    holdings = []
    sector_weights = defaultdict(float)
    
    for h in raw_holdings:
        # Extract individual holdings
        company = h.get("company_name", "Unknown")
        weight = h.get("corpus_per", 0.0)
        
        # Only add meaningful holdings to top_holdings list
        if company and weight is not None:
            holdings.append(Holding(stock=company, weight_pct=weight))
            
        # Aggregate sectors
        sector = h.get("sector_name", "Unspecified")
        if sector and weight is not None:
            sector_weights[sector] += weight

    # Sort holdings by weight
    holdings.sort(key=lambda x: x.weight_pct, reverse=True)
    # Take top 20 holdings to keep chunk size reasonable
    top_holdings = holdings[:20]
    
    # Format sector allocation
    sector_allocation = [
        SectorAllocation(sector=k, weight_pct=round(v, 2)) 
        for k, v in sector_weights.items()
    ]
    sector_allocation.sort(key=lambda x: x.weight_pct, reverse=True)

    # Build the normalized schema
    scheme = FundScheme(
        scheme_slug=slug,
        scheme_name=server_data.get("scheme_name", slug),
        category=server_data.get("category", "Unknown"),
        nav=server_data.get("nav", 0.0),
        nav_date=server_data.get("nav_date", ""),
        aum_cr=server_data.get("aum", 0.0),
        expense_ratio_pct=server_data.get("expense_ratio", 0.0),
        min_sip=server_data.get("min_sip_investment", 0.0),
        rating_stars=server_data.get("groww_rating"),
        risk_label=stats.get("risk", "Unknown"),
        return_1d_pct=stats.get("return1d"),
        return_1y_pct=stats.get("return1y"),
        return_3y_pct=stats.get("return3y"),
        return_5y_pct=stats.get("return5y"),
        top_holdings=top_holdings,
        sector_allocation=sector_allocation,
        exit_load_rule=server_data.get("exit_load", "N/A"),
        benchmark_index=server_data.get("benchmark_name", "N/A"),
        fund_manager=server_data.get("fund_manager", "N/A")
    )
    
    return scheme

def process_all_raw_files():
    raw_files = list(RAW_DIR.glob("*_raw.json"))
    if not raw_files:
        logging.warning(f"No *_raw.json files found in {RAW_DIR}")
        return
        
    for raw_file in raw_files:
        try:
            scheme = parse_and_normalize(raw_file)
            
            # Save the normalized JSON
            # e.g., hdfc-mid-cap-fund-direct-growth_raw.json -> hdfc_mid_cap_fund_direct_growth.json
            slug = scheme.scheme_slug.replace("-", "_")
            out_path = RAW_DIR / f"{slug}.json"
            
            with open(out_path, "w", encoding="utf-8") as f:
                # Use model_dump_json for Pydantic v2
                f.write(scheme.model_dump_json(indent=2))
                
            logging.info(f"Successfully normalized and saved {scheme.scheme_slug} to {out_path.name}")
        except Exception as e:
            logging.error(f"Failed to parse {raw_file.name}: {e}")

if __name__ == "__main__":
    process_all_raw_files()
