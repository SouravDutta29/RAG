import json
from pathlib import Path
import pytest
import sys

# Ensure scraper module is in path so we can import models
sys.path.insert(0, str(Path(__file__).parent.parent / "scraper"))
from models import FundScheme

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

EXPECTED_FUNDS = [
    "hdfc_mid_cap_fund_direct_growth.json",
    "hdfc_small_cap_fund_direct_growth.json",
    "hdfc_gold_etf_fund_of_fund_direct_plan_growth.json",
    "hdfc_multi_cap_fund_direct_growth.json",
    "hdfc_large_cap_fund_direct_growth.json"
]

def test_parsed_files_exist():
    """Assert all 5 expected parsed JSON files exist in the data/raw directory."""
    for fund_file in EXPECTED_FUNDS:
        file_path = RAW_DATA_DIR / fund_file
        assert file_path.exists(), f"Missing parsed file: {fund_file}"
        assert file_path.stat().st_size > 0, f"File {fund_file} is empty"

def test_data_validation_and_critical_fields():
    """Load each parsed JSON, validate against Pydantic schema, and assert critical fields."""
    for fund_file in EXPECTED_FUNDS:
        file_path = RAW_DATA_DIR / fund_file
        
        with open(file_path, "r", encoding="utf-8") as f:
            raw_json_str = f.read()
            
        # 1. Pydantic Type Validation
        # model_validate_json will raise ValidationError if schema doesn't match
        try:
            scheme = FundScheme.model_validate_json(raw_json_str)
        except Exception as e:
            pytest.fail(f"Validation failed for {fund_file}: {e}")
            
        # 2. Critical Field Validations (Non-null and > 0 for core financials)
        assert scheme.nav > 0, f"NAV should be > 0 for {scheme.scheme_name}, got {scheme.nav}"
        assert scheme.aum_cr > 0, f"AUM should be > 0 for {scheme.scheme_name}, got {scheme.aum_cr}"
        
        # Expense ratio might be 0 for some ETF funds, but usually > 0
        assert scheme.expense_ratio_pct >= 0, f"Expense Ratio invalid for {scheme.scheme_name}"
        
        assert scheme.nav_date, f"NAV Date missing for {scheme.scheme_name}"
        assert scheme.category, f"Category missing for {scheme.scheme_name}"
        
        # Check holdings if it's an equity fund (Gold ETF FoF might have fewer holdings)
        if "gold" not in scheme.scheme_slug.lower():
            assert len(scheme.top_holdings) > 0, f"No top holdings found for {scheme.scheme_name}"
            assert len(scheme.sector_allocation) > 0, f"No sector allocation found for {scheme.scheme_name}"
