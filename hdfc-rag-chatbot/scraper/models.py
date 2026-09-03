from typing import List, Optional
from pydantic import BaseModel, Field

class Holding(BaseModel):
    stock: str
    weight_pct: float

class SectorAllocation(BaseModel):
    sector: str
    weight_pct: float

class FundScheme(BaseModel):
    scheme_slug: str
    scheme_name: str
    category: str
    nav: float
    nav_date: str
    aum_cr: float
    expense_ratio_pct: float
    min_sip: float
    rating_stars: Optional[int] = None
    risk_label: str
    return_1d_pct: Optional[float] = None
    return_1y_pct: Optional[float] = None
    return_3y_pct: Optional[float] = None
    return_5y_pct: Optional[float] = None
    top_holdings: List[Holding]
    sector_allocation: List[SectorAllocation]
    exit_load_rule: str
    benchmark_index: str
    fund_manager: str
